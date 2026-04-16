from django.db import migrations


def create_mobile_rendicion_permission(apps, schema_editor):
    permission_model = apps.get_model("auth", "Permission")
    content_type_model = apps.get_model("contenttypes", "ContentType")

    content_type, _ = content_type_model.objects.get_or_create(
        app_label="rendicioncuentasmensual",
        model="rendicioncuentamensual",
    )
    permission_model.objects.get_or_create(
        content_type=content_type,
        codename="manage_mobile_rendicion",
        defaults={"name": "Puede gestionar rendiciones mobile"},
    )


def noop_reverse(apps, schema_editor):
    """No elimina permisos en rollback."""


class Migration(migrations.Migration):
    dependencies = [
        ("rendicioncuentasmensual", "0005_documentacionadjunta_categorias_estado"),
    ]

    operations = [
        migrations.RunPython(create_mobile_rendicion_permission, noop_reverse),
    ]
