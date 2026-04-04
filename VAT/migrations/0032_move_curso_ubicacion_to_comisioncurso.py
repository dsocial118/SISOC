from django.db import migrations, models
import django.db.models.deletion


def copy_curso_ubicacion_to_comisioncurso(apps, schema_editor):
    ComisionCurso = apps.get_model("VAT", "ComisionCurso")

    for comision in ComisionCurso.objects.select_related("curso").all().iterator():
        if comision.curso_id and comision.curso.ubicacion_id:
            comision.ubicacion_id = comision.curso.ubicacion_id
            comision.save(update_fields=["ubicacion"])


class Migration(migrations.Migration):

    dependencies = [
        ("VAT", "0031_remove_curso_programa"),
    ]

    operations = [
        migrations.AddField(
            model_name="comisioncurso",
            name="ubicacion",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="comisiones_curso",
                to="VAT.institucionubicacion",
                verbose_name="Ubicación",
            ),
        ),
        migrations.RunPython(
            copy_curso_ubicacion_to_comisioncurso,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="comisioncurso",
            name="ubicacion",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="comisiones_curso",
                to="VAT.institucionubicacion",
                verbose_name="Ubicación",
            ),
        ),
        migrations.RemoveField(
            model_name="curso",
            name="ubicacion",
        ),
    ]