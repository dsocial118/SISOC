import logging

from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404

from comedores.models import Comedor
from rendicioncuentasmensual.models import DocumentacionAdjunta, RendicionCuentaMensual

logger = logging.getLogger("django")


class RendicionCuentaMensualService:
    @staticmethod
    def _get_archivos_adjuntos_data(data):
        return data.get("archivos_adjuntos", data.get("arvhios_adjuntos"))

    @staticmethod
    def _asignar_archivos_adjuntos(rendicion, archivos_adjuntos):
        if archivos_adjuntos is None:
            return

        manager = getattr(rendicion, "archivos_adjuntos", None)
        if hasattr(manager, "set"):
            manager.set(archivos_adjuntos)
            return

        setattr(rendicion, "archivos_adjuntos", archivos_adjuntos)

    @staticmethod
    def _get_project_queryset(comedor):
        queryset = RendicionCuentaMensual.objects.filter(deleted_at__isnull=True)
        proyecto_codigo = (getattr(comedor, "codigo_de_proyecto", "") or "").strip()
        if proyecto_codigo:
            filters = {"comedor__codigo_de_proyecto": proyecto_codigo}
            organizacion_id = getattr(comedor, "organizacion_id", None)
            if organizacion_id:
                filters["comedor__organizacion_id"] = organizacion_id
            return queryset.filter(**filters)
        return queryset.filter(comedor=comedor)

    @staticmethod
    def _documentos_activos_queryset(rendicion):
        return rendicion.archivos_adjuntos.filter(deleted_at__isnull=True).order_by(
            "categoria", "fecha_creacion", "id"
        )

    @staticmethod
    def _sincronizar_flag_documento_adjunto(rendicion):
        tiene_documentos = RendicionCuentaMensualService._documentos_activos_queryset(
            rendicion
        ).exists()
        if rendicion.documento_adjunto != tiene_documentos:
            rendicion.documento_adjunto = tiene_documentos
            rendicion.save(update_fields=["documento_adjunto", "ultima_modificacion"])

    @staticmethod
    def _validar_numero_y_periodo(
        *,
        comedor,
        convenio,
        numero_rendicion,
        periodo_inicio,
        periodo_fin,
        exclude_id=None,
    ):
        queryset = RendicionCuentaMensualService._get_project_queryset(comedor)
        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)

        if queryset.filter(
            convenio=convenio,
            numero_rendicion=numero_rendicion,
        ).exists():
            raise ValidationError(
                {
                    "numero_rendicion": (
                        "Ya existe una rendición con ese número dentro del mismo convenio."
                    )
                }
            )

        if queryset.filter(
            convenio=convenio,
            periodo_inicio__lte=periodo_fin,
            periodo_fin__gte=periodo_inicio,
        ).exists():
            raise ValidationError(
                {
                    "periodo": (
                        "El período no puede repetirse ni solaparse dentro del mismo convenio."
                    )
                }
            )

    @staticmethod
    def _validar_categoria_documental(rendicion, categoria):
        config = DocumentacionAdjunta.get_categoria_config(categoria)
        if not config:
            raise ValidationError(
                {"categoria": "La categoría de documentación es inválida."}
            )

        if (
            not config["multiple"]
            and RendicionCuentaMensualService._documentos_activos_queryset(rendicion)
            .filter(categoria=categoria)
            .exists()
        ):
            raise ValidationError(
                {
                    "categoria": (
                        "Esta categoría admite un único documento activo por rendición."
                    )
                }
            )
        return config

    @staticmethod
    def _validar_rendicion_editable(rendicion):
        if rendicion.estado not in (
            RendicionCuentaMensual.ESTADO_ELABORACION,
            RendicionCuentaMensual.ESTADO_SUBSANAR,
        ):
            raise ValidationError(
                {
                    "detail": (
                        "La documentación solo puede modificarse en elaboración o subsanación."
                    )
                }
            )

    @staticmethod
    def obtener_resumen_documentacion(rendicion):
        documentos = list(
            RendicionCuentaMensualService._documentos_activos_queryset(rendicion)
        )
        grouped = {
            item["codigo"]: [] for item in DocumentacionAdjunta.categorias_mobile()
        }
        for documento in documentos:
            grouped.setdefault(documento.categoria, []).append(documento)
        return grouped

    @staticmethod
    def obtener_documentacion_para_detalle(rendicion):
        grouped = RendicionCuentaMensualService.obtener_resumen_documentacion(rendicion)
        categorias = []
        for categoria in DocumentacionAdjunta.categorias_mobile():
            categorias.append(
                {
                    **categoria,
                    "archivos": grouped.get(categoria["codigo"], []),
                }
            )
        return categorias

    @staticmethod
    def obtener_scope_proyecto(rendicion):
        comedor = getattr(rendicion, "comedor", None)
        organizacion = getattr(comedor, "organizacion", None) if comedor else None
        proyecto_codigo = (getattr(comedor, "codigo_de_proyecto", "") or "").strip()

        related_comedores = []
        if comedor:
            if proyecto_codigo:
                filters = {
                    "codigo_de_proyecto": proyecto_codigo,
                    "deleted_at__isnull": True,
                }
                organizacion_id = getattr(comedor, "organizacion_id", None)
                if organizacion_id:
                    filters["organizacion_id"] = organizacion_id
                related_comedores = list(
                    Comedor.objects.filter(**filters).order_by("nombre")
                )
            else:
                related_comedores = [comedor]

        return {
            "organizacion": organizacion,
            "proyecto_codigo": proyecto_codigo,
            "comedores_relacionados": related_comedores,
        }

    @staticmethod
    def validar_documentacion_obligatoria(rendicion):
        grouped = RendicionCuentaMensualService.obtener_resumen_documentacion(rendicion)
        faltantes = []
        for categoria in DocumentacionAdjunta.categorias_mobile():
            if categoria["required"] and not grouped.get(categoria["codigo"]):
                faltantes.append(categoria["label"])
        if faltantes:
            raise ValidationError(
                {
                    "detail": (
                        "Falta cargar documentación obligatoria: "
                        + ", ".join(faltantes)
                        + "."
                    )
                }
            )

    @staticmethod
    @transaction.atomic
    def crear_rendicion_mobile(*, comedor, data):
        convenio = (data.get("convenio") or "").strip()
        numero_rendicion = data.get("numero_rendicion")
        periodo_inicio = data.get("periodo_inicio")
        periodo_fin = data.get("periodo_fin")
        observaciones = (data.get("observaciones") or "").strip()

        RendicionCuentaMensualService._validar_numero_y_periodo(
            comedor=comedor,
            convenio=convenio,
            numero_rendicion=numero_rendicion,
            periodo_inicio=periodo_inicio,
            periodo_fin=periodo_fin,
        )

        return RendicionCuentaMensual.objects.create(
            comedor=comedor,
            mes=periodo_inicio.month,
            anio=periodo_inicio.year,
            convenio=convenio,
            numero_rendicion=numero_rendicion,
            periodo_inicio=periodo_inicio,
            periodo_fin=periodo_fin,
            estado=RendicionCuentaMensual.ESTADO_ELABORACION,
            observaciones=observaciones or None,
            documento_adjunto=False,
        )

    @staticmethod
    @transaction.atomic
    def adjuntar_documentacion_mobile(
        *,
        rendicion,
        categoria,
        archivo,
        nombre,
    ):
        RendicionCuentaMensualService._validar_rendicion_editable(rendicion)
        RendicionCuentaMensualService._validar_categoria_documental(
            rendicion, categoria
        )

        documento = DocumentacionAdjunta.objects.create(
            nombre=nombre,
            categoria=categoria,
            estado=DocumentacionAdjunta.ESTADO_PRESENTADO,
            archivo=archivo,
            rendicion_cuenta_mensual=rendicion,
        )
        RendicionCuentaMensualService._sincronizar_flag_documento_adjunto(rendicion)
        return documento

    @staticmethod
    @transaction.atomic
    def eliminar_documentacion_mobile(*, rendicion, documento):
        RendicionCuentaMensualService._validar_rendicion_editable(rendicion)
        if documento.rendicion_cuenta_mensual_id != rendicion.id:
            raise ValidationError(
                {"detail": "El documento no pertenece a la rendición."}
            )
        documento.delete()
        RendicionCuentaMensualService._sincronizar_flag_documento_adjunto(rendicion)

    @staticmethod
    @transaction.atomic
    def presentar_rendicion_mobile(rendicion):
        RendicionCuentaMensualService.validar_documentacion_obligatoria(rendicion)
        RendicionCuentaMensualService._sincronizar_flag_documento_adjunto(rendicion)
        rendicion.estado = RendicionCuentaMensual.ESTADO_REVISION
        rendicion.save(update_fields=["estado", "ultima_modificacion"])
        return rendicion

    @staticmethod
    @transaction.atomic
    def eliminar_rendicion_mobile(rendicion):
        RendicionCuentaMensualService._validar_rendicion_editable(rendicion)
        rendicion.delete()

    @staticmethod
    def crear_rendicion_cuenta_mensual(comedor, data):
        try:
            archivos_adjuntos = (
                RendicionCuentaMensualService._get_archivos_adjuntos_data(data)
            )
            rendicion = RendicionCuentaMensual.objects.create(
                comedor=comedor,
                mes=data.get("mes"),
                anio=data.get("anio"),
                convenio=data.get("convenio"),
                numero_rendicion=data.get("numero_rendicion"),
                periodo_inicio=data.get("periodo_inicio"),
                periodo_fin=data.get("periodo_fin"),
                estado=data.get("estado") or RendicionCuentaMensual.ESTADO_ELABORACION,
                documento_adjunto=data.get("documento_adjunto"),
                observaciones=data.get("observaciones"),
            )
            RendicionCuentaMensualService._asignar_archivos_adjuntos(
                rendicion, archivos_adjuntos
            )
            return rendicion
        except Exception:
            logger.exception(
                "Error en RendicionCuentaMensualService.crear_rendicion_cuenta_mensual",
                extra={"comedor_pk": getattr(comedor, "pk", None)},
            )
            raise

    @staticmethod
    def actualizar_rendicion_cuenta_mensual(rendicion, data):
        try:
            archivos_adjuntos = (
                RendicionCuentaMensualService._get_archivos_adjuntos_data(data)
            )
            rendicion.mes = data.get("mes")
            rendicion.anio = data.get("anio")
            rendicion.convenio = data.get("convenio")
            rendicion.numero_rendicion = data.get("numero_rendicion")
            rendicion.periodo_inicio = data.get("periodo_inicio")
            rendicion.periodo_fin = data.get("periodo_fin")
            rendicion.estado = (
                data.get("estado") or RendicionCuentaMensual.ESTADO_ELABORACION
            )
            rendicion.documento_adjunto = data.get("documento_adjunto")
            rendicion.observaciones = data.get("observaciones")
            RendicionCuentaMensualService._asignar_archivos_adjuntos(
                rendicion, archivos_adjuntos
            )
            rendicion.save()
            return rendicion
        except Exception:
            logger.exception(
                "Error en RendicionCuentaMensualService.actualizar_rendicion_cuenta_mensual",
                extra={"rendicion_pk": getattr(rendicion, "pk", None)},
            )
            raise

    @staticmethod
    def eliminar_rendicion_cuenta_mensual(rendicion):
        try:
            rendicion.delete()
        except Exception:
            logger.exception(
                "Error en RendicionCuentaMensualService.eliminar_rendicion_cuenta_mensual",
                extra={"rendicion_pk": getattr(rendicion, "pk", None)},
            )
            raise

    @staticmethod
    def obtener_rendiciones_cuentas_mensuales(comedor):
        try:
            return RendicionCuentaMensualService._get_project_queryset(comedor)
        except Exception:
            logger.exception(
                "Error en RendicionCuentaMensualService.obtener_rendiciones_cuentas_mensuales",
                extra={"comedor_pk": getattr(comedor, "pk", None)},
            )
            raise

    @staticmethod
    def obtener_todas_rendiciones_cuentas_mensuales():
        try:
            return (
                RendicionCuentaMensual.objects.filter(deleted_at__isnull=True)
                .select_related("comedor")
                .order_by("-ultima_modificacion", "-id")
            )
        except Exception:
            logger.exception(
                "Error en RendicionCuentaMensualService.obtener_todas_rendiciones_cuentas_mensuales"
            )
            raise

    @staticmethod
    def obtener_rendicion_cuenta_mensual(id_enviado):
        try:
            return get_object_or_404(RendicionCuentaMensual, pk=id_enviado)
        except Exception:
            logger.exception(
                "Error en RendicionCuentaMensualService.obtener_rendicion_cuenta_mensual para %s",
                id_enviado,
            )
            raise

    @staticmethod
    def cantidad_rendiciones_cuentas_mensuales(comedor):
        try:
            return RendicionCuentaMensualService._get_project_queryset(comedor).count()
        except Exception:
            logger.exception(
                "Error en RendicionCuentaMensualService.cantidad_rendiciones_cuentas_mensuales",
                extra={"comedor_pk": getattr(comedor, "pk", None)},
            )
            raise
