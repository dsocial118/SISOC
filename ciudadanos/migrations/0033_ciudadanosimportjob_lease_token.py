from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ciudadanos", "0032_ciudadano_documento_pasaporte_ciudadano_pais_emisor"),
    ]

    operations = [
        migrations.AddField(
            model_name="ciudadanosimportjob",
            name="lease_token",
            field=models.UUIDField(blank=True, editable=False, null=True),
        ),
    ]
