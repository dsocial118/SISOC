from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("users", "0052_bootstrap_reportes_cdi_permission")]

    operations = [
        migrations.AddField(
            model_name="userimportjob",
            name="lease_token",
            field=models.UUIDField(blank=True, editable=False, null=True),
        ),
    ]
