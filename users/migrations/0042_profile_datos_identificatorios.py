from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0041_bootstrap_simepi_cdi_groups"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="dni",
            field=models.CharField(blank=True, max_length=16),
        ),
        migrations.AddField(
            model_name="profile",
            name="cuil",
            field=models.CharField(blank=True, max_length=16),
        ),
        migrations.AddField(
            model_name="profile",
            name="tipo_usuario",
            field=models.CharField(
                blank=True,
                choices=[
                    ("interno", "Interno"),
                    ("provincial", "Provincial"),
                    ("externo", "Externo"),
                ],
                max_length=10,
                null=True,
            ),
        ),
    ]
