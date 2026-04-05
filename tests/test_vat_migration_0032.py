from importlib import import_module
from unittest.mock import Mock

migration_0032 = import_module("VAT.migrations.0032_move_curso_ubicacion_to_comisioncurso")


def _build_schema_editor(*, vendor, null_count=0):
    cursor_manager = Mock()
    cursor = Mock()
    cursor.fetchone.return_value = (null_count,)
    cursor_manager.__enter__ = Mock(return_value=cursor)
    cursor_manager.__exit__ = Mock(return_value=False)

    connection = Mock()
    connection.vendor = vendor
    connection.cursor.return_value = cursor_manager

    schema_editor = Mock()
    schema_editor.connection = connection
    return schema_editor


def test_enforce_comisioncurso_ubicacion_not_null_if_safe_skips_mysql_with_nulls():
    apps = Mock()
    comisioncurso_model = Mock()
    comisioncurso_model._meta.db_table = "VAT_comisioncurso"
    institucion_ubicacion_model = Mock()
    apps.get_model.side_effect = [comisioncurso_model, institucion_ubicacion_model]

    schema_editor = _build_schema_editor(vendor="mysql", null_count=3)

    migration_0032.enforce_comisioncurso_ubicacion_not_null_if_safe(apps, schema_editor)

    schema_editor.alter_field.assert_not_called()


def test_enforce_comisioncurso_ubicacion_not_null_if_safe_alters_when_safe():
    apps = Mock()
    comisioncurso_model = Mock()
    comisioncurso_model._meta.db_table = "VAT_comisioncurso"
    institucion_ubicacion_model = Mock()
    apps.get_model.side_effect = [comisioncurso_model, institucion_ubicacion_model]

    schema_editor = _build_schema_editor(vendor="mysql", null_count=0)

    migration_0032.enforce_comisioncurso_ubicacion_not_null_if_safe(apps, schema_editor)

    schema_editor.alter_field.assert_called_once()
