from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("pwa", "0019_actividad_responsable_vigencia"),
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
                    (
                        "manage_prestaciones_mensuales_pwa",
                        "Puede gestionar conformidad de prestaciones mensuales PWA",
                    ),
                    (
                        "manage_nomina_pwa",
                        "Puede gestionar nomina PWA",
                    ),
                    (
                        "manage_colaboradores_pwa",
                        "Puede gestionar colaboradores PWA",
                    ),
                ],
                "verbose_name": "Catalogo Actividad PWA",
                "verbose_name_plural": "Catalogo Actividades PWA",
            },
        ),
    ]
