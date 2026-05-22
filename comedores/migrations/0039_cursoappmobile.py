from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("comedores", "0038_comedordatosconveniopnud"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="CursoAppMobile",
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
                    "deleted_at",
                    models.DateTimeField(
                        blank=True, db_index=True, editable=False, null=True
                    ),
                ),
                ("nombre", models.CharField(max_length=255)),
                ("link", models.URLField(max_length=500)),
                (
                    "imagen",
                    models.ImageField(
                        blank=True, null=True, upload_to="comedores/cursos_app_mobile/"
                    ),
                ),
                (
                    "descripcion",
                    models.CharField(blank=True, max_length=300, null=True),
                ),
                (
                    "programa_objetivo",
                    models.CharField(
                        choices=[
                            ("pnud", "PNUD"),
                            ("alimentar_comunidad", "Alimentar Comunidad"),
                            ("ambos", "PNUD y Alimentar Comunidad"),
                        ],
                        default="pnud",
                        max_length=30,
                    ),
                ),
                ("activo", models.BooleanField(default=True)),
                ("orden", models.PositiveIntegerField(default=0)),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True)),
                ("fecha_modificacion", models.DateTimeField(auto_now=True)),
                (
                    "creado_por",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="cursos_app_mobile_creados",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "modificado_por",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="cursos_app_mobile_modificados",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Curso App Mobile",
                "verbose_name_plural": "Cursos App Mobile",
                "ordering": ["orden", "nombre", "id"],
            },
        ),
        migrations.AddIndex(
            model_name="cursoappmobile",
            index=models.Index(
                fields=["programa_objetivo", "activo"],
                name="comedores_c_program_1d6a38_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="cursoappmobile",
            index=models.Index(
                fields=["orden", "nombre"], name="comedores_c_orden_7ff31f_idx"
            ),
        ),
    ]
