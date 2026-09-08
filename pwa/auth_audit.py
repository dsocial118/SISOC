"""Registro del persistidor PWA para la auditoría de autenticación."""

from pwa.services.auditoria_service import registrar_evento_auth
from users.auth_audit import registrar_auditoria_auth


def registrar_auditoria_auth_pwa() -> None:
    """Conecta el persistidor PWA al puerto de autenticación de users."""
    registrar_auditoria_auth(registrar_evento_auth)
