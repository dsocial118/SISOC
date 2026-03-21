from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("VAT", "0006_remove_beneficiarios_responsables"),
    ]

    operations = [
        migrations.CreateModel(
            name="ModalidadInstitucional",
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
                    "nombre",
                    models.CharField(
                        max_length=100, verbose_name="Nombre de la modalidad"
                    ),
                ),
                (
                    "descripcion",
                    models.TextField(blank=True, null=True, verbose_name="Descripción"),
                ),
                ("activo", models.BooleanField(default=True, verbose_name="Activo")),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True)),
                ("fecha_modificacion", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Modalidad Institucional",
                "verbose_name_plural": "Modalidades Institucionales",
                "ordering": ["nombre"],
            },
        ),
    ]
