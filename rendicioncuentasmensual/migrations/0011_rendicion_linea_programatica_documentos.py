from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("rendicioncuentasmensual", "0010_documentacionadjunta_documento_subsanado"),
    ]

    operations = [
        migrations.AddField(
            model_name="rendicioncuentamensual",
            name="linea_programatica",
            field=models.CharField(
                choices=[
                    ("secos", "Abordaje Comunitario - Linea Secos"),
                    ("tradicional", "Abordaje Comunitario - Linea Tradicional"),
                ],
                default="tradicional",
                max_length=20,
                verbose_name="Linea Programatica",
            ),
        ),
        migrations.AlterField(
            model_name="documentacionadjunta",
            name="categoria",
            field=models.CharField(
                choices=[
                    ("formulario_i", "Formulario I"),
                    ("formulario_ii", "Formulario II"),
                    ("formulario_iii", "Formulario III"),
                    ("formulario_iii_alimentario", "Formulario III Alimentario"),
                    ("formulario_iii_siph", "Formulario III SIPH"),
                    ("formulario_iv", "Formulario IV"),
                    ("formulario_v", "Formulario V"),
                    ("formulario_v_alimentario", "Formulario V Alimentario"),
                    ("formulario_v_siph", "Formulario V SIPH"),
                    ("formulario_vi", "Formulario VI"),
                    ("extracto_bancario", "Extracto Bancario"),
                    ("comprobantes", "Comprobante/s"),
                    ("planilla_seguros", "Planilla de Seguros"),
                    ("otros", "Documentacion Adicional"),
                ],
                default="comprobantes",
                max_length=40,
                verbose_name="Categoria",
            ),
        ),
    ]
