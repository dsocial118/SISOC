from __future__ import annotations

from typing import Iterable

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from core.permissions.registry import (
    permission_codes_for_bootstrap_group,
)
from iam.services import ensure_role_for_group


def _permissions_from_codes(permission_codes: Iterable[str]) -> list[Permission]:
    permissions: list[Permission] = []
    for permission_code in permission_codes:
        try:
            app_label, codename = permission_code.split(".", 1)
        except ValueError:
            continue
        permission = (
            Permission.objects.select_related("content_type")
            .filter(content_type__app_label=app_label, codename=codename)
            .first()
        )
        if permission:
            permissions.append(permission)
            continue

        role_permission = _ensure_role_permission_exists(app_label, codename)
        if role_permission:
            permissions.append(role_permission)
    return permissions


def _ensure_role_permission_exists(app_label: str, codename: str) -> Permission | None:
    if app_label != "auth" or not codename.startswith("role_"):
        return None

    content_type = ContentType.objects.get_for_model(Group)
    name_suffix = codename[len("role_") :].replace("_", " ").strip()
    defaults = {"name": name_suffix.title() or codename}
    permission, _ = Permission.objects.get_or_create(
        content_type=content_type,
        codename=codename,
        defaults=defaults,
    )
    return permission


def sync_permissions_for_group(group: Group) -> None:
    if not group:
        return

    ensure_role_for_group(group)
    permission_codes = permission_codes_for_bootstrap_group(group.name)
    permissions = _permissions_from_codes(permission_codes)
    if permissions:
        group.permissions.add(*permissions)


def sync_bootstrapped_group_permissions() -> None:
    for group in Group.objects.all():
        sync_permissions_for_group(group)
