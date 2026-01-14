from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_nacionalidad"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="FiltroFavorito",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("seccion", models.CharField(max_length=100)),
                ("nombre", models.CharField(max_length=120)),
                ("filtros", models.JSONField(default=dict)),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True)),
                (
                    "usuario",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="filtros_favoritos",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["fecha_creacion"],
            },
        ),
        migrations.AddConstraint(
            model_name="filtrofavorito",
            constraint=models.UniqueConstraint(
                fields=("usuario", "seccion", "nombre"),
                name="unico_filtro_favorito_usuario_seccion_nombre",
            ),
        ),
    ]
