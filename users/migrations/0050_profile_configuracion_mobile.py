from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("users", "0049_coordinadorequipotecnico_pwa")]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="configuracion_mobile",
            field=models.JSONField(
                default=dict,
                blank=True,
                editable=False,
                help_text="Selecciones del formulario mobile; no otorga permisos ni acceso.",
            ),
        ),
    ]
