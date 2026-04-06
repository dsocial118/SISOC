from django.db import migrations, models
import django.db.models.deletion


def _column_exists(schema_editor, table_name, column_name):
    with schema_editor.connection.cursor() as cursor:
        description = schema_editor.connection.introspection.get_table_description(
            cursor,
            table_name,
        )
    return any(column.name == column_name for column in description)


def add_comisioncurso_ubicacion_if_missing(apps, schema_editor):
    ComisionCurso = apps.get_model("VAT", "ComisionCurso")
    InstitucionUbicacion = apps.get_model("VAT", "InstitucionUbicacion")

    if _column_exists(schema_editor, ComisionCurso._meta.db_table, "ubicacion_id"):
        return

    field = models.ForeignKey(
        InstitucionUbicacion,
        blank=True,
        null=True,
        on_delete=django.db.models.deletion.PROTECT,
        related_name="comisiones_curso",
        verbose_name="Ubicación",
    )
    field.set_attributes_from_name("ubicacion")
    schema_editor.add_field(ComisionCurso, field)


def copy_curso_ubicacion_to_comisioncurso(apps, schema_editor):
    ComisionCurso = apps.get_model("VAT", "ComisionCurso")

    for comision in ComisionCurso.objects.select_related("curso").all().iterator():
        if comision.ubicacion_id:
            continue

        if comision.curso_id and comision.curso.ubicacion_id:
            comision.ubicacion_id = comision.curso.ubicacion_id
            comision.save(update_fields=["ubicacion"])


def _has_null_ubicaciones(schema_editor, table_name):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            f"SELECT COUNT(*) FROM `{table_name}` WHERE `ubicacion_id` IS NULL"
        )
        return cursor.fetchone()[0] > 0


def enforce_comisioncurso_ubicacion_not_null_if_safe(apps, schema_editor):
    ComisionCurso = apps.get_model("VAT", "ComisionCurso")
    InstitucionUbicacion = apps.get_model("VAT", "InstitucionUbicacion")

    if (
        schema_editor.connection.vendor == "mysql"
        and _has_null_ubicaciones(schema_editor, ComisionCurso._meta.db_table)
    ):
        return

    from_field = models.ForeignKey(
        InstitucionUbicacion,
        blank=True,
        null=True,
        on_delete=django.db.models.deletion.PROTECT,
        related_name="comisiones_curso",
        verbose_name="Ubicación",
    )
    from_field.set_attributes_from_name("ubicacion")

    to_field = models.ForeignKey(
        InstitucionUbicacion,
        on_delete=django.db.models.deletion.PROTECT,
        related_name="comisiones_curso",
        verbose_name="Ubicación",
    )
    to_field.set_attributes_from_name("ubicacion")

    schema_editor.alter_field(ComisionCurso, from_field, to_field, strict=False)


class Migration(migrations.Migration):

    dependencies = [
        ("VAT", "0031_remove_curso_programa"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
                    add_comisioncurso_ubicacion_if_missing,
                    migrations.RunPython.noop,
                )
            ],
            state_operations=[
                migrations.AddField(
                    model_name="comisioncurso",
                    name="ubicacion",
                    field=models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="comisiones_curso",
                        to="VAT.institucionubicacion",
                        verbose_name="Ubicación",
                    ),
                )
            ],
        ),
        migrations.RunPython(
            copy_curso_ubicacion_to_comisioncurso,
            migrations.RunPython.noop,
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
                    enforce_comisioncurso_ubicacion_not_null_if_safe,
                    migrations.RunPython.noop,
                )
            ],
            state_operations=[
                migrations.AlterField(
                    model_name="comisioncurso",
                    name="ubicacion",
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="comisiones_curso",
                        to="VAT.institucionubicacion",
                        verbose_name="Ubicación",
                    ),
                )
            ],
        ),
        migrations.RemoveField(
            model_name="curso",
            name="ubicacion",
        ),
    ]
