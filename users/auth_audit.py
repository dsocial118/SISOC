"""Puerto de auditoría para eventos de autenticación."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


EVENTO_LOGIN_OK = "login_ok"
EVENTO_LOGIN_ERROR = "login_error"
EVENTO_LOGOUT = "logout"
EVENTO_ME_OK = "me_ok"
RESULTADO_OK = "ok"
RESULTADO_ERROR = "error"

AuthAuditHandler = Callable[..., None]
_registrar_evento: AuthAuditHandler | None = None


def registrar_auditoria_auth(handler: AuthAuditHandler) -> None:
    """Registra el persistidor de auditoría de autenticación."""
    global _registrar_evento

    if _registrar_evento is None or _registrar_evento is handler:
        _registrar_evento = handler
        return
    raise ValueError("Ya existe un persistidor de auditoría de autenticación.")


def registrar_evento_auth(**kwargs: Any) -> None:
    """Persiste un evento mediante el proveedor registrado por el dominio."""
    if _registrar_evento is None:
        raise RuntimeError("No hay un persistidor de auditoría de autenticación.")
    _registrar_evento(**kwargs)
