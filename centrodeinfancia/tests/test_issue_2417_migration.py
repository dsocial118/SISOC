from importlib import import_module

from django.db import migrations, models


migration_0048 = import_module(
    "centrodeinfancia.migrations.0048_issue_2417_respuestas_no_sabe"
)


def test_0048_preserva_respuestas_booleanas_del_calendario():
    assert dict(migration_0048.CALENDARIO_BOOLEANO_A_RESPUESTA) == {
        True: "si",
        False: "no",
    }


def test_0048_revierte_no_sabe_a_nulo():
    respuestas_reversibles = {
        respuesta: valor
        for valor, respuesta in migration_0048.CALENDARIO_BOOLEANO_A_RESPUESTA
    }

    assert respuestas_reversibles == {"si": True, "no": False}
    assert respuestas_reversibles.get("no_sabe") is None


def test_0048_reemplaza_la_columna_sin_coercion_directa():
    operations = migration_0048.Migration.operations

    assert isinstance(operations[0], migrations.AddField)
    assert isinstance(operations[0].field, models.CharField)
    assert isinstance(operations[1], migrations.RunPython)
    assert isinstance(operations[2], migrations.RemoveField)
    assert isinstance(operations[3], migrations.RenameField)
