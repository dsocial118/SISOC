"""Regla de navegacion exclusiva del dominio VAT."""

from typing import Any

from VAT.services.access_scope import is_vat_provincial, is_vat_referente, is_vat_sse
from core.services.sidebar_access import registrar_predicado_sidebar


def es_usuario_solo_vat(user: Any) -> bool:
    if not user or not user.is_authenticated or user.is_superuser:
        return False
    return bool(is_vat_sse(user) or is_vat_referente(user) or is_vat_provincial(user))


def registrar_acceso_sidebar() -> None:
    registrar_predicado_sidebar("vat", es_usuario_solo_vat)
