from django.db import migrations

GROUP_NAME = "CDI - Referente centro"

PERMISSION_CODES = (
    "auth.role_centro_de_infancia_editar",
    "centrodeinfancia.change_centrodeinfancia",
    "auth.role_centro_de_infancia_formulario_borrar",
    "centrodeinfancia.delete_formulariocdi",
    "auth.role_centro_de_infancia_formulario_crear",
    "centrodeinfancia.add_formulariocdi",
    "auth.role_centro_de_infancia_formulario_editar",
    "centrodeinfancia.change_formulariocdi",
    "auth.role_centro_de_infancia_formulario_ver",
    "centrodeinfancia.view_formulariocdi",
    "auth.role_centro_de_infancia_intervencion_borrar",
    "centrodeinfancia.delete_intervencioncentroinfancia",
    "auth.role_centro_de_infancia_intervencion_crear",
    "centrodeinfancia.add_intervencioncentroinfancia",
    "auth.role_centro_de_infancia_intervencion_editar",
    "centrodeinfancia.change_intervencioncentroinfancia",
    "auth.role_centro_de_infancia_listar",
    "centrodeinfancia.view_centrodeinfancia",
    "auth.role_centro_de_infancia_nomina_borrar",
    "centrodeinfancia.delete_nominacentroinfancia",
    "auth.role_centro_de_infancia_nomina_crear",
    "centrodeinfancia.add_nominacentroinfancia",
    "auth.role_centro_de_infancia_nomina_editar",
    "centrodeinfancia.change_nominacentroinfancia",
    "auth.role_centro_de_infancia_nomina_ver",
    "centrodeinfancia.view_nominacentroinfancia",
    "auth.role_centro_de_infancia_ver",
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


def bootstrap_cdi_referente_centro_group(apps, schema_editor):
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
            "0028_rename_users_bulk_status_dfc1d3_idx_users_bulkc_status_7d2f67_idx_and_more",
        ),
        ("centrodeinfancia", "0029_accesocdi_accesocdi_uniq_acceso_cdi_user_centro"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.RunPython(
            bootstrap_cdi_referente_centro_group,
            reverse_code=migrations.RunPython.noop,
        )
    ]
