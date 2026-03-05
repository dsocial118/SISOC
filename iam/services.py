from __future__ import annotations

from typing import Iterable

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.utils.text import slugify

from core.permissions.registry import resolve_permission_codes


def _normalize(values: Iterable[str]) -> set[str]:
    return {value for value in (str(v).strip() for v in values or []) if value}


def get_effective_role_names(user) -> set[str]:
    """Retorna roles efectivos (interpretados como permisos por nombre)."""
    if not user or not getattr(user, "is_authenticated", False):
        return set()

    cached = getattr(user, "cached_role_names", None)
    if cached is not None:
        return cached

    # Modelo objetivo: roles == permisos de Django asignados al usuario y sus grupos.
    role_names = set(
        Permission.objects.filter(Q(group__user=user) | Q(user=user))
        .distinct()
        .values_list("name", flat=True)
    )
    user.cached_role_names = role_names
    return role_names


def user_has_role(user, role_name: str) -> bool:
    """
    Compatibilidad histórica: valida un único permiso canónico.

    Nota: ya no resuelve aliases legacy por nombre de grupo.
    """
    return user_has_permission_code(user, role_name)


def user_has_any_role(user, role_names: Iterable[str]) -> bool:
    """
    Compatibilidad histórica: valida si tiene alguno de los permisos canónicos.

    Nota: ya no resuelve aliases legacy por nombre de grupo.
    """
    return user_has_any_permission_codes(user, role_names)


def get_effective_permission_codes(user) -> set[str]:
    """Permisos efectivos en formato app_label.codename."""
    if not user or not getattr(user, "is_authenticated", False):
        return set()

    cached = getattr(user, "cached_permission_codes", None)
    if cached is not None:
        return cached

    result = set(user.get_all_permissions())
    user.cached_permission_codes = result
    return result


def user_has_permission_code(user, permission_code: str) -> bool:
    """Valida un permiso app_label.codename."""
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if not permission_code:
        return False
    permission_codes = resolve_permission_codes([permission_code])
    if not permission_codes:
        return False
    return user.has_perm(permission_codes[0])


def user_has_any_permission_codes(user, permission_codes: Iterable[str]) -> bool:
    """Valida si el usuario tiene al menos uno de los permisos indicados."""
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return True

    normalized = _normalize(permission_codes)
    if not normalized:
        return False

    resolved = resolve_permission_codes(normalized)
    if not resolved:
        return False
    return any(user.has_perm(code) for code in resolved)


def user_has_all_permission_codes(user, permission_codes: Iterable[str]) -> bool:
    """Valida si el usuario tiene todos los permisos indicados."""
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return True

    normalized = _normalize(permission_codes)
    if not normalized:
        return False

    resolved = resolve_permission_codes(normalized)
    if not resolved:
        return False
    return all(user.has_perm(code) for code in resolved)


def ensure_role_for_group(group: Group) -> None:
    """
    Compatibilidad: garantiza un Permission homónimo al Group y lo asigna al grupo.

    Esto preserva los checks históricos basados en strings (p.ej. "Comedores Ver")
    mientras migramos a grupos con múltiples permisos.
    """
    if not group or not group.name:
        return

    content_type = ContentType.objects.get_for_model(Group)
    base_codename = f"role_{slugify(group.name).replace('-', '_')}"[:100]
    if not base_codename or base_codename == "role_":
        base_codename = f"role_group_{group.id}"

    codename = base_codename
    suffix = 1
    while (
        Permission.objects.filter(content_type=content_type, codename=codename)
        .exclude(name=group.name)
        .exists()
    ):
        suffix += 1
        codename = f"{base_codename[:95]}_{suffix}"[:100]

    permission, _ = Permission.objects.get_or_create(
        content_type=content_type,
        codename=codename,
        defaults={"name": group.name},
    )
    if permission.name != group.name:
        permission.name = group.name
        permission.save(update_fields=["name"])

    group.permissions.add(permission)
