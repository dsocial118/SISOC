from django.db import migrations, models


def backfill_estado_revision_manual(apps, schema_editor):
    Ciudadano = apps.get_model("ciudadanos", "Ciudadano")
    Ciudadano.objects.filter(requiere_revision_manual=True).update(
        estado_revision_manual="PENDIENTE"
    )
    Ciudadano.objects.filter(
        requiere_revision_manual=False,
        tipo_registro_identidad__in=["SIN_DNI", "DNI_NO_VALIDADO_RENAPER"],
    ).update(estado_revision_manual="APROBADA")


def revert_backfill_estado_revision_manual(apps, schema_editor):
    Ciudadano = apps.get_model("ciudadanos", "Ciudadano")
    Ciudadano.objects.all().update(estado_revision_manual="PENDIENTE")


class Migration(migrations.Migration):

    dependencies = [
        ("ciudadanos", "0028_merge_20260420_0000"),
    ]

    operations = [
        migrations.AddField(
            model_name="ciudadano",
            name="estado_revision_manual",
            field=models.CharField(
                choices=[
                    ("PENDIENTE", "Revisi\u00f3n pendiente"),
                    ("APROBADA", "Aprobado"),
                    ("DESCARTADA", "Descartado"),
                ],
                db_index=True,
                default="PENDIENTE",
                max_length=20,
            ),
        ),
        migrations.RunPython(
            backfill_estado_revision_manual,
            revert_backfill_estado_revision_manual,
        ),
    ]
