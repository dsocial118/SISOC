"""Contribucion de PWA al detalle Ciudadano 360."""

from typing import Any

from ciudadanos.detail_contributions import registrar_contribucion_detalle
from pwa.models import NominaEspacioPWA


def obtener_contexto(ciudadano: Any, _logger: Any) -> dict[str, Any]:
    perfiles = NominaEspacioPWA.objects.filter(
        nomina__ciudadano=ciudadano,
        activo=True,
    )
    return {
        "pertenece_comunidad_indigena": perfiles.filter(
            pertenece_comunidad_indigena=True
        ).exists(),
        "situacion_calle_pwa": perfiles.filter(situacion_calle=True).exists(),
        "persona_con_celiaquia_pwa": perfiles.filter(
            persona_con_celiaquia=True
        ).exists(),
    }


def registrar_contribucion_ciudadano() -> None:
    registrar_contribucion_detalle("pwa", obtener_contexto)
