from django.db import migrations


ACOMPANAMIENTO_PERMISSION_CODES = (
    "acompanamientos.view_informacionrelevante",
    "auth.role_acompanamiento_listar",
    "auth.role_acompanamiento_detalle",
)
COMEDORES_GROUPS = ("Comedores total", "Comedores Visualización")


def _get_permission(apps, permission_code):
    Permission = apps.get_model("auth", "Permission")
    app_label, codename = permission_code.split(".", 1)
    return Permission.objects.filter(
        content_type__app_label=app_label,
        codename=codename,
    ).first()


def revoke_generic_comedores_acompanamiento_access(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    permissions = [
        permission
        for code in ACOMPANAMIENTO_PERMISSION_CODES
        if (permission := _get_permission(apps, code)) is not None
    ]

    if not permissions:
        return

    for group in Group.objects.filter(name__in=COMEDORES_GROUPS):
        group.permissions.remove(*permissions)


def grant_hitos_change_to_tecnico_comedor(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    permission = _get_permission(apps, "acompanamientos.change_hitos")
    if permission is None:
        return

    tecnico_comedor = Group.objects.filter(name="Tecnico Comedor").first()
    if tecnico_comedor:
        tecnico_comedor.permissions.add(permission)


def reconcile_acompanamiento_permissions(apps, schema_editor):
    revoke_generic_comedores_acompanamiento_access(apps, schema_editor)
    grant_hitos_change_to_tecnico_comedor(apps, schema_editor)


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0041_bootstrap_simepi_cdi_groups"),
    ]

    operations = [
        migrations.RunPython(
            reconcile_acompanamiento_permissions,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
