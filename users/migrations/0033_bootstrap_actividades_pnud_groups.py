from django.db import migrations


GROUP_PERMISSION_MAP = {
    "Actividades PNUD Ver": ("pwa.view_catalogoactividadpwa",),
    "Actividades PNUD Gestionar": (
        "pwa.view_catalogoactividadpwa",
        "pwa.manage_catalogoactividadpwa",
    ),
}


def bootstrap_actividades_pnud_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    for group_name, permission_codes in GROUP_PERMISSION_MAP.items():
        group, _ = Group.objects.get_or_create(name=group_name)
        permissions = []
        for code in permission_codes:
            app_label, codename = code.split(".", 1)
            permission = Permission.objects.filter(
                content_type__app_label=app_label,
                codename=codename,
            ).first()
            if permission:
                permissions.append(permission)
        if permissions:
            group.permissions.add(*permissions)


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0032_merge_cdf_referente_profile_source"),
        ("pwa", "0018_catalogoactividadpwa_manage_permission"),
    ]

    operations = [
        migrations.RunPython(
            bootstrap_actividades_pnud_groups,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
