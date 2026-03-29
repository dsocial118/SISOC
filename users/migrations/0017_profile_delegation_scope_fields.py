from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("users", "0016_bootstrap_formulario_cdi_permissions"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="grupos_asignables",
            field=models.ManyToManyField(
                blank=True,
                help_text="Define qué grupos puede asignar este usuario al crear/editar otros usuarios.",
                related_name="perfiles_delegadores",
                to="auth.group",
                verbose_name="Grupos que puede asignar",
            ),
        ),
        migrations.AddField(
            model_name="profile",
            name="roles_asignables",
            field=models.ManyToManyField(
                blank=True,
                help_text="Permisos auth.role_* que este usuario puede asignar a terceros.",
                related_name="perfiles_roles_delegables",
                to="auth.permission",
                verbose_name="Roles que puede asignar",
            ),
        ),
    ]
