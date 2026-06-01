# pylint: disable=invalid-name

from django.db import migrations, models
import django.db.models.deletion


def populate_comision_modalidad(apps, schema_editor):
    ComisionCurso = apps.get_model("VAT", "ComisionCurso")
    db_alias = schema_editor.connection.alias
    for comision in (
        ComisionCurso.objects.using(db_alias).select_related("curso").iterator()
    ):
        if comision.modalidad_id or not comision.curso_id:
            continue
        comision.modalidad_id = comision.curso.modalidad_id
        comision.save(using=db_alias, update_fields=["modalidad"])


class Migration(migrations.Migration):

    dependencies = [
        ("VAT", "0046_curso_tipo"),
    ]

    operations = [
        migrations.AddField(
            model_name="comisioncurso",
            name="modalidad",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="comisiones_curso",
                to="VAT.modalidadcursada",
                verbose_name="Modalidad de Cursado",
            ),
        ),
        migrations.RunPython(populate_comision_modalidad, migrations.RunPython.noop),
    ]
