from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("rendicioncuentasmensual", "0007_alter_rendicioncuentamensual_options_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="rendicioncuentamensual",
            name="usuario_creador",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.SET_NULL,
                related_name="rendiciones_cuentas_mensuales_creadas",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Usuario creador",
            ),
        ),
    ]
