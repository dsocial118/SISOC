from django.conf import settings
from django.db import migrations, models


def copy_legacy_referente_to_referentes(apps, schema_editor):
    Centro = apps.get_model("VAT", "Centro")
    through_model = Centro.referentes.through
    rows = [
        through_model(centro_id=centro.pk, user_id=centro.referente_id)
        for centro in Centro.objects.exclude(referente_id__isnull=True).iterator()
    ]
    if rows:
        through_model.objects.bulk_create(rows, ignore_conflicts=True)


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("VAT", "0044_centro_listado_indexes"),
    ]

    operations = [
        migrations.AddField(
            model_name="centro",
            name="referentes",
            field=models.ManyToManyField(
                blank=True,
                limit_choices_to={"groups__name": "CFP"},
                related_name="vat_centros_referente",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="centro",
            name="revisores",
            field=models.ManyToManyField(
                blank=True,
                limit_choices_to={"groups__name": "CFPRevisor"},
                related_name="vat_centros_revisor",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(
            copy_legacy_referente_to_referentes,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
