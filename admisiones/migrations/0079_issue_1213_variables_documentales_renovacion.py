from django.db import migrations, models


VARIABLES_DOCUMENTALES = (
    (
        "informe.resolucion_o_disposicion_incorporacion",
        "Resolución o disposición de incorporación",
        "Renovaciones - antecedentes",
    ),
    (
        "informe.renovaciones_anteriores_detalladas",
        "Renovaciones anteriores detalladas",
        "Renovaciones - antecedentes",
    ),
    (
        "informe.referencia_itcomp_modificacion_prestaciones",
        "Referencia IF IT Complementario",
        "Renovaciones - Informe Complementario",
    ),
    (
        "informe.expediente_pago_en_curso",
        "Expediente de pago en curso",
        "Renovaciones - antecedentes",
    ),
    (
        "informe.expediente_ultimo_convenio",
        "Expediente del último convenio",
        "Renovaciones - antecedentes",
    ),
    *(
        (
            f"informe.total_semanal_ultimo_convenio_{comida}s",
            f"Total semanal último convenio - {comida.capitalize()}",
            "Renovaciones - prestaciones",
        )
        for comida in ("desayuno", "almuerzo", "merienda", "cena")
    ),
    *(
        (
            f"informe.total_semanal_actual_{comida}s",
            f"Total semanal actual - {comida.capitalize()}",
            "Renovaciones - prestaciones",
        )
        for comida in ("desayuno", "almuerzo", "merienda", "cena")
    ),
)


def registrar_variables(apps, schema_editor):
    Variable = apps.get_model("admisiones", "VariableTemplateInformeTecnico")
    for orden, (codigo, nombre, categoria) in enumerate(
        VARIABLES_DOCUMENTALES, start=1
    ):
        Variable.objects.update_or_create(
            codigo=codigo,
            defaults={
                "nombre": nombre,
                "categoria": categoria,
                "orden": orden,
                "activo": True,
            },
        )


def eliminar_variables(apps, schema_editor):
    Variable = apps.get_model("admisiones", "VariableTemplateInformeTecnico")
    Variable.objects.filter(
        codigo__in=[codigo for codigo, _, _ in VARIABLES_DOCUMENTALES]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [("admisiones", "0078_issue_2234_campo_informe_complementario")]

    operations = [
        migrations.AddField(
            model_name="informetecnico",
            name="if_it_complementario",
            field=models.CharField(
                blank=True,
                max_length=255,
                null=True,
                verbose_name="IF IT Complementario",
            ),
        ),
        migrations.RunPython(registrar_variables, eliminar_variables),
    ]
