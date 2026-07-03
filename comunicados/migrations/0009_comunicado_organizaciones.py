from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("organizaciones", "0015_quitar_acta_solicitud_subsidio"),
        ("comunicados", "0008_mailingjobattachment"),
    ]

    operations = [
        migrations.AlterField(
            model_name="comunicado",
            name="subtipo",
            field=models.CharField(
                blank=True,
                choices=[
                    ("institucional", "Comunicación Institucional"),
                    ("comedores", "Comunicación a Comedores"),
                    ("organizaciones", "Comunicación a Organizaciones"),
                ],
                default="",
                max_length=20,
                verbose_name="Subtipo de comunicado",
            ),
        ),
        migrations.AddField(
            model_name="comunicado",
            name="organizaciones",
            field=models.ManyToManyField(
                blank=True,
                related_name="comunicados",
                to="organizaciones.organizacion",
                verbose_name="Organizaciones destinatarias",
            ),
        ),
    ]
