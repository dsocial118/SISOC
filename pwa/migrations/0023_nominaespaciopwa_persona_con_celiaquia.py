from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("pwa", "0022_pwa_usuarios_permission"),
    ]

    operations = [
        migrations.AddField(
            model_name="nominaespaciopwa",
            name="persona_con_celiaquia",
            field=models.BooleanField(default=False),
        ),
    ]
