from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0037_userimportjob_is_pwa_import"),
    ]

    operations = [
        migrations.AlterField(
            model_name="auditaccesocomedorpwa",
            name="accion",
            field=models.CharField(
                choices=[
                    ("create", "Alta"),
                    ("reactivate", "Reactivación"),
                    ("deactivate", "Baja"),
                    ("update_permissions", "Edicion de permisos"),
                ],
                db_index=True,
                max_length=20,
            ),
        ),
    ]
