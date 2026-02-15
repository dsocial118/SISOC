from django.db import migrations


def ensure_ciudadano_geo_columns(apps, schema_editor):
    connection = schema_editor.connection
    Ciudadano = apps.get_model("ciudadanos", "Ciudadano")
    table = Ciudadano._meta.db_table

    with connection.cursor() as cursor:
        columns = {
            col.name
            for col in connection.introspection.get_table_description(cursor, table)
        }

    for field_name in ("latitud", "longitud", "estado_civil", "cuil_cuit", "origen_dato"):
        if field_name in columns:
            continue
        schema_editor.add_field(Ciudadano, Ciudadano._meta.get_field(field_name))


class Migration(migrations.Migration):

    dependencies = [
        ("ciudadanos", "0020_remove_historialtransferencia_unique_historial_ciudadano_mes_anio_and_more"),
    ]

    operations = [
        migrations.RunPython(ensure_ciudadano_geo_columns, migrations.RunPython.noop),
    ]
