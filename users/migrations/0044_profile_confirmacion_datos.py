from django.db import migrations, models


def marcar_perfiles_existentes(apps, schema_editor):
    """Fuerza la confirmación de datos a los usuarios previos al despliegue.

    Los perfiles creados después de esta migración quedan con el default
    ``False``, así que los usuarios nuevos no ven el flujo obligatorio.

    Hay usuarios históricos sin ``Profile`` (el perfil se crea por signal y
    algunas altas antiguas quedaron sin él). Se les crea el perfil vacío para
    que el middleware pueda exigirles la confirmación en lugar de saltearlos.
    """

    User = apps.get_model("auth", "User")
    Profile = apps.get_model("users", "Profile")

    perfiles_faltantes = [
        Profile(user_id=user_id, needs_profile_confirmation=True)
        for user_id in User.objects.filter(
            is_active=True, profile__isnull=True
        ).values_list("id", flat=True)
    ]
    if perfiles_faltantes:
        Profile.objects.bulk_create(perfiles_faltantes, batch_size=500)

    Profile.objects.filter(user__is_active=True).update(
        needs_profile_confirmation=True
    )


def desmarcar_perfiles(apps, schema_editor):
    Profile = apps.get_model("users", "Profile")
    Profile.objects.update(needs_profile_confirmation=False)


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0043_merge_issue_2225_profile_datos_identificatorios"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="needs_profile_confirmation",
            field=models.BooleanField(
                default=False,
                help_text=(
                    "Obliga al usuario a confirmar o corregir sus datos "
                    "personales en su próximo ingreso web."
                ),
                verbose_name="Debe confirmar datos personales",
            ),
        ),
        migrations.AddField(
            model_name="profile",
            name="datos_confirmados_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name="Datos personales confirmados en",
            ),
        ),
        migrations.RunPython(
            marcar_perfiles_existentes,
            desmarcar_perfiles,
        ),
    ]
