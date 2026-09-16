"""Payload y comparación de identidad para consumidores de RENAPER."""

from datetime import date, datetime

from django.utils import timezone

from ciudadanos.models import Ciudadano
from core.services.text_encoding import normalize_text, repair_utf8_mojibake


def build_validacion_renaper_payload(result):
    """Usar solo luego de verificar la identidad contra una respuesta confiable."""
    return {
        "estado_validacion_renaper": Ciudadano.RENAPER_VALIDADO,
        "fecha_validacion_renaper": timezone.now(),
        "datos_renaper": result.get("datos_api") or result.get("data") or {},
        "origen_dato": "renaper",
    }


def _fecha_identidad(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    for formato in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%Y%m%d"):
        try:
            return datetime.strptime(str(value or "").strip(), formato).date()
        except ValueError:
            continue
    return None


def identidad_coincide(datos_locales, datos_renaper):
    """Compara identidad completa reparando mojibake y normalizando diacríticos."""
    for campo in ("apellido", "nombre"):
        local = normalize_text(
            repair_utf8_mojibake(str(datos_locales.get(campo) or ""))
        )
        remoto = normalize_text(
            repair_utf8_mojibake(str(datos_renaper.get(campo) or ""))
        )
        if not local or local != remoto:
            return False
    fecha_local = _fecha_identidad(datos_locales.get("fecha_nacimiento"))
    fecha_remota = _fecha_identidad(datos_renaper.get("fecha_nacimiento"))
    return fecha_local is not None and fecha_local == fecha_remota
