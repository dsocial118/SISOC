from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("pwa", "0017_sync_catalogo_actividades_pwa"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="catalogoactividadpwa",
            options={
                "ordering": ("categoria", "actividad", "id"),
                "permissions": [
                    (
                        "manage_catalogoactividadpwa",
                        "Puede gestionar actividades PNUD PWA",
                    ),
                ],
                "verbose_name": "Catalogo Actividad PWA",
                "verbose_name_plural": "Catalogo Actividades PWA",
            },
        ),
    ]
