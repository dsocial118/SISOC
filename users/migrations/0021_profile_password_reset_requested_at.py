from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "users",
            "0020_rename_users_audit_user_74b57d_idx_users_audit_user_id_0e2825_idx_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="password_reset_requested_at",
            field=models.DateTimeField(
                blank=True,
                help_text=(
                    "Se completa cuando un usuario mobile solicita desde la app "
                    "que un administrador genere una nueva contraseña temporal."
                ),
                null=True,
                verbose_name="Reset de contraseña solicitado en",
            ),
        ),
    ]
