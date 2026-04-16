from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("rendicioncuentasmensual", "0004_rendicioncuentamensual_datos_mobile"),
    ]

    operations = [
        migrations.AddField(
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
                    ("otros", "Otros"),
                ],
                default="comprobantes",
                max_length=40,
                verbose_name="Categoría",
            ),
        ),
        migrations.AddField(
            model_name="documentacionadjunta",
            name="estado",
            field=models.CharField(
                choices=[
                    ("presentado", "Presentado"),
                    ("subsanar", "A Subsanar"),
                    ("validado", "Validado"),
                ],
                default="presentado",
                max_length=20,
                verbose_name="Estado del documento",
            ),
        ),
        migrations.AddField(
            model_name="documentacionadjunta",
            name="observaciones",
            field=models.TextField(
                blank=True,
                null=True,
                verbose_name="Observaciones",
            ),
        ),
    ]
