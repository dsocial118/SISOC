from django.db import migrations, models


STAGE_PERMISSIONS = {
    "manage_territorial_stage": "Puede gestionar la etapa Revisión Territorial",
    "manage_auditoria_review_stage": "Puede gestionar la etapa Revisión de Auditoría",
    "manage_auditoria_stage": "Puede gestionar la etapa Auditoría",
    "manage_regularizacion_stage": "Puede gestionar la etapa Regularización",
}


def crear_y_asignar_permisos(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    content_type = ContentType.objects.get(
        app_label="rendicioncuentasmensual",
        model="rendicioncuentamensual",
    )
    permisos = {}
    for codename, name in STAGE_PERMISSIONS.items():
        permiso, _ = Permission.objects.update_or_create(
            content_type=content_type,
            codename=codename,
            defaults={"name": name},
        )
        permisos[codename] = permiso

    asignaciones = {
        "Rendición Territorial": ("manage_territorial_stage",),
        "Rendición Auditoría": (
            "manage_auditoria_review_stage",
            "manage_auditoria_stage",
            "manage_regularizacion_stage",
        ),
        "Administrador Auditoría": tuple(STAGE_PERMISSIONS),
    }
    for nombre_grupo, codenames in asignaciones.items():
        grupo = Group.objects.filter(name=nombre_grupo).first()
        if grupo:
            grupo.permissions.add(*(permisos[codename] for codename in codenames))


class Migration(migrations.Migration):
    dependencies = [
        (
            "rendicioncuentasmensual",
            "0017_alter_rendicioncuentamensual_options_and_more",
        ),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="rendicioncuentamensual",
            options={
                "permissions": [
                    ("manage_mobile_rendicion", "Puede gestionar rendiciones mobile"),
                    ("edit_rendicion_data", "Puede editar datos de rendición"),
                    (
                        "manage_territorial_stage",
                        "Puede gestionar la etapa Revisión Territorial",
                    ),
                    (
                        "manage_auditoria_review_stage",
                        "Puede gestionar la etapa Revisión de Auditoría",
                    ),
                    (
                        "manage_auditoria_stage",
                        "Puede gestionar la etapa Auditoría",
                    ),
                    (
                        "manage_regularizacion_stage",
                        "Puede gestionar la etapa Regularización",
                    ),
                ],
                "verbose_name": "Rendición de Cuenta Mensual",
                "verbose_name_plural": "Rendiciones de Cuenta Mensuales",
            },
        ),
        migrations.RunPython(crear_y_asignar_permisos, migrations.RunPython.noop),
    ]
