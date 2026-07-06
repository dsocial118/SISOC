from django.db import migrations


# Reconciliacion exacta de los grupos VAT administrativos. A diferencia de
# `create_groups` (aditivo), esta migracion deja cada grupo con EXACTAMENTE
# estos permisos, removiendo los sobrantes en entornos ya existentes.
#
# Debe mantenerse en sincronia con `users/bootstrap/groups_seed.py`. Se deja el
# listado hardcodeado (self-contained) para que la migracion sea estable ante
# futuros cambios del seed.
GROUP_PERMISSION_MAP = {
    # operador CFP: se conserva el marcador de rol `role_referentecentrovat`,
    # necesario para que access_scope reconozca al usuario como referente.
    "CFP": (
        "auth.role_referentecentrovat",
        "VAT.view_centro",
        "VAT.add_curso",
        "VAT.change_curso",
        "VAT.delete_curso",
        "VAT.view_comisioncurso",
        "VAT.add_comisioncurso",
        "VAT.change_comisioncurso",
        "VAT.delete_comisioncurso",
        "VAT.view_comisionhorario",
        "VAT.add_comisionhorario",
        "VAT.change_comisionhorario",
        "VAT.delete_comisionhorario",
        "VAT.view_inscripcion",
        "VAT.add_inscripcion",
        "VAT.change_inscripcion",
        "VAT.add_asistenciasesion",
        "VAT.change_asistenciasesion",
    ),
    "INET_PROVINCIA": (
        "auth.role_inet_provincia",
        "VAT.view_centro",
        "VAT.add_centro",
        "VAT.change_centro",
        "VAT.view_planversioncurricular",
        "VAT.add_planversioncurricular",
        "VAT.view_comision",
        "VAT.view_comisioncurso",
    ),
    "INET Admin Visualizador": (
        "VAT.view_centro",
        "VAT.view_comision",
        "VAT.view_comisioncurso",
        "VAT.view_comisionhorario",
        "VAT.view_inscripcion",
        "VAT.view_inscripcionoferta",
        "VAT.view_planversioncurricular",
    ),
    "INET Admin General": (
        "auth.role_vat_sse",
        "auth.role_admin_inet_general",
        "VAT.view_centro",
        "VAT.add_centro",
        "VAT.change_centro",
        "VAT.add_curso",
        "VAT.change_curso",
        "VAT.delete_curso",
        "VAT.view_comision",
        "VAT.change_comision",
        "VAT.view_comisioncurso",
        "VAT.add_comisioncurso",
        "VAT.change_comisioncurso",
        "VAT.delete_comisioncurso",
        "VAT.view_comisionhorario",
        "VAT.add_comisionhorario",
        "VAT.change_comisionhorario",
        "VAT.delete_comisionhorario",
        "VAT.view_inscripcion",
        "VAT.add_inscripcion",
        "VAT.change_inscripcion",
        "VAT.add_asistenciasesion",
        "VAT.change_asistenciasesion",
        "VAT.view_planversioncurricular",
        "VAT.add_planversioncurricular",
    ),
}


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
        group_ct, _ = ContentType.objects.get_or_create(
            app_label="auth", model="group"
        )
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

    for group_name, permission_codes in GROUP_PERMISSION_MAP.items():
        group, _ = Group.objects.get_or_create(name=group_name)
        permissions = []
        for code in permission_codes:
            permission = _resolve_permission(apps, code)
            if permission:
                permissions.append(permission)
        # `.set()` deja el grupo con exactamente estos permisos (quita sobrantes).
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
