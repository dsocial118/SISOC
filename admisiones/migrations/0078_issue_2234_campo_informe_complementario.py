from django.db import migrations, models


def registrar_variable(apps, schema_editor):
    Variable = apps.get_model("admisiones", "VariableTemplateInformeTecnico")
    Variable.objects.update_or_create(
        codigo="informe.informe_tecnico_complementario_modificacion_prestaciones",
        defaults={
            "nombre": "Informe Técnico Complementario - Modificación de Prestaciones",
            "categoria": "Renovaciones",
            "activo": True,
        },
    )


def eliminar_variable(apps, schema_editor):
    Variable = apps.get_model("admisiones", "VariableTemplateInformeTecnico")
    Variable.objects.filter(
        codigo="informe.informe_tecnico_complementario_modificacion_prestaciones"
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("admisiones", "0077_issue_2234_informe_complementario_prestaciones")
    ]

    operations = [
        migrations.AddField(
            model_name="informetecnico",
            name="informe_tecnico_complementario_modificacion_prestaciones",
            field=models.CharField(
                blank=True,
                max_length=255,
                null=True,
                verbose_name="Informe Técnico Complementario - Modificación de Prestaciones",
            ),
        ),
        migrations.RunPython(registrar_variable, eliminar_variable),
    ]
