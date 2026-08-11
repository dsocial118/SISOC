from django.db import migrations, models


def completar_renovaciones_existentes(apps, schema_editor):
    Admision = apps.get_model("admisiones", "Admision")
    Plantilla = apps.get_model("admisiones", "PlantillaInformeTecnico")
    Publicacion = apps.get_model("admisiones", "PlantillaInformeTecnicoPublicacion")

    Admision.objects.filter(tipo="renovacion").update(
        informe_complementario_modifica_prestaciones="no"
    )
    plantillas = Plantilla.objects.filter(tipo_admision="renovacion")
    plantillas.update(informe_complementario_modifica_prestaciones="no")
    for plantilla in plantillas.iterator():
        publicacion = Publicacion.objects.filter(plantilla_id=plantilla.id).first()
        if publicacion:
            publicacion.clave_condiciones = (
                f"{publicacion.clave_condiciones}|informe_complementario:no"
            )
            publicacion.save(update_fields=["clave_condiciones"])


class Migration(migrations.Migration):
    dependencies = [("admisiones", "0076_issue_2233_campos_informe_tecnico")]

    operations = [
        migrations.AddField(
            model_name="admision",
            name="informe_complementario_modifica_prestaciones",
            field=models.CharField(
                blank=True,
                choices=[("si", "Sí"), ("no", "No")],
                max_length=2,
                null=True,
                verbose_name="¿Se realizó Informe Complementario para modificar prestaciones?",
            ),
        ),
        migrations.AddField(
            model_name="plantillainformetecnico",
            name="informe_complementario_modifica_prestaciones",
            field=models.CharField(
                blank=True,
                choices=[("si", "Sí"), ("no", "No")],
                max_length=2,
                null=True,
            ),
        ),
        migrations.RunPython(
            completar_renovaciones_existentes, migrations.RunPython.noop
        ),
    ]
