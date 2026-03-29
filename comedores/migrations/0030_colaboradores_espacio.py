from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def cargar_actividades_colaborador(apps, schema_editor):
    ActividadColaboradorEspacio = apps.get_model(
        "comedores", "ActividadColaboradorEspacio"
    )
    actividades = [
        {"orden": 1, "alias": "COM", "nombre": "Compras"},
        {"orden": 2, "alias": "LIM", "nombre": "Limpieza"},
        {"orden": 3, "alias": "COM", "nombre": "Prep/Serv Alimentos"},
        {"orden": 4, "alias": "COM", "nombre": "Cuidado Niños/Niñas/Adolesc"},
        {"orden": 5, "alias": "COM", "nombre": "Tareas Administ./Rend.Cuentas"},
        {"orden": 6, "alias": "MAN", "nombre": "Mantenimiento"},
        {"orden": 7, "alias": "ROE", "nombre": "Responsable de la Org.Ejecutante"},
        {"orden": 8, "alias": "ROS", "nombre": "Responsable de la Org.Solicitante"},
    ]
    for actividad in actividades:
        ActividadColaboradorEspacio.objects.update_or_create(
            alias=actividad["alias"],
            nombre=actividad["nombre"],
            defaults={
                "orden": actividad["orden"],
                "activo": True,
            },
        )


def revertir_actividades_colaborador(apps, schema_editor):
    ActividadColaboradorEspacio = apps.get_model(
        "comedores", "ActividadColaboradorEspacio"
    )
    ActividadColaboradorEspacio.objects.filter(
        nombre__in=[
            "Compras",
            "Limpieza",
            "Prep/Serv Alimentos",
            "Cuidado Niños/Niñas/Adolesc",
            "Tareas Administ./Rend.Cuentas",
            "Mantenimiento",
            "Responsable de la Org.Ejecutante",
            "Responsable de la Org.Solicitante",
        ]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("ciudadanos", "0021_ensure_ciudadano_geo_columns"),
        ("comedores", "0029_nomina_comedor_directo"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ActividadColaboradorEspacio",
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
                ("alias", models.CharField(max_length=10)),
                ("nombre", models.CharField(max_length=255)),
                ("orden", models.PositiveSmallIntegerField(default=0)),
                ("activo", models.BooleanField(default=True)),
            ],
            options={
                "verbose_name": "Actividad de colaborador del espacio",
                "verbose_name_plural": "Actividades de colaboradores del espacio",
                "ordering": ["orden", "id"],
            },
        ),
        migrations.CreateModel(
            name="ColaboradorEspacio",
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
                    "genero",
                    models.CharField(
                        choices=[
                            ("V", "Varón"),
                            ("M", "Mujer"),
                            ("VT", "Varón Trans"),
                            ("MT", "Mujer Trans"),
                            ("TR", "Travesti"),
                            ("OT", "Otros"),
                            ("ND", "No declara"),
                        ],
                        default="ND",
                        max_length=2,
                    ),
                ),
                ("codigo_telefono", models.CharField(blank=True, max_length=10, null=True)),
                ("numero_telefono", models.CharField(blank=True, max_length=20, null=True)),
                ("fecha_alta", models.DateField()),
                ("fecha_baja", models.DateField(blank=True, null=True)),
                ("fecha_creado", models.DateTimeField(auto_now_add=True)),
                ("fecha_modificado", models.DateTimeField(auto_now=True)),
                (
                    "ciudadano",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="colaboraciones_espacio",
                        to="ciudadanos.ciudadano",
                    ),
                ),
                (
                    "comedor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="colaboradores_espacio",
                        to="comedores.comedor",
                    ),
                ),
                (
                    "creado_por",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="colaboradores_espacio_creados",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "modificado_por",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="colaboradores_espacio_modificados",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Colaborador del espacio",
                "verbose_name_plural": "Colaboradores del espacio",
                "ordering": ["ciudadano__apellido", "ciudadano__nombre", "-id"],
            },
        ),
        migrations.AddField(
            model_name="colaboradorespacio",
            name="actividades",
            field=models.ManyToManyField(
                blank=True,
                related_name="colaboradores",
                to="comedores.actividadcolaboradorespacio",
            ),
        ),
        migrations.AddConstraint(
            model_name="actividadcolaboradorespacio",
            constraint=models.UniqueConstraint(
                fields=("alias", "nombre"),
                name="uniq_actividad_colaborador_espacio_alias_nombre",
            ),
        ),
        migrations.AddConstraint(
            model_name="colaboradorespacio",
            constraint=models.UniqueConstraint(
                fields=("comedor", "ciudadano"),
                name="uniq_colaborador_espacio_por_comedor_ciudadano",
            ),
        ),
        migrations.AddIndex(
            model_name="colaboradorespacio",
            index=models.Index(
                fields=["comedor", "fecha_baja"],
                name="comedores_c_comedor_6a9f95_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="colaboradorespacio",
            index=models.Index(
                fields=["ciudadano"],
                name="comedores_c_ciudada_05b1f7_idx",
            ),
        ),
        migrations.RunPython(
            cargar_actividades_colaborador,
            reverse_code=revertir_actividades_colaborador,
        ),
    ]
