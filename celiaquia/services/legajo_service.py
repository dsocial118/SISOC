import logging
from django.db import transaction
from django.core.exceptions import ValidationError

from celiaquia.models import (
    EstadoLegajo,
    ExpedienteCiudadano,
    RevisionTecnico,
)

logger = logging.getLogger(__name__)


class LegajoService:
    @staticmethod
    def listar_legajos(expediente):
        return (
            expediente.expediente_ciudadanos
            .select_related("ciudadano", "estado")
            .order_by("creado_en")
        )

    @staticmethod
    @transaction.atomic
    def subir_archivo_individual(exp_ciudadano: ExpedienteCiudadano, archivo, slot: int | None = None):
        if not archivo:
            raise ValidationError("Debe proporcionar un archivo válido.")
        if slot is not None and slot not in (1, 2, 3):
            raise ValidationError("Slot inválido. Debe ser 1, 2 o 3.")

        changed = []
        if slot == 1 or (slot is None and not exp_ciudadano.archivo1):
            exp_ciudadano.archivo1 = archivo
            changed.append("archivo1")
        elif slot == 2 or (slot is None and not exp_ciudadano.archivo2):
            exp_ciudadano.archivo2 = archivo
            changed.append("archivo2")
        elif slot == 3 or (slot is None and not exp_ciudadano.archivo3):
            exp_ciudadano.archivo3 = archivo
            changed.append("archivo3")
        else:
            raise ValidationError("Los tres archivos ya se encuentran cargados.")

        try:
            estado_cargado = EstadoLegajo.objects.get(nombre="ARCHIVO_CARGADO")
        except EstadoLegajo.DoesNotExist:
            estado_cargado = None

        if estado_cargado:
            exp_ciudadano.estado = estado_cargado
            changed.append("estado")

        changed.append("modificado_en")
        exp_ciudadano.save(update_fields=changed)
        logger.info("Legajo %s: archivo actualizado en %s.", exp_ciudadano.pk, ",".join(changed))
        return exp_ciudadano

    @staticmethod
    @transaction.atomic
    def subir_archivos_iniciales(exp_ciudadano: ExpedienteCiudadano, archivo1, archivo2, archivo3):
        if not archivo1 or not archivo2 or not archivo3:
            raise ValidationError("Debés adjuntar los tres archivos requeridos.")
        try:
            estado_cargado = EstadoLegajo.objects.get(nombre="ARCHIVO_CARGADO")
        except EstadoLegajo.DoesNotExist:
            estado_cargado = None

        exp_ciudadano.archivo1 = archivo1
        exp_ciudadano.archivo2 = archivo2
        exp_ciudadano.archivo3 = archivo3
        update_fields = ["archivo1", "archivo2", "archivo3", "modificado_en"]
        if estado_cargado:
            exp_ciudadano.estado = estado_cargado
            update_fields.append("estado")
        exp_ciudadano.save(update_fields=update_fields)
        logger.info("Legajo %s: tres archivos cargados.", exp_ciudadano.pk)
        return exp_ciudadano

    @staticmethod
    @transaction.atomic
    def actualizar_archivos_subsanacion(
        exp_ciudadano: ExpedienteCiudadano,
        archivo1=None,
        archivo2=None,
        archivo3=None,
    ):
        changed = []
        if archivo1:
            exp_ciudadano.archivo1 = archivo1
            changed.append("archivo1")
        if archivo2:
            exp_ciudadano.archivo2 = archivo2
            changed.append("archivo2")
        if archivo3:
            exp_ciudadano.archivo3 = archivo3
            changed.append("archivo3")
        if not changed:
            raise ValidationError("Debés subir al menos un archivo para subsanar.")

        changed.append("modificado_en")
        exp_ciudadano.save(update_fields=changed)
        logger.info("Legajo %s: subsanación, archivos actualizados: %s.", exp_ciudadano.pk, ",".join(changed))
        return exp_ciudadano

    @staticmethod
    @transaction.atomic
    def solicitar_subsanacion(exp_ciudadano: ExpedienteCiudadano, motivo: str, usuario):
        if not motivo or not motivo.strip():
            raise ValidationError("Debés indicar un motivo de subsanación.")
        exp_ciudadano.revision_tecnico = RevisionTecnico.SUBSANAR
        exp_ciudadano.subsanacion_motivo = motivo.strip()[:500]
        exp_ciudadano.subsanacion_solicitada_por = usuario
        exp_ciudadano.save(update_fields=["revision_tecnico", "subsanacion_motivo", "subsanacion_solicitada_por", "modificado_en"])
        logger.info("Legajo %s: subsanación solicitada por %s.", exp_ciudadano.pk, getattr(usuario, "username", usuario))
        return exp_ciudadano

    @staticmethod
    def all_legajos_loaded(expediente) -> bool:
        return not expediente.expediente_ciudadanos.filter(
            archivo1__isnull=True
        ).exists() and not expediente.expediente_ciudadanos.filter(
            archivo2__isnull=True
        ).exists() and not expediente.expediente_ciudadanos.filter(
            archivo3__isnull=True
        ).exists()

    @staticmethod
    def faltantes_archivos(expediente):
        faltantes = []
        for leg in expediente.expediente_ciudadanos.select_related("ciudadano").all():
            miss = []
            if not leg.archivo1:
                miss.append("archivo1")
            if not leg.archivo2:
                miss.append("archivo2")
            if not leg.archivo3:
                miss.append("archivo3")
            if miss:
                faltantes.append(
                    {
                        "legajo_id": leg.id,
                        "documento": getattr(leg.ciudadano, "documento", ""),
                        "nombre": getattr(leg.ciudadano, "nombre", ""),
                        "apellido": getattr(leg.ciudadano, "apellido", ""),
                        "faltan": miss,
                    }
                )
        return faltantes
