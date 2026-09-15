"""Crea el permiso de reportes CDI y lo asigna a los roles SIMEPI (issue #2508).

El módulo de reportes no reutiliza `auth.role_exportar_a_csv` porque ese permiso
es global: dárselo a los roles SIMEPI también habilitaría exportar comedores,
usuarios y el resto de los listados del sistema.
"""

from django.db import migrations


PERMISSION_CODENAME = "role_reportes_cdi"
PERMISSION_NAME = "Reportes CDI"

GRUPOS = (
    "SIMEPI - Administrador",
    "SIMEPI - Analista de datos",
    "SIMEPI - Equipo Nacional",
    "SIMEPI - Auditoría",
    "SIMEPI - EGP",
)


def _permiso(apps):
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")
    group_ct, _ = ContentType.objects.get_or_create(app_label="auth", model="group")
    permiso, _ = Permission.objects.get_or_create(
        content_type=group_ct,
        codename=PERMISSION_CODENAME,
        defaults={"name": PERMISSION_NAME},
    )
    return permiso


def asignar(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    permiso = _permiso(apps)
    for nombre in GRUPOS:
        grupo = Group.objects.filter(name=nombre).first()
        if grupo:
            grupo.permissions.add(permiso)


def desasignar(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    permiso = Permission.objects.filter(codename=PERMISSION_CODENAME).first()
    if not permiso:
        return
    for nombre in GRUPOS:
        grupo = Group.objects.filter(name=nombre).first()
        if grupo:
            grupo.permissions.remove(permiso)


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0051_merge_mobile_configuration_and_datacalle"),
        ("auth", "0012_alter_user_first_name_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.RunPython(asignar, desasignar),
    ]
