from django.db import migrations


GROUP_PERMISSION_MAP = {
    "Centro de Infancia Formulario Ver": ("centrodeinfancia.view_formulariocdi",),
    "Centro de Infancia Formulario Crear": ("centrodeinfancia.add_formulariocdi",),
    "Centro de Infancia Formulario Editar": ("centrodeinfancia.change_formulariocdi",),
    "Centro de Infancia Formulario Borrar": ("centrodeinfancia.delete_formulariocdi",),
}


def bootstrap_formulario_cdi_permissions(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    for group_name, permission_codes in GROUP_PERMISSION_MAP.items():
        group, _created = Group.objects.get_or_create(name=group_name)
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
        ("centrodeinfancia", "0010_centrodeinfancia_cdi_code_formulariocdi_and_more"),
        ("users", "0015_assign_bootstrap_group_permissions"),
    ]

    operations = [
        migrations.RunPython(
            bootstrap_formulario_cdi_permissions,
            reverse_code=migrations.RunPython.noop,
        )
    ]
