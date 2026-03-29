from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from users.bootstrap.groups_seed import bootstrap_group_names
from users.services_group_permissions import sync_permissions_for_group


EXTRA_GROUP_PERMISSION_CODES: dict[str, tuple[str, ...]] = {
    "VAT SSE": ("VAT.view_centro", "auth.role_vat_sse"),
    "ReferenteCentroVAT": ("VAT.view_centro", "auth.role_referentecentrovat"),
    "Provincia VAT": ("VAT.view_centro",),
}


def _resolve_permission(permission_code: str) -> Permission | None:
    try:
        app_label, codename = permission_code.split(".", 1)
    except ValueError:
        return None

    permission = Permission.objects.filter(
        content_type__app_label=app_label,
        codename=codename,
    ).first()
    if permission:
        return permission

    if app_label == "auth" and codename.startswith("role_"):
        content_type = ContentType.objects.get_for_model(Group)
        permission, _ = Permission.objects.get_or_create(
            content_type=content_type,
            codename=codename,
            defaults={"name": codename.replace("role_", "").replace("_", " ").title()},
        )
        return permission

    return None


def _assign_extra_permissions(group: Group) -> None:
    permission_codes = EXTRA_GROUP_PERMISSION_CODES.get(group.name, ())
    if not permission_codes:
        return

    permissions = [
        permission
        for permission in (_resolve_permission(code) for code in permission_codes)
        if permission is not None
    ]
    if permissions:
        group.permissions.add(*permissions)


class Command(BaseCommand):
    help = "Crea los grupos de usuario predeterminados"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS(f"Creando grupos de usuario..."))
        bootstrap_groups = []
        group_names = list(bootstrap_group_names())
        for extra_group_name in EXTRA_GROUP_PERMISSION_CODES:
            if extra_group_name not in group_names:
                group_names.append(extra_group_name)

        for group_name in group_names:
            group, created = Group.objects.get_or_create(name=group_name)
            bootstrap_groups.append(group)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Grupo "{group_name}" creado'))

        # Segunda pasada: asegura permisos cruzados entre grupos bootstrap
        # aun cuando algunos `auth.role_*` dependan de grupos creados más abajo.
        for group in bootstrap_groups:
            sync_permissions_for_group(group)
            _assign_extra_permissions(group)
