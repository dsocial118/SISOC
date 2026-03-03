from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("centrodeinfancia", "0006_alter_observacioncentroinfancia_managers_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="centrodeinfancia",
            name="apellido_referente",
            field=models.CharField(max_length=255, blank=True, null=True),
        ),
    ]
