"""Contribucion de Comedores al detalle Ciudadano 360."""

from typing import Any

from ciudadanos.detail_contributions import registrar_contribucion_detalle
from comedores.models import ColaboradorEspacio, Nomina


def obtener_contexto(ciudadano: Any, logger: Any) -> dict[str, Any]:
    try:
        nominas = list(
            Nomina.objects.filter(ciudadano=ciudadano)
            .select_related(
                "admision__comedor__provincia",
                "admision__comedor__municipio",
                "admision__comedor__tipocomedor",
            )
            .order_by("-fecha")
        )
        colaboraciones = list(
            ColaboradorEspacio.objects.filter(ciudadano=ciudadano)
            .select_related(
                "comedor__provincia",
                "comedor__municipio",
                "comedor__tipocomedor",
            )
            .prefetch_related("actividades")
            .order_by("-fecha_alta", "-id")
        )
    except Exception:
        logger.exception(
            "Error cargando nominas de comedor para ciudadano %s", ciudadano.pk
        )
        return {"nominas_comedor": [], "colaboraciones_comedor": []}

    contexto = {
        "nominas_comedor": nominas,
        "colaboraciones_comedor": colaboraciones,
    }
    if nominas:
        contexto["nomina_actual"] = nominas[0]
    return contexto


def registrar_contribucion_ciudadano() -> None:
    registrar_contribucion_detalle("comedores", obtener_contexto)
