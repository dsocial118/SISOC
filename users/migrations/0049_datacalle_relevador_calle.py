# Escrita a mano siguiendo 0046_profile_es_territorial_comedor_and_more.
# Verificar con `makemigrations --check` al levantar el stack.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0008_programa_organismo_programa_descripcion"),
        ("users", "0048_merge_pwa_territorial_and_organizacion"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="es_relevador_calle",
            field=models.BooleanField(
                default=False,
                help_text="Marca al usuario como relevador de personas en situacion de calle en SISOC - Mobile (DataCalle). El alcance se define por provincia en RelevadorCalleProvincia.",
                verbose_name="Acceso SISOC - Mobile DataCalle",
            ),
        ),
        migrations.CreateModel(
            name="RelevadorCalleProvincia",
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
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="relevador_calle_provincias",
                        to="users.profile",
                    ),
                ),
                (
                    "provincia",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="core.provincia",
                    ),
                ),
            ],
            options={
                "verbose_name": "Provincia de relevador DataCalle",
                "verbose_name_plural": "Provincias de relevador DataCalle",
                "indexes": [
                    models.Index(
                        fields=["provincia"], name="users_relev_provinc_3cb09a_idx"
                    )
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("profile", "provincia"),
                        name="uniq_relevador_calle_provincia",
                    )
                ],
            },
        ),
    ]
