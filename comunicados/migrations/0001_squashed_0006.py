import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    replaces = [
        ("comunicados", "0001_initial"),
        ("comunicados", "0002_crear_grupos_permisos"),
        ("comunicados", "0003_add_tipo_comedores"),
        ("comunicados", "0004_create_v2_groups"),
        ("comunicados", "0005_add_subtipo"),
        ("comunicados", "0006_alter_comunicado_tipo"),
    ]

    initial = True

    dependencies = [
        ("comedores", "0021_alter_nomina_estado"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Comunicado",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("titulo", models.CharField(max_length=255, verbose_name="Título")),
                ("cuerpo", models.TextField(verbose_name="Cuerpo")),
                (
                    "estado",
                    models.CharField(
                        choices=[
                            ("borrador", "Borrador"),
                            ("publicado", "Publicado"),
                            ("archivado", "Archivado"),
                        ],
                        default="borrador",
                        max_length=20,
                        verbose_name="Estado",
                    ),
                ),
                ("destacado", models.BooleanField(default=False, verbose_name="Destacado")),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")),
                ("fecha_publicacion", models.DateTimeField(blank=True, null=True, verbose_name="Fecha de publicación")),
                ("fecha_vencimiento", models.DateTimeField(blank=True, null=True, verbose_name="Fecha de vencimiento")),
                ("fecha_ultima_modificacion", models.DateTimeField(auto_now=True, verbose_name="Fecha última modificación")),
                (
                    "usuario_creador",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="comunicados_creados",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Usuario creador",
                    ),
                ),
                (
                    "usuario_ultima_modificacion",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="comunicados_modificados",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Última modificación por",
                    ),
                ),
                (
                    "comedores",
                    models.ManyToManyField(
                        blank=True,
                        related_name="comunicados",
                        to="comedores.comedor",
                        verbose_name="Comedores destinatarios",
                    ),
                ),
                ("para_todos_comedores", models.BooleanField(default=False, verbose_name="Enviar a todos los comedores")),
                (
                    "tipo",
                    models.CharField(
                        choices=[
                            ("interno", "Comunicación Interna"),
                            ("externo", "Comunicación Externa"),
                        ],
                        default="interno",
                        max_length=20,
                        verbose_name="Tipo de comunicado",
                    ),
                ),
                (
                    "subtipo",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("institucional", "Comunicación Institucional"),
                            ("comedores", "Comunicación a Comedores"),
                        ],
                        default="",
                        max_length=20,
                        verbose_name="Subtipo de comunicado",
                    ),
                ),
            ],
            options={
                "verbose_name": "Comunicado",
                "verbose_name_plural": "Comunicados",
                "ordering": ["-destacado", "-fecha_publicacion", "-fecha_creacion"],
            },
        ),
        migrations.CreateModel(
            name="ComunicadoAdjunto",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("archivo", models.FileField(upload_to="comunicados/adjuntos/", verbose_name="Archivo")),
                ("nombre_original", models.CharField(blank=True, max_length=255, verbose_name="Nombre original")),
                ("fecha_subida", models.DateTimeField(auto_now_add=True, verbose_name="Fecha de subida")),
                (
                    "comunicado",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="adjuntos",
                        to="comunicados.comunicado",
                        verbose_name="Comunicado",
                    ),
                ),
            ],
            options={
                "verbose_name": "Adjunto",
                "verbose_name_plural": "Adjuntos",
            },
        ),
    ]
