from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def migrate_programa_from_ciudadanos(apps, schema_editor):
    try:
        programa_old = apps.get_model('ciudadanos', 'Programa')
        programa_new = apps.get_model('core', 'Programa')
        for old in programa_old.objects.all():
            programa_new.objects.create(
                id=old.id,
                nombre=old.nombre,
                estado=old.estado,
                observaciones=old.observaciones,
            )
    except Exception:
        pass


def migrate_nacionalidad_from_ciudadanos(apps, schema_editor):
    try:
        nacionalidad_old = apps.get_model("ciudadanos", "Nacionalidad")
    except LookupError:
        return
    nacionalidad_new = apps.get_model("core", "Nacionalidad")
    db_alias = schema_editor.connection.alias
    for old in nacionalidad_old.objects.using(db_alias).all():
        nacionalidad_new.objects.using(db_alias).update_or_create(
            id=old.id, defaults={"nacionalidad": old.nacionalidad}
        )


class Migration(migrations.Migration):

    replaces = [
        ("core", "0001_initial"),
        ("core", "0002_alter_provincia_nombre"),
        ("core", "0003_programa_and_migrate_data"),
        ("core", "0004_nacionalidad"),
        ("core", "0005_favorite_filter"),
        ("core", "0006_preferencia_columnas"),
        ("core", "0007_montoprestacionprograma"),
    ]

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Dia",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=255)),
            ],
            options={"verbose_name": "Dia", "verbose_name_plural": "Dias", "ordering": ["id"]},
        ),
        migrations.CreateModel(
            name="Mes",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=255)),
            ],
            options={"verbose_name": "Mes", "verbose_name_plural": "Meses", "ordering": ["id"]},
        ),
        migrations.CreateModel(
            name="Provincia",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=255, unique=True)),
            ],
            options={"verbose_name": "Provincia", "verbose_name_plural": "Provincia", "ordering": ["id"]},
        ),
        migrations.CreateModel(
            name="Sexo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sexo", models.CharField(max_length=10)),
            ],
            options={"verbose_name": "Sexo", "verbose_name_plural": "Sexos"},
        ),
        migrations.CreateModel(
            name="Turno",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=255)),
            ],
            options={"verbose_name": "Turno", "verbose_name_plural": "Turnos", "ordering": ["id"]},
        ),
        migrations.CreateModel(
            name="Municipio",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=255)),
                (
                    "provincia",
                    models.ForeignKey(
                        blank=True, null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="core.provincia",
                    ),
                ),
            ],
            options={
                "verbose_name": "Municipio", "verbose_name_plural": "Municipio",
                "ordering": ["id"], "unique_together": {("nombre", "provincia")},
            },
        ),
        migrations.CreateModel(
            name="Localidad",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=255)),
                (
                    "municipio",
                    models.ForeignKey(
                        blank=True, null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="core.municipio",
                    ),
                ),
            ],
            options={"verbose_name": "Localidad", "verbose_name_plural": "Localidad", "unique_together": {("nombre", "municipio")}},
        ),
        migrations.CreateModel(
            name="Programa",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=255, unique=True)),
                ("estado", models.BooleanField(default=True)),
                ("observaciones", models.CharField(blank=True, max_length=500, null=True)),
            ],
            options={"verbose_name": "Programa", "verbose_name_plural": "Programas", "ordering": ["nombre"]},
        ),
        migrations.RunPython(migrate_programa_from_ciudadanos, migrations.RunPython.noop),
        migrations.CreateModel(
            name="Nacionalidad",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nacionalidad", models.CharField(max_length=50)),
            ],
            options={"verbose_name": "Nacionalidad", "verbose_name_plural": "Nacionalidades"},
        ),
        migrations.RunPython(migrate_nacionalidad_from_ciudadanos, migrations.RunPython.noop),
        migrations.CreateModel(
            name="FiltroFavorito",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("seccion", models.CharField(max_length=100)),
                ("nombre", models.CharField(max_length=120)),
                ("filtros", models.JSONField(default=dict)),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True)),
                (
                    "usuario",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="filtros_favoritos",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["fecha_creacion"]},
        ),
        migrations.AddConstraint(
            model_name="filtrofavorito",
            constraint=models.UniqueConstraint(
                fields=("usuario", "seccion", "nombre"),
                name="unico_filtro_favorito_usuario_seccion_nombre",
            ),
        ),
        migrations.CreateModel(
            name="PreferenciaColumnas",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("listado", models.CharField(max_length=150)),
                ("columnas", models.JSONField(default=list)),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True)),
                ("fecha_actualizacion", models.DateTimeField(auto_now=True)),
                (
                    "usuario",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="preferencias_columnas",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-fecha_actualizacion"]},
        ),
        migrations.AddConstraint(
            model_name="preferenciacolumnas",
            constraint=models.UniqueConstraint(
                fields=("usuario", "listado"),
                name="unica_preferencia_columnas_usuario_listado",
            ),
        ),
        migrations.CreateModel(
            name="MontoPrestacionPrograma",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "programa",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="montos_prestacion",
                        to="core.programa",
                        verbose_name="Programa",
                    ),
                ),
                ("desayuno_valor", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name="Valor desayuno")),
                ("almuerzo_valor", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name="Valor almuerzo")),
                ("merienda_valor", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name="Valor merienda")),
                ("cena_valor", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name="Valor cena")),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")),
                ("fecha_modificacion", models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")),
                (
                    "usuario_creador",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"verbose_name": "Prestación", "verbose_name_plural": "Prestaciones", "ordering": ["id"]},
        ),
        migrations.AddConstraint(
            model_name="montoprestacionprograma",
            constraint=models.CheckConstraint(
                check=(
                    models.Q(desayuno_valor__isnull=False)
                    | models.Q(almuerzo_valor__isnull=False)
                    | models.Q(merienda_valor__isnull=False)
                    | models.Q(cena_valor__isnull=False)
                ),
                name="monto_prestacion_al_menos_un_valor",
            ),
        ),
    ]
