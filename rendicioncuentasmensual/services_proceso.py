"""Servicios para el flujo de rendiciones y su consulta por organización."""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from comedores.models import Comedor
from organizaciones.models import ProyectoOrganizacion
from rendicioncuentasmensual.models import DocumentacionAdjunta, RendicionCuentaMensual
from rendicioncuentasmensual.services import RendicionCuentaMensualService


class RendicionesOrganizacionService:
    """Consultas de rendiciones mostradas dentro del legajo de Organización."""

    @staticmethod
    def obtener_rendiciones(organizacion, codigo_proyecto=None):
        queryset = (
            RendicionCuentaMensual.objects.filter(
                deleted_at__isnull=True,
                comedor__deleted_at__isnull=True,
                comedor__organizacion=organizacion,
            )
            .select_related("comedor", "comedor__organizacion")
            .order_by("-periodo_inicio", "-id")
        )
        codigo = (codigo_proyecto or "").strip()
        if codigo:
            queryset = queryset.filter(
                Q(comedor__proyecto__codigo=codigo)
                | Q(comedor__codigo_de_proyecto=codigo)
            )
        return queryset

    @staticmethod
    def obtener_proyectos(organizacion):
        """Códigos activos relacionados directamente con la organización."""
        proyectos = set(
            ProyectoOrganizacion.objects.filter(
                organizacion=organizacion,
                activo=True,
            ).values_list("codigo", flat=True)
        )
        proyectos.update(
            Comedor.objects.filter(
                organizacion=organizacion,
                deleted_at__isnull=True,
            )
            .exclude(codigo_de_proyecto__isnull=True)
            .exclude(codigo_de_proyecto="")
            .values_list("codigo_de_proyecto", flat=True)
        )
        return sorted(proyectos)


class RendicionProcesoService:
    ACCION_INICIAR_TERRITORIAL = "iniciar_revision_territorial"
    ACCION_FINALIZAR_TERRITORIAL = "finalizar_revision_territorial"
    ACCION_INICIAR_REVISION_AUDITORIA = "iniciar_revision_auditoria"
    ACCION_FINALIZAR_REVISION_AUDITORIA = "finalizar_revision_auditoria"
    ACCION_INICIAR_AUDITORIA = "iniciar_auditoria"
    ACCION_FINALIZAR_SIN_OBSERVACIONES = "finalizar_sin_observaciones"
    ACCION_FINALIZAR_CON_OBSERVACIONES = "finalizar_con_observaciones"
    ACCION_INICIAR_REGULARIZACION = "iniciar_regularizacion"
    ACCION_FINALIZAR_REGULARIZACION = "finalizar_regularizacion"

    @staticmethod
    def _validar_documentos(rendicion):
        if not RendicionCuentaMensualService.rendicion_esta_completamente_validada(
            rendicion
        ):
            raise ValidationError(
                "No se puede finalizar la etapa mientras existan documentos sin validar."
            )

    @staticmethod
    def _validar_estado(rendicion, etapa, subestados):
        if (
            rendicion.etapa_proceso != etapa
            or rendicion.subestado_proceso not in subestados
        ):
            raise ValidationError(
                "La acción no corresponde al estado actual de la rendición."
            )

    @staticmethod
    @transaction.atomic
    def ejecutar(
        *, rendicion, accion, datos, actor=None
    ):  # pylint: disable=too-many-statements
        ahora = timezone.now()
        pendiente = RendicionCuentaMensual.SUBESTADO_PENDIENTE
        en_curso = RendicionCuentaMensual.SUBESTADO_EN_CURSO
        subsanado = RendicionCuentaMensual.SUBESTADO_SUBSANADO
        finalizada = RendicionCuentaMensual.SUBESTADO_FINALIZADA

        if accion == RendicionProcesoService.ACCION_INICIAR_TERRITORIAL:
            RendicionProcesoService._validar_estado(
                rendicion,
                RendicionCuentaMensual.ETAPA_REVISION_DOCUMENTACION,
                {pendiente, subsanado},
            )
            rendicion.subestado_proceso = en_curso
            rendicion.estado = RendicionCuentaMensual.ESTADO_REVISION
        elif accion == RendicionProcesoService.ACCION_FINALIZAR_TERRITORIAL:
            RendicionProcesoService._validar_estado(
                rendicion,
                RendicionCuentaMensual.ETAPA_REVISION_DOCUMENTACION,
                {en_curso},
            )
            RendicionProcesoService._validar_documentos(rendicion)
            rendicion.fecha_validacion_territorial = ahora
            rendicion.etapa_proceso = RendicionCuentaMensual.ETAPA_REVISION_AUDITORIA
            rendicion.subestado_proceso = pendiente
            rendicion.estado = RendicionCuentaMensual.ESTADO_FINALIZADA
        elif accion == RendicionProcesoService.ACCION_INICIAR_REVISION_AUDITORIA:
            RendicionProcesoService._validar_estado(
                rendicion,
                RendicionCuentaMensual.ETAPA_REVISION_AUDITORIA,
                {pendiente, subsanado},
            )
            rendicion.subestado_proceso = en_curso
            rendicion.estado = RendicionCuentaMensual.ESTADO_REVISION
            RendicionCuentaMensualService.documentos_vigentes_queryset(rendicion).filter(
                estado=DocumentacionAdjunta.ESTADO_VALIDADO
            ).update(
                estado=DocumentacionAdjunta.ESTADO_PRESENTADO,
                observaciones=None,
            )
        elif accion == RendicionProcesoService.ACCION_FINALIZAR_REVISION_AUDITORIA:
            RendicionProcesoService._validar_estado(
                rendicion,
                RendicionCuentaMensual.ETAPA_REVISION_AUDITORIA,
                {en_curso},
            )
            RendicionProcesoService._validar_documentos(rendicion)
            rendicion.fecha_validacion_auditoria = ahora
            rendicion.etapa_proceso = RendicionCuentaMensual.ETAPA_AUDITORIA
            rendicion.subestado_proceso = pendiente
            rendicion.estado = RendicionCuentaMensual.ESTADO_FINALIZADA
        elif accion == RendicionProcesoService.ACCION_INICIAR_AUDITORIA:
            RendicionProcesoService._validar_estado(
                rendicion,
                RendicionCuentaMensual.ETAPA_AUDITORIA,
                {pendiente},
            )
            rendicion.fecha_carga_auditoria = ahora
            rendicion.subestado_proceso = en_curso
        elif accion in {
            RendicionProcesoService.ACCION_FINALIZAR_SIN_OBSERVACIONES,
            RendicionProcesoService.ACCION_FINALIZAR_CON_OBSERVACIONES,
        }:
            RendicionProcesoService._validar_estado(
                rendicion,
                RendicionCuentaMensual.ETAPA_AUDITORIA,
                {en_curso},
            )
            rendicion.monto_rendido = datos["monto_rendido"]
            rendicion.acta_auditoria = datos["acta_auditoria"]
            rendicion.observaciones = datos.get("observaciones") or None
            rendicion.fecha_auditada = ahora
            rendicion.subestado_proceso = (
                RendicionCuentaMensual.SUBESTADO_FINALIZADA_CON_OBSERVACIONES
                if accion == RendicionProcesoService.ACCION_FINALIZAR_CON_OBSERVACIONES
                else finalizada
            )
        elif accion == RendicionProcesoService.ACCION_INICIAR_REGULARIZACION:
            RendicionProcesoService._validar_estado(
                rendicion,
                RendicionCuentaMensual.ETAPA_AUDITORIA,
                {RendicionCuentaMensual.SUBESTADO_FINALIZADA_CON_OBSERVACIONES},
            )
            rendicion.etapa_proceso = RendicionCuentaMensual.ETAPA_REGULARIZACION
            rendicion.subestado_proceso = en_curso
        elif accion == RendicionProcesoService.ACCION_FINALIZAR_REGULARIZACION:
            RendicionProcesoService._validar_estado(
                rendicion,
                RendicionCuentaMensual.ETAPA_REGULARIZACION,
                {en_curso},
            )
            rendicion.documento_regularizacion = datos["documento_regularizacion"]
            rendicion.fecha_regularizacion = ahora
            rendicion.subestado_proceso = finalizada
        else:
            raise ValidationError("Acción de proceso inválida.")

        RendicionCuentaMensualService.aplicar_usuario_ultima_modificacion(
            rendicion, actor
        )
        rendicion.save()
        return rendicion
