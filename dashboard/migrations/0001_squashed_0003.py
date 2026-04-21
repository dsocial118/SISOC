from django.db import migrations, models


class Migration(migrations.Migration):

    replaces = [
        ("dashboard", "0001_initial"),
        ("dashboard", "0002_tablero"),
        ("dashboard", "0003_alter_tablero_permisos"),
    ]

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Dashboard",
            fields=[
                (
                    "llave",
                    models.CharField(
                        help_text="Llave única para identificar el registro en el dashboard.",
                        max_length=255,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                (
                    "cantidad",
                    models.BigIntegerField(
                        default=0,
                        help_text="Cantidad asociada al registro en el dashboard.",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Tablero",
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
                        help_text="Nombre visible en el menú y el encabezado del tablero.",
                        max_length=255,
                    ),
                ),
                (
                    "slug",
                    models.SlugField(
                        help_text="Identificador único para la URL del tablero.",
                        max_length=255,
                        unique=True,
                    ),
                ),
                (
                    "url",
                    models.URLField(
                        blank=True,
                        help_text="URL embebida del tablero (Power BI u otra herramienta).",
                    ),
                ),
                (
                    "mensaje_construccion",
                    models.TextField(
                        blank=True,
                        help_text="Mensaje a mostrar cuando el tablero no tiene URL.",
                    ),
                ),
                (
                    "orden",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="Orden de aparición en el menú de tableros.",
                    ),
                ),
                (
                    "activo",
                    models.BooleanField(
                        default=True,
                        help_text="Define si el tablero aparece en el menú.",
                    ),
                ),
                (
                    "permisos",
                    models.JSONField(
                        blank=True,
                        default=list,
                        help_text="Listado de permisos con acceso al tablero (app_label.codename). Se aceptan nombres de grupo legacy por compatibilidad.",
                    ),
                ),
            ],
            options={
                "verbose_name": "tablero",
                "verbose_name_plural": "tableros",
                "ordering": ["orden", "nombre"],
            },
        ),
    ]
