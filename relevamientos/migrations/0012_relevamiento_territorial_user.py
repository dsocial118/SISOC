from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("relevamientos", "0011_alter_menuseguimiento_mejora_alimentacion_ofrecida"),
    ]

    operations = [
        migrations.AddField(
            model_name="relevamiento",
            name="territorial_user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="relevamientos_asignados",
                to=settings.AUTH_USER_MODEL,
                help_text=(
                    "Territorial (usuario SISOC) asignado al relevamiento. Único y "
                    "reasignable; reemplaza la asignación por uid de AppSheet."
                ),
            ),
        ),
    ]
