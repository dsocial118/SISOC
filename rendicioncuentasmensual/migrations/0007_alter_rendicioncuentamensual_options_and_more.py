from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("rendicioncuentasmensual", "0006_bootstrap_mobile_permission"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="rendicioncuentamensual",
            options={
                "permissions": [
                    ("manage_mobile_rendicion", "Puede gestionar rendiciones mobile")
                ],
                "verbose_name": "Rendición de Cuenta Mensual",
                "verbose_name_plural": "Rendiciones de Cuenta Mensuales",
            },
        ),
        migrations.AlterField(
            model_name="documentacionadjunta",
            name="categoria",
            field=models.CharField(
                choices=[
                    ("formulario_ii", "Formulario II"),
                    ("formulario_iii", "Formulario III"),
                    ("formulario_iv", "Formulario IV"),
                    ("formulario_v", "Formulario V"),
                    ("formulario_vi", "Formulario VI"),
                    ("extracto_bancario", "Extracto Bancario"),
                    ("comprobantes", "Comprobante/s"),
                    ("planilla_seguros", "Planilla de Seguros"),
                    ("otros", "Documentación Extra"),
                ],
                default="comprobantes",
                max_length=40,
                verbose_name="Categoría",
            ),
        ),
    ]
