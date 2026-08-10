from django.db import migrations, models
import django.core.validators


def registrar_variables(apps, schema_editor):
    Variable = apps.get_model("admisiones", "VariableTemplateInformeTecnico")
    variables = (
        ("informe.criterio_seleccionado", "Criterio seleccionado", "Criterios"),
        ("informe.get_criterio_seleccionado_display", "Criterio seleccionado (descripción)", "Criterios"),
        ("informe.antecedentes_renovaciones", "Antecedentes de renovaciones", "Renovaciones"),
        ("informe.finalizacion_convenio_pnud_vigente", "Finalización de Convenio PNUD Vigente", "Convenio PNUD"),
        ("informe.acreditaciones_ultimo_convenio", "Acreditaciones realizadas último convenio", "Resoluciones de pago"),
        ("informe.monto_total_conveniado_informe", "Monto total conveniado al momento del informe", "Resoluciones de pago"),
        ("informe.monto_total_conveniado", "Monto total conveniado", "Resoluciones de pago"),
        ("informe.expediente_incorporacion", "Expediente de Incorporación", "Renovaciones"),
        ("informe.convenio_incorporacion", "Convenio de Incorporación", "Renovaciones"),
        ("informe.presentacion_avales", "Presentación de Avales", "Avales"),
    )
    for codigo, nombre, categoria in variables:
        Variable.objects.update_or_create(
            codigo=codigo,
            defaults={"nombre": nombre, "categoria": categoria, "activo": True},
        )


class Migration(migrations.Migration):
    dependencies = [("admisiones", "0075_alter_admision_legales_num_if")]

    operations = [
        migrations.AddField(model_name="informetecnico", name="criterio_seleccionado", field=models.CharField(blank=True, choices=[("A", "A - Coincidencia"), ("B", "B - Solicitud Menor"), ("C", "C - Solicitud Mayor")], max_length=1, null=True, verbose_name="Criterio seleccionado")),
        migrations.AddField(model_name="informetecnico", name="antecedentes_renovaciones", field=models.JSONField(blank=True, default=list)),
        migrations.AddField(model_name="informetecnico", name="finalizacion_convenio_pnud_vigente", field=models.DateField(blank=True, null=True, verbose_name="Finalización de Convenio PNUD Vigente")),
        migrations.AddField(model_name="informetecnico", name="acreditaciones_ultimo_convenio", field=models.PositiveIntegerField(blank=True, null=True, verbose_name="Acreditaciones realizadas último convenio")),
        migrations.AddField(model_name="informetecnico", name="monto_total_conveniado_informe", field=models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True, validators=[django.core.validators.MinValueValidator(0)], verbose_name="Monto total conveniado al momento del informe")),
        migrations.AddField(model_name="informetecnico", name="monto_total_conveniado", field=models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True, validators=[django.core.validators.MinValueValidator(0)], verbose_name="Monto total conveniado")),
        migrations.AddField(model_name="informetecnico", name="expediente_incorporacion", field=models.CharField(blank=True, max_length=255, null=True, verbose_name="Expediente de Incorporación")),
        migrations.AddField(model_name="informetecnico", name="convenio_incorporacion", field=models.CharField(blank=True, max_length=255, null=True, verbose_name="Convenio de Incorporación")),
        migrations.AddField(model_name="informetecnico", name="presentacion_avales", field=models.CharField(blank=True, max_length=255, null=True, verbose_name="Presentación de Avales")),
        migrations.RunPython(registrar_variables, migrations.RunPython.noop),
    ]
