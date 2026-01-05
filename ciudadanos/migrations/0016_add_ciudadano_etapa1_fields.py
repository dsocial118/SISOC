# Generated manually for ETAPA 1

from django.db import migrations, models


def add_ciudadano_fields(apps, schema_editor):
    Ciudadano = apps.get_model("ciudadanos", "Ciudadano")
    table = Ciudadano._meta.db_table
    connection = schema_editor.connection

    def column_exists(name: str) -> bool:
        with connection.cursor() as cursor:
            columns = connection.introspection.get_table_description(cursor, table)
        return any(col.name == name for col in columns)

    fields = [
        (
            "latitud",
            models.DecimalField(
                blank=True, decimal_places=6, max_digits=9, null=True
            ),
        ),
        (
            "longitud",
            models.DecimalField(
                blank=True, decimal_places=6, max_digits=9, null=True
            ),
        ),
        (
            "estado_civil",
            models.CharField(
                blank=True,
                choices=[
                    ("soltero", "Soltero/a"),
                    ("casado", "Casado/a"),
                    ("divorciado", "Divorciado/a"),
                    ("viudo", "Viudo/a"),
                    ("union_convivencial", "Unión convivencial"),
                ],
                max_length=20,
                null=True,
            ),
        ),
        ("cuil_cuit", models.CharField(blank=True, max_length=13, null=True)),
        (
            "origen_dato",
            models.CharField(
                choices=[
                    ("anses", "ANSES"),
                    ("renaper", "RENAPER"),
                    ("manual", "Carga Manual"),
                    ("migracion", "Migración"),
                ],
                default="manual",
                max_length=20,
            ),
        ),
    ]

    for name, field in fields:
        if column_exists(name):
            continue
        field.set_attributes_from_name(name)
        field.model = Ciudadano
        schema_editor.add_field(Ciudadano, field)


class Migration(migrations.Migration):

    dependencies = [
        ('ciudadanos', '0015_cleanup_ciudadano_legacy_columns'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
                    add_ciudadano_fields, migrations.RunPython.noop
                )
            ],
            state_operations=[
                migrations.AddField(
                    model_name="ciudadano",
                    name="latitud",
                    field=models.DecimalField(
                        blank=True, decimal_places=6, max_digits=9, null=True
                    ),
                ),
                migrations.AddField(
                    model_name="ciudadano",
                    name="longitud",
                    field=models.DecimalField(
                        blank=True, decimal_places=6, max_digits=9, null=True
                    ),
                ),
                migrations.AddField(
                    model_name="ciudadano",
                    name="estado_civil",
                    field=models.CharField(
                        blank=True,
                        choices=[
                            ("soltero", "Soltero/a"),
                            ("casado", "Casado/a"),
                            ("divorciado", "Divorciado/a"),
                            ("viudo", "Viudo/a"),
                            ("union_convivencial", "Unión convivencial"),
                        ],
                        max_length=20,
                        null=True,
                    ),
                ),
                migrations.AddField(
                    model_name="ciudadano",
                    name="cuil_cuit",
                    field=models.CharField(blank=True, max_length=13, null=True),
                ),
                migrations.AddField(
                    model_name="ciudadano",
                    name="origen_dato",
                    field=models.CharField(
                        choices=[
                            ("anses", "ANSES"),
                            ("renaper", "RENAPER"),
                            ("manual", "Carga Manual"),
                            ("migracion", "Migración"),
                        ],
                        default="manual",
                        max_length=20,
                    ),
                ),
            ],
        ),
    ]
