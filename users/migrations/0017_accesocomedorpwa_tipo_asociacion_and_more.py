from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("organizaciones", "0008_alter_aval_managers_alter_firmante_managers_and_more"),
        ("users", "0016_bootstrap_formulario_cdi_permissions"),
    ]

    operations = [
        migrations.AddField(
            model_name="accesocomedorpwa",
            name="organizacion",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.PROTECT,
                related_name="accesos_pwa",
                to="organizaciones.organizacion",
            ),
        ),
        migrations.AddField(
            model_name="accesocomedorpwa",
            name="tipo_asociacion",
            field=models.CharField(
                choices=[
                    ("organizacion", "Organización"),
                    ("espacio", "Espacio"),
                ],
                default="espacio",
                max_length=20,
            ),
        ),
        migrations.AddIndex(
            model_name="accesocomedorpwa",
            index=models.Index(
                fields=["organizacion", "activo"],
                name="users_acces_organiz_e9365d_idx",
            ),
        ),
    ]
