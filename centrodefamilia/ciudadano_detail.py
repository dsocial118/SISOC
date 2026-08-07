"""Contribucion de Centro de Familia al detalle Ciudadano 360."""

from typing import Any

from django.db.models import Sum

from centrodefamilia.models import ParticipanteActividad
from ciudadanos.detail_contributions import registrar_contribucion_detalle


def obtener_contexto(ciudadano: Any, logger: Any) -> dict[str, Any]:
    try:
        participaciones = (
            ParticipanteActividad.objects.filter(ciudadano=ciudadano)
            .select_related("actividad_centro__centro", "actividad_centro__actividad")
            .order_by("-fecha_registro")
        )
        costo_total_cdf = (
            ParticipanteActividad.objects.filter(
                ciudadano=ciudadano, estado="inscrito"
            ).aggregate(total=Sum("actividad_centro__precio"))["total"]
            or 0
        )
    except Exception:
        logger.exception(
            "Error cargando participaciones CDF para ciudadano %s", ciudadano.pk
        )
        return {"participaciones_cdf": [], "costo_total_cdf": 0}
    return {
        "participaciones_cdf": participaciones,
        "costo_total_cdf": costo_total_cdf,
    }


def registrar_contribucion_ciudadano() -> None:
    registrar_contribucion_detalle("centrodefamilia", obtener_contexto)
