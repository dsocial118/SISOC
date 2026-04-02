from django.db import migrations


LEGACY_CURSO_COLUMNS = ("cupo_total", "fecha_inicio", "fecha_fin")
CURSO_ESTADO_TO_COMISION = {
    "planificado": "planificada",
    "activo": "activa",
    "finalizado": "cerrada",
    "cancelado": "suspendida",
}


def _map_curso_estado_to_comision(estado):
    return CURSO_ESTADO_TO_COMISION.get(estado, "planificada")


def _backfill_comision_curso_if_needed(
    curso_model, comision_curso_model, existing_columns
):
    required_columns = set(LEGACY_CURSO_COLUMNS)
    if not required_columns.issubset(existing_columns):
        return

    cursos_con_comision = set(
        comision_curso_model.objects.values_list("curso_id", flat=True)
    )
    cursos_legacy = (
        curso_model.objects.exclude(cupo_total__isnull=True)
        .exclude(fecha_inicio__isnull=True)
        .exclude(fecha_fin__isnull=True)
    )

    comisiones_creadas = []
    for curso in cursos_legacy.iterator():
        if curso.pk in cursos_con_comision:
            continue
        comisiones_creadas.append(
            comision_curso_model(
                curso_id=curso.pk,
                codigo_comision=f"LEG-{curso.pk}",
                nombre=curso.nombre,
                cupo_total=curso.cupo_total,
                fecha_inicio=curso.fecha_inicio,
                fecha_fin=curso.fecha_fin,
                estado=_map_curso_estado_to_comision(curso.estado),
                observaciones=getattr(curso, "observaciones", None),
            )
        )

    if comisiones_creadas:
        comision_curso_model.objects.bulk_create(comisiones_creadas)


def _drop_curso_columns_if_present(apps, schema_editor):
    """Backfill legacy Curso data into ComisionCurso before dropping columns."""
    curso_model = apps.get_model("VAT", "Curso")
    comision_curso_model = apps.get_model("VAT", "ComisionCurso")
    table_name = curso_model._meta.db_table
    connection = schema_editor.connection
    introspection = connection.introspection

    with connection.cursor() as cursor:
        if table_name not in introspection.table_names(cursor):
            return

        description = introspection.get_table_description(cursor, table_name)
        existing = {getattr(column, "name", column[0]) for column in description}

    _backfill_comision_curso_if_needed(curso_model, comision_curso_model, existing)

    for column_name in LEGACY_CURSO_COLUMNS:
        if column_name in existing:
            field = curso_model._meta.get_field(column_name)
            schema_editor.remove_field(curso_model, field)


class Migration(migrations.Migration):
    dependencies = [
        ("VAT", "0023_ofertainstitucional_voucher_parametrias"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
                    _drop_curso_columns_if_present,
                    reverse_code=migrations.RunPython.noop,
                )
            ],
            state_operations=[
                migrations.RemoveField(
                    model_name="curso",
                    name="cupo_total",
                ),
                migrations.RemoveField(
                    model_name="curso",
                    name="fecha_fin",
                ),
                migrations.RemoveField(
                    model_name="curso",
                    name="fecha_inicio",
                ),
            ],
        ),
    ]
