from django.db import migrations

from users.bootstrap.groups_seed import permission_codes_for_bootstrap_group


# Reconciliacion exacta de los grupos VAT administrativos. A diferencia de
# `create_groups` (aditivo), esta migracion deja cada grupo con EXACTAMENTE
# estos permisos de la semilla declarativa, removiendo los sobrantes en
# entornos ya existentes, salvo el permiso legado de rol del propio grupo.
RECONCILED_GROUP_NAMES = (
    "CFP",
    "INET_PROVINCIA",
    "INET Admin Visualizador",
    "INET Admin General",
)


def _resolve_permission(apps, code):
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")

    app_label, codename = code.split(".", 1)
    permission = Permission.objects.filter(
        content_type__app_label=app_label,
        codename=codename,
    ).first()
    if permission:
        return permission

    # Los permisos de rol (`auth.role_*`) son sinteticos y viven sobre el
    # ContentType de auth.Group; se crean on-demand si aun no existen (p. ej.
    # `role_admin_inet_general`, nuevo).
    if app_label == "auth" and codename.startswith("role_"):
        group_ct, _ = ContentType.objects.get_or_create(app_label="auth", model="group")
        name_suffix = codename[len("role_") :].replace("_", " ").strip()
        permission, _ = Permission.objects.get_or_create(
            content_type=group_ct,
            codename=codename,
            defaults={"name": name_suffix.title() or codename},
        )
        return permission

    return None


def reconcile_vat_admin_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")
    group_ct, _ = ContentType.objects.get_or_create(app_label="auth", model="group")

    for group_name in RECONCILED_GROUP_NAMES:
        group, _ = Group.objects.get_or_create(name=group_name)
        permissions = []
        for code in permission_codes_for_bootstrap_group(group_name):
            permission = _resolve_permission(apps, code)
            if permission:
                permissions.append(permission)
        # Preserva el permiso de compatibilidad legado creado por
        # ensure_role_for_group (iam/services.py), cuyo codename puede llevar
        # sufijo por colision y por eso se busca por name == nombre del grupo.
        legacy_role_permission = Permission.objects.filter(
            content_type=group_ct,
            name=group_name,
        ).first()
        if legacy_role_permission and legacy_role_permission not in permissions:
            permissions.append(legacy_role_permission)
        # `.set()` deja el grupo con los permisos reconciliados (quita sobrantes).
        group.permissions.set(permissions)


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0038_auditaccesocomedorpwa_update_permissions_choice"),
        ("VAT", "0001_squashed_0045"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.RunPython(
            reconcile_vat_admin_groups,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
