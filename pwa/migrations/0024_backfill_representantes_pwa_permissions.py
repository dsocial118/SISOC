from django.db import migrations


PWA_PERMISSION_CODES = (
    ("pwa", "manage_colaboradores_pwa"),
    ("pwa", "manage_usuarios_pwa"),
    ("pwa", "manage_nomina_pwa"),
    ("pwa", "manage_prestaciones_mensuales_pwa"),
)


def grant_permissions_to_existing_representantes(apps, schema_editor):
    User = apps.get_model("auth", "User")
    Permission = apps.get_model("auth", "Permission")
    AccesoComedorPWA = apps.get_model("users", "AccesoComedorPWA")
    UserPermission = User.user_permissions.through

    permissions = list(
        Permission.objects.filter(
            content_type__app_label__in={
                app_label for app_label, _ in PWA_PERMISSION_CODES
            },
            codename__in={codename for _, codename in PWA_PERMISSION_CODES},
        )
    )
    representante_user_ids = (
        AccesoComedorPWA.objects.filter(
            activo=True,
            rol="representante",
        )
        .values_list("user_id", flat=True)
        .distinct()
    )
    for user_id in representante_user_ids.iterator():
        through_rows = [
            UserPermission(user_id=user_id, permission_id=permission.id)
            for permission in permissions
        ]
        UserPermission.objects.bulk_create(
            through_rows,
            ignore_conflicts=True,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("pwa", "0023_nominaespaciopwa_persona_con_celiaquia"),
        ("users", "0037_userimportjob_is_pwa_import"),
    ]

    operations = [
        migrations.RunPython(
            grant_permissions_to_existing_representantes,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
