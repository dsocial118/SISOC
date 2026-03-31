from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("organizaciones", "0008_alter_aval_managers_alter_firmante_managers_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="organizacion",
            name="sigla",
            field=models.CharField(blank=True, max_length=30, null=True, verbose_name="Sigla"),
        ),
    ]
