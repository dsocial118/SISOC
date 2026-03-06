from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("centrodeinfancia", "0008_migrate_legacy_cdi_tables"),
    ]

    operations = [
        migrations.AddField(
            model_name="centrodeinfancia",
            name="numero",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
