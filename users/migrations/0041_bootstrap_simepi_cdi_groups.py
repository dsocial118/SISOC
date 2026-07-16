from django.db import migrations


GROUP_PERMISSION_MAP = {
    "SIMEPI - Administrador": (
        "auth.add_user",
        "auth.change_user",
        "auth.delete_user",
        "auth.view_user",
        "centrodeinfancia.add_centrodeinfancia",
        "centrodeinfancia.change_centrodeinfancia",
        "centrodeinfancia.delete_centrodeinfancia",
        "centrodeinfancia.view_centrodeinfancia",
        "centrodeinfancia.add_trabajador",
        "centrodeinfancia.change_trabajador",
        "centrodeinfancia.delete_trabajador",
        "centrodeinfancia.view_trabajador",
        "centrodeinfancia.add_nominacentroinfancia",
        "centrodeinfancia.change_nominacentroinfancia",
        "centrodeinfancia.delete_nominacentroinfancia",
        "centrodeinfancia.view_nominacentroinfancia",
        "centrodeinfancia.add_formulariocdi",
        "centrodeinfancia.change_formulariocdi",
        "centrodeinfancia.delete_formulariocdi",
        "centrodeinfancia.view_formulariocdi",
    ),
    "SIMEPI - Analista de datos": (
        "centrodeinfancia.add_centrodeinfancia",
        "centrodeinfancia.change_centrodeinfancia",
        "centrodeinfancia.delete_centrodeinfancia",
        "centrodeinfancia.view_centrodeinfancia",
        "centrodeinfancia.add_trabajador",
        "centrodeinfancia.change_trabajador",
        "centrodeinfancia.delete_trabajador",
        "centrodeinfancia.view_trabajador",
        "centrodeinfancia.add_nominacentroinfancia",
        "centrodeinfancia.change_nominacentroinfancia",
        "centrodeinfancia.delete_nominacentroinfancia",
        "centrodeinfancia.view_nominacentroinfancia",
        "centrodeinfancia.add_formulariocdi",
        "centrodeinfancia.change_formulariocdi",
        "centrodeinfancia.delete_formulariocdi",
        "centrodeinfancia.view_formulariocdi",
    ),
    "SIMEPI - Equipo Nacional": (
        "auth.add_user",
        "auth.change_user",
        "auth.view_user",
        "centrodeinfancia.view_centrodeinfancia",
        "centrodeinfancia.view_trabajador",
        "centrodeinfancia.view_nominacentroinfancia",
        "centrodeinfancia.view_formulariocdi",
    ),
    "SIMEPI - Auditoría": (
        "centrodeinfancia.view_centrodeinfancia",
        "centrodeinfancia.view_trabajador",
        "centrodeinfancia.view_nominacentroinfancia",
        "centrodeinfancia.view_formulariocdi",
    ),
    "SIMEPI - EGP": (
        "auth.add_user",
        "auth.change_user",
        "auth.view_user",
        "centrodeinfancia.add_centrodeinfancia",
        "centrodeinfancia.change_centrodeinfancia",
        "centrodeinfancia.delete_centrodeinfancia",
        "centrodeinfancia.view_centrodeinfancia",
        "centrodeinfancia.add_trabajador",
        "centrodeinfancia.change_trabajador",
        "centrodeinfancia.delete_trabajador",
        "centrodeinfancia.view_trabajador",
        "centrodeinfancia.add_nominacentroinfancia",
        "centrodeinfancia.change_nominacentroinfancia",
        "centrodeinfancia.delete_nominacentroinfancia",
        "centrodeinfancia.view_nominacentroinfancia",
        "centrodeinfancia.add_formulariocdi",
        "centrodeinfancia.change_formulariocdi",
        "centrodeinfancia.delete_formulariocdi",
        "centrodeinfancia.view_formulariocdi",
    ),
    "CDI - Trabajador": (
        "centrodeinfancia.view_centrodeinfancia",
        "centrodeinfancia.view_trabajador",
        "centrodeinfancia.view_nominacentroinfancia",
        "centrodeinfancia.view_formulariocdi",
    ),
    "CDI - Referente centro": (
        "auth.add_user",
        "auth.view_user",
        "centrodeinfancia.add_trabajador",
        "centrodeinfancia.change_trabajador",
        "centrodeinfancia.view_trabajador",
    ),
}


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


def bootstrap_simepi_cdi_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")

    for group_name, permission_codes in GROUP_PERMISSION_MAP.items():
        group, _ = Group.objects.get_or_create(name=group_name)
        permissions = []
        for code in permission_codes:
            permission = _resolve_permission(apps, code)
            if permission:
                permissions.append(permission)
        if permissions:
            group.permissions.add(*permissions)


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0040_userimportjobrow_created_user_credentials_sent_at"),
        ("centrodeinfancia", "0035_migrar_pueblo_originario_legacy"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.RunPython(
            bootstrap_simepi_cdi_groups,
            reverse_code=migrations.RunPython.noop,
        )
    ]
