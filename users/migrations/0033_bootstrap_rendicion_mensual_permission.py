from django.db import migrations


GROUPS_WITH_RENDICION_ACCESS = [
    "Tecnico Comedor",
    "Area Contable",
    "Coordinador Equipo Tecnico",
    "Coordinador general",
    "Coordinador Gestion",
]


def assign_rendicion_mensual_permission(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    permission = Permission.objects.filter(
        content_type__app_label="rendicioncuentasmensual",
        codename="view_rendicioncuentamensual",
    ).first()

    if not permission:
        return

    for group_name in GROUPS_WITH_RENDICION_ACCESS:
        group = Group.objects.filter(name=group_name).first()
        if group:
            group.permissions.add(permission)


def revoke_rendicion_mensual_permission(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    permission = Permission.objects.filter(
        content_type__app_label="rendicioncuentasmensual",
        codename="view_rendicioncuentamensual",
    ).first()

    if not permission:
        return

    for group_name in GROUPS_WITH_RENDICION_ACCESS:
        group = Group.objects.filter(name=group_name).first()
        if group:
            group.permissions.remove(permission)


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0032_merge_cdf_referente_profile_source"),
    ]

    operations = [
        migrations.RunPython(
            assign_rendicion_mensual_permission, revoke_rendicion_mensual_permission
        ),
    ]
