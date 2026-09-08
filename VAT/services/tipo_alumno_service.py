"""Clasificación de alumnos según tengan voucher VAT activo o no.

Regla de negocio (issue "Diferenciación visual de alumnos VAT"):
voucher con estado "activo" y vencimiento vigente → "VAT"; caso contrario
→ "Sin Plan". El estado "vencido" se estampa de forma perezosa al validar,
por eso además del estado se chequea la fecha de vencimiento. El cálculo es
exclusivamente backend y comparten esta única implementación tanto los
listados (asistencia, detalle de comisión) como las exportaciones.
"""

from django.db.models import Exists, OuterRef
from django.utils import timezone

from VAT.models import Voucher

TIPO_ALUMNO_VAT = "VAT"
TIPO_ALUMNO_SIN_PLAN = "Sin Plan"


def _vouchers_activos_queryset():
    return Voucher.objects.filter(
        estado="activo",
        fecha_vencimiento__gte=timezone.localdate(),
    )


def tipo_alumno_label(tiene_voucher_activo) -> str:
    return TIPO_ALUMNO_VAT if tiene_voucher_activo else TIPO_ALUMNO_SIN_PLAN


def tiene_voucher_activo_subquery(ciudadano_field="ciudadano_id"):
    """Expresión ``Exists`` para anotar querysets de Inscripcion."""
    return Exists(
        _vouchers_activos_queryset().filter(ciudadano_id=OuterRef(ciudadano_field))
    )


def ciudadanos_con_voucher_activo(ciudadano_ids) -> set:
    ciudadano_ids = {pk for pk in ciudadano_ids if pk}
    if not ciudadano_ids:
        return set()
    return set(
        _vouchers_activos_queryset()
        .filter(ciudadano_id__in=ciudadano_ids)
        .values_list("ciudadano_id", flat=True)
    )


def anotar_tipo_alumno(inscripciones):
    """Setea ``es_alumno_vat`` y ``tipo_alumno`` en cada inscripción (una sola
    query por lote). Devuelve la misma lista para poder encadenar."""
    ids_vat = ciudadanos_con_voucher_activo(
        inscripcion.ciudadano_id for inscripcion in inscripciones
    )
    for inscripcion in inscripciones:
        inscripcion.es_alumno_vat = inscripcion.ciudadano_id in ids_vat
        inscripcion.tipo_alumno = tipo_alumno_label(inscripcion.es_alumno_vat)
    return inscripciones
