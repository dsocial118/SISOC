"""Fachada compartida y compatible para consultas RENAPER."""

from __future__ import annotations

import logging
import unicodedata
from typing import Any

from core.integrations.renaper import APIClient
from core.models import Sexo


logger = logging.getLogger("django")
_RENAPER_INT_PLACEHOLDERS = {
    "",
    "0",
    "-",
    "n/a",
    "na",
    "n/d",
    "nd",
    "s/d",
    "sd",
    "s/n",
    "sn",
    "sinnumero",
    "sinnro",
}


def _error_result(message: str, error_type: str, **extra: Any) -> dict[str, Any]:
    return {"success": False, "error": message, "error_type": error_type, **extra}


def _log_unexpected_error(event: str, exc: Exception) -> None:
    """Conserva el traceback sin registrar el mensaje potencialmente sensible."""
    sanitized_error = RuntimeError("unexpected RENAPER integration error")
    logger.exception(
        event,
        exc_info=(RuntimeError, sanitized_error, exc.__traceback__),
    )


def _normalizar(texto: object) -> str:
    if not texto:
        return ""
    return (
        unicodedata.normalize("NFKD", str(texto).lower().replace("_", " "))
        .encode("ascii", "ignore")
        .decode("utf-8")
        .strip()
    )


def _safe_int_renaper(value: object) -> int | None:
    if value is None:
        return None
    value_text = str(value).strip()
    if _normalizar(value_text).replace(" ", "") in _RENAPER_INT_PLACEHOLDERS:
        return None
    try:
        parsed_value = int(value_text)
    except (TypeError, ValueError):
        return None
    return parsed_value or None


def _mapear_datos_renaper(datos: dict[str, Any], dni: str, sexo: str) -> dict[str, Any]:
    sexo_texto = {"F": "Femenino", "M": "Masculino", "X": "X"}.get(sexo)
    sexo_pk = None
    if sexo_texto:
        sexo_obj = Sexo.objects.filter(sexo=sexo_texto).first()
        sexo_pk = sexo_obj.pk if sexo_obj else None

    return {
        "cuil": _safe_int_renaper(datos.get("cuil")),
        "dni": int(dni),
        "apellido": datos.get("apellido", ""),
        "nombre": datos.get("nombres", ""),
        "genero": sexo,
        "sexo": sexo_pk,
        "tipo_documento": "DNI",
        "fecha_nacimiento": datos.get("fechaNacimiento"),
        "provincia_api": datos.get("provincia", ""),
        "municipio_api": datos.get("municipio", ""),
        "localidad_api": datos.get("ciudad", ""),
        "codigo_postal": _safe_int_renaper(datos.get("cpostal")),
        "calle": datos.get("calle", ""),
        "altura": _safe_int_renaper(datos.get("numero")),
        "piso_vivienda": datos.get("piso", "") or None,
        "departamento_vivienda": datos.get("departamento", "") or None,
        "barrio": (
            datos.get("barrio") if datos.get("barrio") not in {"0", "", None} else None
        ),
        "monoblock": datos.get("monoblock") or None,
        "nacionalidad_api": datos.get("pais") or "",
    }


def consultar_datos_renaper(dni: str, sexo: str) -> dict[str, Any]:
    """Adaptador temporal del contrato compartido de consulta ciudadana."""
    try:
        response = APIClient().consultar_ciudadano(dni, sexo)
        if not response.get("success"):
            return _error_result(
                response.get("error", "Error desconocido al consultar RENAPER"),
                response.get("error_type", "unexpected_error"),
            )

        datos = response.get("data")
        if not isinstance(datos, dict):
            return _error_result(
                "RENAPER devolvio un payload invalido del ciudadano.",
                "invalid_response",
            )
        if datos.get("mensaf") == "FALLECIDO":
            return _error_result(
                "El ciudadano se encuentra fallecido.", "fallecido", fallecido=True
            )
        return {
            "success": True,
            "data": _mapear_datos_renaper(datos, dni, sexo),
            "datos_api": datos,
        }
    except Exception as exc:  # pylint: disable=broad-exception-caught
        _log_unexpected_error("renaper.integration.unhandled_error", exc)
        return _error_result(
            "Error inesperado al consultar RENAPER.", "unexpected_error"
        )
