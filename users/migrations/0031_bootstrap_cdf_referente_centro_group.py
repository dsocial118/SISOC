from django.db import migrations

GROUP_NAME = "CDF - Referente centro"

PERMISSION_CODES = (
    "centrodefamilia.view_centro",
    "centrodefamilia.change_centro",
)


def _resolve_permission(apps, code):
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")
    try:
        app_label, codename = code.split(".", 1)
    except ValueError:
        return None

    permission = Permission.objects.filter(
        content_type__app_label=app_label,
        codename=codename,
    ).first()
    if permission:
        return permission

    if app_label == "auth" and codename.startswith("role_"):
        group_ct, _ = ContentType.objects.get_or_create(app_label="auth", model="group")
        name = codename[len("role_") :].replace("_", " ").strip().title()
        permission, _ = Permission.objects.get_or_create(
            content_type=group_ct,
            codename=codename,
            defaults={"name": name or codename},
        )
        return permission

    return None


def bootstrap_cdf_referente_centro_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    group, _ = Group.objects.get_or_create(name=GROUP_NAME)

    permissions = []
    for code in PERMISSION_CODES:
        permission = _resolve_permission(apps, code)
        if permission:
            permissions.append(permission)
    if permissions:
        group.permissions.add(*permissions)


class Migration(migrations.Migration):
    dependencies = [
        (
            "users",
            "0030_profile_territorial_scope",
        ),
        ("centrodefamilia", "0014_accesocdf"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.RunPython(
            bootstrap_cdf_referente_centro_group,
            reverse_code=migrations.RunPython.noop,
        )
    ]
