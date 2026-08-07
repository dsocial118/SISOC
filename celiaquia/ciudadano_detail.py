"""Contribucion de Celiaquia al detalle Ciudadano 360."""

from typing import Any

from celiaquia.models import ExpedienteCiudadano
from ciudadanos.detail_contributions import registrar_contribucion_detalle


def obtener_contexto(ciudadano: Any, logger: Any) -> dict[str, Any]:
    try:
        expedientes = (
            ExpedienteCiudadano.objects.filter(ciudadano=ciudadano)
            .select_related("expediente", "estado")
            .order_by("-creado_en")
        )
    except Exception:
        logger.exception(
            "Error cargando expedientes celiaquia para ciudadano %s", ciudadano.pk
        )
        return {"expedientes_celiaquia": []}

    contexto = {"expedientes_celiaquia": expedientes}
    expediente_actual = expedientes.first()
    if expediente_actual:
        contexto["expediente_actual"] = expediente_actual
    return contexto


def registrar_contribucion_ciudadano() -> None:
    registrar_contribucion_detalle("celiaquia", obtener_contexto)
