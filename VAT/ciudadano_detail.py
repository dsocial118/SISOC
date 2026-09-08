"""Contribucion de VAT al detalle Ciudadano 360."""

from collections import defaultdict
from typing import Any

from ciudadanos.detail_contributions import registrar_contribucion_detalle
from VAT.models import AsistenciaSesion, Inscripcion, InscripcionOferta, Voucher


def obtener_contexto(  # pylint: disable=too-many-locals,too-many-branches
    ciudadano: Any, logger: Any
) -> dict[str, Any]:
    try:
        inscripciones = list(
            Inscripcion.objects.filter(ciudadano=ciudadano)
            .select_related("comision__oferta__centro", "programa")
            .prefetch_related("comision__oferta__plan_curricular__titulos")
            .order_by("-fecha_inscripcion")
        )
        vouchers = list(
            Voucher.objects.filter(ciudadano=ciudadano)
            .select_related("programa")
            .order_by("-fecha_asignacion")
        )
        inscripciones_oferta = list(
            InscripcionOferta.objects.filter(ciudadano=ciudadano)
            .select_related("oferta__oferta__centro")
            .prefetch_related("oferta__oferta__plan_curricular__titulos")
            .order_by("-fecha_inscripcion")
        )
        asistencias = list(
            AsistenciaSesion.objects.filter(inscripcion__ciudadano=ciudadano)
            .select_related("inscripcion")
            .order_by("-fecha_registro")
        )
    except Exception:
        logger.exception("Error cargando datos VAT para ciudadano %s", ciudadano.pk)
        return _contexto_vacio()

    creditos_totales = sum(voucher.cantidad_inicial for voucher in vouchers)
    creditos_disponibles = sum(
        voucher.cantidad_disponible
        for voucher in vouchers
        if voucher.estado == "activo"
    )
    voucher_activo = next(
        (voucher for voucher in vouchers if voucher.estado == "activo"), None
    )
    asistencias_por_inscripcion = defaultdict(
        lambda: {"presentes": 0, "registradas": 0}
    )

    for asistencia in asistencias:
        resumen = asistencias_por_inscripcion[asistencia.inscripcion_id]
        resumen["registradas"] += 1
        if asistencia.presente:
            resumen["presentes"] += 1

    for inscripcion in inscripciones:
        resumen = asistencias_por_inscripcion.get(
            inscripcion.id, {"presentes": 0, "registradas": 0}
        )
        registradas = resumen["registradas"]
        inscripcion.asistencias_presentes = resumen["presentes"]
        inscripcion.asistencias_registradas = registradas
        inscripcion.asistencia_porcentaje = (
            round((resumen["presentes"] / registradas) * 100) if registradas else 0
        )

    programas: dict[int, dict[str, Any]] = {}

    def asegurar_programa(programa: Any) -> dict[str, Any] | None:
        if not programa:
            return None
        if programa.id not in programas:
            programas[programa.id] = {
                "programa": programa,
                "vouchers": [],
                "voucher_activo": None,
                "voucher_referencia": None,
                "inscripciones": [],
                "inscripciones_oferta": [],
                "creditos_totales": 0,
                "creditos_actuales": 0,
                "cursos_asignados": 0,
                "asistencias_presentes": 0,
                "asistencias_registradas": 0,
            }
        return programas[programa.id]

    for voucher in vouchers:
        programa_ctx = asegurar_programa(voucher.programa)
        if not programa_ctx:
            continue
        programa_ctx["vouchers"].append(voucher)
        programa_ctx["creditos_totales"] += voucher.cantidad_inicial
        if voucher.estado == "activo":
            programa_ctx["creditos_actuales"] += voucher.cantidad_disponible
            if programa_ctx["voucher_activo"] is None:
                programa_ctx["voucher_activo"] = voucher
        if programa_ctx["voucher_referencia"] is None:
            programa_ctx["voucher_referencia"] = voucher

    for inscripcion in inscripciones:
        programa_ctx = asegurar_programa(inscripcion.programa)
        if not programa_ctx:
            continue
        programa_ctx["inscripciones"].append(inscripcion)
        programa_ctx["cursos_asignados"] += 1
        programa_ctx["asistencias_presentes"] += inscripcion.asistencias_presentes
        programa_ctx["asistencias_registradas"] += inscripcion.asistencias_registradas

    for inscripcion_oferta in inscripciones_oferta:
        programa = getattr(
            getattr(inscripcion_oferta.oferta, "oferta", None), "programa", None
        )
        programa_ctx = asegurar_programa(programa)
        if not programa_ctx:
            continue
        programa_ctx["inscripciones_oferta"].append(inscripcion_oferta)
        programa_ctx["cursos_asignados"] += 1

    return {
        "vat_inscripciones": inscripciones,
        "vat_vouchers": vouchers,
        "vat_inscripciones_oferta": inscripciones_oferta,
        "vat_creditos_totales": creditos_totales,
        "vat_creditos_disponibles": creditos_disponibles,
        "vat_voucher_activo": voucher_activo,
        "vat_programas": sorted(
            programas.values(), key=lambda item: str(item["programa"]).lower()
        ),
    }


def _contexto_vacio() -> dict[str, Any]:
    return {
        "vat_inscripciones": [],
        "vat_vouchers": [],
        "vat_inscripciones_oferta": [],
        "vat_programas": [],
    }


def registrar_contribucion_ciudadano() -> None:
    registrar_contribucion_detalle("vat", obtener_contexto)
