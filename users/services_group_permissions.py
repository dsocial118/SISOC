from __future__ import annotations

from typing import Iterable

from django.contrib.auth.models import Group, Permission

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
    return permissions


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
