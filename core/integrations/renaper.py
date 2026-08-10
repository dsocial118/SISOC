"""Cliente tecnico compartido para la integracion RENAPER."""

from __future__ import annotations

import logging
from typing import Any

import requests
from django.conf import settings
from django.core.cache import cache


logger = logging.getLogger("django")
TOKEN_CACHE_KEY = "renaper_token"


class RenaperServiceError(RuntimeError):
    """Error tecnico clasificado de la integracion RENAPER."""

    def __init__(self, message: str, error_type: str):
        super().__init__(message)
        self.error_type = error_type


def _error_result(message: str, error_type: str) -> dict[str, Any]:
    return {"success": False, "error": message, "error_type": error_type}


def _log_failure(
    operation: str,
    error_type: str,
    status_code: int | None = None,
) -> None:
    data = {"operation": operation, "error_type": error_type}
    if status_code is not None:
        data["status_code"] = status_code
    logger.warning("renaper.integration.failure", extra={"data": data})


class APIClient:
    """Encapsula autenticacion, cache, transporte y errores de RENAPER."""

    def __init__(self):
        self.username = settings.RENAPER_API_USERNAME
        self.password = settings.RENAPER_API_PASSWORD
        self.session = requests.Session()

    @property
    def login_url(self) -> str:
        return f"{settings.RENAPER_API_URL.rstrip('/')}/auth/login"

    @property
    def consulta_url(self) -> str:
        return f"{settings.RENAPER_API_URL.rstrip('/')}/consultarenaper"

    def get_token(self) -> str:
        token_data = cache.get(TOKEN_CACHE_KEY)
        if isinstance(token_data, dict) and token_data.get("token"):
            return token_data["token"]
        return self._login_and_cache_token()

    def _login_and_cache_token(self) -> str:
        try:
            response = self.session.post(
                self.login_url,
                json={"username": self.username, "password": self.password},
                timeout=settings.RENAPER_REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except requests.Timeout as exc:
            _log_failure("authenticate", "timeout")
            raise RenaperServiceError(
                "RENAPER no respondio a tiempo durante la autenticacion.", "timeout"
            ) from exc
        except requests.HTTPError as exc:
            status_code = getattr(exc.response, "status_code", None)
            error_type = "auth_error" if status_code in {401, 403} else "remote_error"
            _log_failure("authenticate", error_type, status_code)
            message = (
                "RENAPER rechazo la autenticacion."
                if error_type == "auth_error"
                else "RENAPER devolvio un error durante la autenticacion."
            )
            raise RenaperServiceError(message, error_type) from exc
        except requests.RequestException as exc:
            _log_failure("authenticate", "remote_error")
            raise RenaperServiceError(
                "No se pudo conectar al servicio de login de RENAPER.", "remote_error"
            ) from exc

        try:
            data = response.json()
        except ValueError as exc:
            _log_failure("authenticate", "invalid_response")
            raise RenaperServiceError(
                "RENAPER devolvio una respuesta invalida durante la autenticacion.",
                "invalid_response",
            ) from exc

        token = data.get("token") if isinstance(data, dict) else None
        if not token:
            _log_failure("authenticate", "invalid_response")
            raise RenaperServiceError(
                "RENAPER no devolvio un token de autenticacion.", "invalid_response"
            )

        cache.set(
            TOKEN_CACHE_KEY,
            {"token": token},
            settings.RENAPER_TOKEN_CACHE_TTL_SECONDS,
        )
        return token

    def consultar_ciudadano(self, dni: str, sexo: str) -> dict[str, Any]:
        try:
            token = self.get_token()
        except RenaperServiceError as exc:
            return _error_result(str(exc), exc.error_type)

        try:
            response = self.session.get(
                self.consulta_url,
                headers={"Authorization": f"Bearer {token}"},
                params={"dni": dni, "sexo": sexo.upper()},
                timeout=settings.RENAPER_REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except requests.Timeout:
            _log_failure("consult", "timeout")
            return _error_result(
                "RENAPER no respondio a tiempo durante la consulta.", "timeout"
            )
        except requests.HTTPError as exc:
            status_code = getattr(exc.response, "status_code", None)
            error_type = "auth_error" if status_code in {401, 403} else "remote_error"
            _log_failure("consult", error_type, status_code)
            message = (
                "RENAPER rechazo la autenticacion de la consulta."
                if error_type == "auth_error"
                else "RENAPER devolvio un error durante la consulta."
            )
            return _error_result(message, error_type)
        except requests.RequestException:
            _log_failure("consult", "remote_error")
            return _error_result("No se pudo consultar RENAPER.", "remote_error")

        return self._build_consulta_result(response)

    def _build_consulta_result(self, response: requests.Response) -> dict[str, Any]:
        """Normaliza la respuesta HTTP sin exponer el payload ante un error."""

        try:
            data = response.json()
        except ValueError:
            _log_failure("consult", "invalid_response")
            return _error_result(
                "RENAPER devolvio una respuesta invalida durante la consulta.",
                "invalid_response",
            )

        if not isinstance(data, dict):
            _log_failure("consult", "invalid_response")
            return _error_result(
                "RENAPER devolvio una estructura de respuesta invalida.",
                "invalid_response",
            )
        if not data.get("isSuccess", False):
            return _error_result("No se encontro coincidencia.", "no_match")

        result = data.get("result")
        if not isinstance(result, dict):
            _log_failure("consult", "invalid_response")
            return _error_result(
                "RENAPER devolvio una respuesta invalida.", "invalid_response"
            )
        return {"success": True, "data": result}
