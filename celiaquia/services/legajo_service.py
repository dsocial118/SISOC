import logging
from functools import lru_cache
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from celiaquia.models import (
    EstadoLegajo,
    ExpedienteCiudadano,
    RevisionTecnico,
)

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _estado_archivo_cargado_id():
    try:
        return EstadoLegajo.objects.only("id").get(nombre="ARCHIVO_CARGADO").id
    except EstadoLegajo.DoesNotExist:
        return None


def _set_estado_archivo_cargado(obj, update_fields):
    eid = _estado_archivo_cargado_id()
    if eid is not None and getattr(obj, "estado_id", None) != eid:
        obj.estado_id = eid
        update_fields.append("estado")


def _recalc_archivos_ok(obj, update_fields):
    if hasattr(obj, "archivos_ok"):
        val = bool(obj.archivo1 and obj.archivo2 and obj.archivo3)
        if obj.archivos_ok != val:
            obj.archivos_ok = val
            update_fields.append("archivos_ok")


class LegajoService:
    @staticmethod
    def listar_legajos(expediente):
        return expediente.expediente_ciudadanos.select_related(
            "ciudadano", "estado"
        ).order_by("creado_en")

    @staticmethod
    @transaction.atomic
    def subir_archivo_individual(
        exp_ciudadano: ExpedienteCiudadano, archivo, slot: int | None = None
    ):
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

        _set_estado_archivo_cargado(exp_ciudadano, changed)
        _recalc_archivos_ok(exp_ciudadano, changed)

        changed.append("modificado_en")
        exp_ciudadano.save(update_fields=changed)
        logger.info(
            "Legajo %s: archivo actualizado en %s.", exp_ciudadano.pk, ",".join(changed)
        )
        return exp_ciudadano

    @staticmethod
    @transaction.atomic
    def subir_archivos_iniciales(
        exp_ciudadano: ExpedienteCiudadano, archivo1, archivo2, archivo3
    ):
        if not archivo1 or not archivo2 or not archivo3:
            raise ValidationError("Debés adjuntar los tres archivos requeridos.")

        exp_ciudadano.archivo1 = archivo1
        exp_ciudadano.archivo2 = archivo2
        exp_ciudadano.archivo3 = archivo3

        update_fields = ["archivo1", "archivo2", "archivo3"]
        _set_estado_archivo_cargado(exp_ciudadano, update_fields)
        _recalc_archivos_ok(exp_ciudadano, update_fields)

        update_fields.append("modificado_en")
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

        _set_estado_archivo_cargado(exp_ciudadano, changed)
        _recalc_archivos_ok(exp_ciudadano, changed)

        changed.append("modificado_en")
        exp_ciudadano.save(update_fields=changed)
        logger.info(
            "Legajo %s: subsanación, archivos actualizados: %s.",
            exp_ciudadano.pk,
            ",".join(changed),
        )
        return exp_ciudadano

    @staticmethod
    @transaction.atomic
    def solicitar_subsanacion(exp_ciudadano: ExpedienteCiudadano, motivo: str, usuario):
        if not motivo or not motivo.strip():
            raise ValidationError("Debés indicar un motivo de subsanación.")
        exp_ciudadano.revision_tecnico = RevisionTecnico.SUBSANAR
        exp_ciudadano.subsanacion_motivo = motivo.strip()[:500]
        exp_ciudadano.subsanacion_solicitada_en = timezone.now()
        exp_ciudadano.save(
            update_fields=[
                "revision_tecnico",
                "subsanacion_motivo",
                "subsanacion_solicitada_en",
                "modificado_en",
            ]
        )
        logger.info(
            "Legajo %s: subsanación solicitada por %s.",
            exp_ciudadano.pk,
            getattr(usuario, "username", usuario),
        )
        return exp_ciudadano

    @staticmethod
    def all_legajos_loaded(expediente) -> bool:
        qs = expediente.expediente_ciudadanos
        if hasattr(ExpedienteCiudadano, "archivos_ok"):
            return not qs.filter(archivos_ok=False).exists()
        return (
            not qs.filter(archivo1__isnull=True).exists()
            and not qs.filter(archivo2__isnull=True).exists()
            and not qs.filter(archivo3__isnull=True).exists()
        )

    @staticmethod
    def faltantes_archivos(
        expediente, limit: int | None = None, friendly_names: dict | None = None
    ):
        """
        Devuelve una lista de dicts con legajos que NO tienen los 3 archivos.
        - limit: corta la lista al llegar a N (útil para previsualización).
        - friendly_names: mapping opcional para mostrar nombres legibles de cada archivo.
        """
        friendly_names = friendly_names or {
            "archivo1": "DNI",
            "archivo2": "Biopsia / Constancia médica",
            "archivo3": "Negativa ANSES",
        }

        qs = expediente.expediente_ciudadanos.select_related(
            "ciudadano", "estado"
        ).only(
            "id",
            "archivo1",
            "archivo2",
            "archivo3",
            "revision_tecnico",
            "estado_id",
            "ciudadano__documento",
            "ciudadano__nombre",
            "ciudadano__apellido",
        )
        if hasattr(ExpedienteCiudadano, "archivos_ok"):
            qs = qs.filter(archivos_ok=False)

        faltantes = []
        for leg in qs.iterator():
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
                        "estado": getattr(getattr(leg, "estado", None), "nombre", None),
                        "revision_tecnico": getattr(leg, "revision_tecnico", None),
                        "archivos_ok": getattr(leg, "archivos_ok", None),
                        "faltan": miss,
                        "faltan_nombres": [friendly_names.get(m, m) for m in miss],
                    }
                )
                if limit and len(faltantes) >= limit:
                    break

        return faltantes
