import logging
from datetime import date, datetime
from decimal import Decimal

from pwa.models import AuditoriaOperacionPWA

LOGGER = logging.getLogger(__name__)


def _json_safe(value):
    if isinstance(value, dict):
        return {str(key): _json_safe(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def registrar_evento_operacion(
    *,
    actor,
    comedor_id: int | None,
    entidad: str,
    entidad_id: int,
    accion: str,
    snapshot_antes: dict | None = None,
    snapshot_despues: dict | None = None,
    metadata: dict | None = None,
):
    try:
        AuditoriaOperacionPWA.objects.create(
            user=actor if getattr(actor, "is_authenticated", False) else None,
            comedor_id=comedor_id,
            entidad=entidad,
            entidad_id=entidad_id,
            accion=accion,
            snapshot_antes=_json_safe(snapshot_antes) if snapshot_antes else None,
            snapshot_despues=_json_safe(snapshot_despues) if snapshot_despues else None,
            metadata=_json_safe(metadata) if metadata else {},
        )
    except Exception:  # pragma: no cover
        LOGGER.exception("Error registrando auditoria de operacion PWA")
