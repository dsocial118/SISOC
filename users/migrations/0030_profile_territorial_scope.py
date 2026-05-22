from django.db import migrations, models
import django.db.models.deletion


def migrate_legacy_profile_provincias(apps, schema_editor):
    Profile = apps.get_model("users", "Profile")
    ProfileTerritorialScope = apps.get_model("users", "ProfileTerritorialScope")

    profiles = Profile.objects.filter(
        es_usuario_provincial=True,
        provincia_id__isnull=False,
    ).only("id", "provincia_id")
    for profile in profiles.iterator():
        scope_key = f"p{profile.provincia_id}:m0:l0"
        ProfileTerritorialScope.objects.get_or_create(
            profile_id=profile.id,
            scope_key=scope_key,
            defaults={"provincia_id": profile.provincia_id},
        )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0008_programa_organismo_programa_descripcion"),
        ("users", "0029_bootstrap_cdi_referente_centro_group"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProfileTerritorialScope",
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
                    "scope_key",
                    models.CharField(db_index=True, editable=False, max_length=64),
                ),
                (
                    "localidad",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="core.localidad",
                    ),
                ),
                (
                    "municipio",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="core.municipio",
                    ),
                ),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="territorial_scopes",
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
                "verbose_name": "Alcance territorial de perfil",
                "verbose_name_plural": "Alcances territoriales de perfil",
            },
        ),
        migrations.AddConstraint(
            model_name="profileterritorialscope",
            constraint=models.CheckConstraint(
                check=(
                    models.Q(("localidad__isnull", True))
                    | models.Q(("municipio__isnull", False))
                ),
                name="profile_scope_localidad_requires_municipio",
            ),
        ),
        migrations.AddConstraint(
            model_name="profileterritorialscope",
            constraint=models.UniqueConstraint(
                fields=("profile", "scope_key"),
                name="uniq_profile_scope_key",
            ),
        ),
        migrations.AddIndex(
            model_name="profileterritorialscope",
            index=models.Index(
                fields=["profile", "provincia"],
                name="users_profi_profile_4be6f7_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="profileterritorialscope",
            index=models.Index(
                fields=["profile", "provincia", "municipio"],
                name="users_profi_profile_26d7f4_idx",
            ),
        ),
        migrations.RunPython(
            migrate_legacy_profile_provincias,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
