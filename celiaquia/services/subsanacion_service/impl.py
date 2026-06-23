"""Servicio de subsanaciones (Fase 2).

La provincia responde una subsanación adjuntando uno o varios archivos. La
documentación corregida se incorpora como evidencia nueva (`SubsanacionArchivo`)
SIN reemplazar los archivos originales del legajo (archivo1/2/3), preservando la
trazabilidad histórica.
"""

import logging

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from celiaquia.models import (
    ExpedienteCiudadano,
    RevisionTecnico,
    SubsanacionArchivo,
    SubsanacionEstado,
    SubsanacionObservacion,
)
from celiaquia.services.comentarios_service import ComentariosService

logger = logging.getLogger("django")


class SubsanacionService:
    @staticmethod
    def subsanacion_activa(legajo: ExpedienteCiudadano):
        """Devuelve la subsanación del ciclo actual del legajo (la más reciente),
        ya sea que esté pendiente de respuesta o ya respondida pero aún no
        confirmada. None si el legajo no tiene subsanaciones."""
        return legajo.subsanaciones.order_by("-solicitada_en", "-pk").first()

    @staticmethod
    def tiene_evidencia(legajo: ExpedienteCiudadano) -> bool:
        """True si la subsanación activa del legajo tiene evidencia de respuesta.

        Cuenta como evidencia un archivo nuevo (SubsanacionArchivo) del flujo
        actual o, por compatibilidad con subsanaciones en curso al momento del
        despliegue, una respuesta del flujo anterior (SubsanacionRespuesta)
        registrada durante el ciclo actual."""
        subsanacion = SubsanacionService.subsanacion_activa(legajo)
        if subsanacion is None:
            return False
        if subsanacion.archivos.exists():
            return True
        # Compatibilidad hacia atrás: respuesta cargada por el flujo previo
        # (reemplazo de archivos) dentro del ciclo de subsanación vigente.
        return legajo.subsanaciones_respuestas.filter(
            creado_en__gte=subsanacion.solicitada_en
        ).exists()

    @staticmethod
    def legajos_sin_evidencia(expediente):
        """Legajos en SUBSANAR cuya subsanación activa todavía no tiene archivos
        de respuesta cargados."""
        legajos = expediente.expediente_ciudadanos.filter(
            revision_tecnico=RevisionTecnico.SUBSANAR
        ).select_related("ciudadano")
        return [
            legajo
            for legajo in legajos
            if not SubsanacionService.tiene_evidencia(legajo)
        ]

    @staticmethod
    @transaction.atomic
    def responder(
        legajo: ExpedienteCiudadano,
        archivos,
        usuario=None,
        descripcion: str = "",
        observacion_id=None,
    ):
        """Registra la respuesta de la provincia a la subsanación activa del
        legajo: crea un SubsanacionArchivo por cada archivo adjunto (evidencia
        nueva) y marca la subsanación como RESPONDIDA. No modifica los archivos
        originales del legajo."""
        archivos = [a for a in (archivos or []) if a]
        if not archivos:
            raise ValidationError("Debés adjuntar al menos un archivo.")

        subsanacion = SubsanacionService.subsanacion_activa(legajo)
        if subsanacion is None:
            raise ValidationError(
                "El legajo no tiene una subsanación activa para responder."
            )

        observacion = None
        if observacion_id:
            observacion = SubsanacionObservacion.objects.filter(
                pk=observacion_id, subsanacion=subsanacion
            ).first()
            if observacion is None:
                raise ValidationError(
                    "La observación seleccionada no pertenece a la subsanación activa."
                )

        descripcion = (descripcion or "").strip()[:255]
        creados = [
            SubsanacionArchivo.objects.create(
                subsanacion=subsanacion,
                observacion=observacion,
                archivo=archivo,
                descripcion=descripcion,
                usuario=usuario,
            )
            for archivo in archivos
        ]

        subsanacion.estado = SubsanacionEstado.RESPONDIDA
        subsanacion.respondida_por = usuario
        subsanacion.respondida_en = timezone.now()
        subsanacion.save(update_fields=["estado", "respondida_por", "respondida_en"])

        comentario = f"La provincia adjuntó {len(creados)} archivo(s) de subsanación."
        if descripcion:
            comentario = f"{comentario} {descripcion}"
        try:
            ComentariosService.agregar_subsanacion_respuesta(
                legajo=legajo,
                respuesta=comentario,
                usuario=usuario,
                archivo_adjunto=creados[0].archivo if creados else None,
            )
        except Exception as exc:  # pragma: no cover - traza no crítica
            logger.warning(
                "No se pudo registrar el comentario de respuesta de subsanación "
                "para legajo %s: %s",
                legajo.pk,
                exc,
            )

        logger.info(
            "Subsanación %s respondida por user=%s con %s archivo(s) (legajo=%s).",
            subsanacion.pk,
            getattr(usuario, "id", None),
            len(creados),
            legajo.pk,
        )
        return subsanacion
