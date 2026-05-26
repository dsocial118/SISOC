# Generated manually 2026-05-26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "rendicioncuentasmensual",
            "0012_alter_rendicioncuentamensual_options_and_more",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="documentacionadjunta",
            name="categoria",
            field=models.CharField(
                choices=[
                    ("formulario_i", "Formulario I - Certificación de Cuenta Bancaria"),
                    ("formulario_ii", "Formulario II - Resumen"),
                    (
                        "formulario_iii",
                        "Formulario III - Desagregado por Facturas Prestación Alimentaria",
                    ),
                    (
                        "formulario_iii_alimentario",
                        "Formulario III - Desagregado por Facturas Prestación Alimentaria",
                    ),
                    (
                        "formulario_iii_siph",
                        "Formulario III - Desagregado por Facturas SIPH",
                    ),
                    ("formulario_iv", "Formulario IV - Recibo de Fondos"),
                    (
                        "formulario_v",
                        "Formulario V - Certificación de Prestaciones Alimentarias",
                    ),
                    (
                        "formulario_v_alimentario",
                        "Formulario V - Certificación de Prestaciones Alimentarias",
                    ),
                    ("formulario_v_siph", "Formulario V - Certificación de SIPH"),
                    ("formulario_vi", "Formulario VI - Planilla de Pagos"),
                    ("extracto_bancario", "Extracto Bancario"),
                    ("comprobantes", "Comprobante/s"),
                    ("planilla_seguros", "Planilla de Seguros"),
                    ("otros", "Documentación Adicional"),
                ],
                default="comprobantes",
                max_length=40,
                verbose_name="Categoría",
            ),
        ),
    ]
