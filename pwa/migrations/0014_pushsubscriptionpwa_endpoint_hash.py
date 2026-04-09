import hashlib

from django.db import migrations, models


def populate_push_subscription_endpoint_hash(apps, schema_editor):
    PushSubscriptionPWA = apps.get_model("pwa", "PushSubscriptionPWA")

    for subscription in PushSubscriptionPWA.objects.all().iterator():
        endpoint = (subscription.endpoint or "").strip()
        subscription.endpoint = endpoint
        subscription.endpoint_hash = hashlib.sha256(
            endpoint.encode("utf-8")
        ).hexdigest()
        subscription.save(update_fields=["endpoint", "endpoint_hash"])


def noop_reverse(apps, schema_editor):
    """La reversión no requiere transformar datos."""


class Migration(migrations.Migration):
    dependencies = [
        ("pwa", "0013_pushsubscriptionpwa"),
    ]

    operations = [
        migrations.AddField(
            model_name="pushsubscriptionpwa",
            name="endpoint_hash",
            field=models.CharField(
                blank=True,
                editable=False,
                max_length=64,
                null=True,
            ),
        ),
        migrations.RunPython(
            populate_push_subscription_endpoint_hash,
            noop_reverse,
        ),
        migrations.AlterField(
            model_name="pushsubscriptionpwa",
            name="endpoint",
            field=models.URLField(max_length=500),
        ),
        migrations.AlterField(
            model_name="pushsubscriptionpwa",
            name="endpoint_hash",
            field=models.CharField(editable=False, max_length=64, unique=True),
        ),
    ]
