import json
from io import StringIO
from contextlib import nullcontext

import pytest

from core.management.commands.load_fixtures import Command


def _command():
    cmd = Command()
    cmd.stdout = StringIO()
    cmd.stderr = StringIO()
    return cmd


def test_handle_sets_force_and_calls_load_fixtures(mocker):
    cmd = _command()
    mock_load = mocker.patch.object(cmd, "load_fixtures")

    cmd.handle(force=True)

    assert cmd.force is True
    mock_load.assert_called_once_with()


def test_get_models_from_fixture_success(tmp_path):
    cmd = _command()
    fixture = tmp_path / "fx.json"
    fixture.write_text(
        json.dumps([{"model": "a.b"}, {"other": 1}, {"model": "c.d"}]), encoding="utf-8"
    )

    result = cmd.get_models_from_fixture(str(fixture))

    assert result == {"a.b", "c.d"}


def test_get_models_from_fixture_error(tmp_path):
    cmd = _command()
    fixture = tmp_path / "broken.json"
    fixture.write_text("{broken", encoding="utf-8")

    result = cmd.get_models_from_fixture(str(fixture))

    assert result == set()
    assert "Error al leer" in cmd.stderr.getvalue()


def test_model_is_empty_success_and_error(mocker):
    cmd = _command()
    mock_model = mocker.Mock()
    mock_model.objects.count.return_value = 0
    mocker.patch("core.management.commands.load_fixtures.apps.get_model", return_value=mock_model)

    assert cmd.model_is_empty("app.model") is True

    mocker.patch(
        "core.management.commands.load_fixtures.apps.get_model",
        side_effect=RuntimeError("boom"),
    )
    assert cmd.model_is_empty("app.model") is False
    assert "Error al consultar" in cmd.stderr.getvalue()


def test_should_load_fixture_force_and_empty_models(mocker):
    cmd = _command()
    cmd.force = True
    assert cmd.should_load_fixture("x.json") is True

    cmd.force = False
    mocker.patch.object(cmd, "get_models_from_fixture", return_value=set())
    assert cmd.should_load_fixture("x.json") is False
    assert "Sin modelos en" in cmd.stderr.getvalue()


def test_should_load_fixture_when_any_model_empty(mocker):
    cmd = _command()
    cmd.force = False
    mocker.patch.object(cmd, "get_models_from_fixture", return_value={"a.b", "c.d"})
    mocker.patch.object(cmd, "model_is_empty", side_effect=[False, True])

    assert cmd.should_load_fixture("x.json") is True


def test_upsert_fixture_deserialize_error(mocker):
    cmd = _command()
    mocker.patch(
        "core.management.commands.load_fixtures.serializers.deserialize",
        side_effect=RuntimeError("bad"),
    )

    cmd.upsert_fixture("x.json")

    assert "No se pudo deserializar" in cmd.stderr.getvalue()


def test_upsert_fixture_counts_created_updated_and_failed(mocker, tmp_path):
    cmd = _command()
    fixture = tmp_path / "fx.json"
    fixture.write_text("[]", encoding="utf-8")

    class DummyManager:
        @staticmethod
        def filter(pk):
            class Qs:
                @staticmethod
                def exists():
                    return pk == 1

            return Qs()

    class DummyObj:
        _meta = type("Meta", (), {"pk": type("Pk", (), {"attname": "id"})()})()
        objects = DummyManager()

        def __init__(self, pk):
            self.id = pk

    class DummySerialized:
        def __init__(self, pk, fail=False):
            self.object = DummyObj(pk)
            self._fail = fail

        def save(self):
            if self._fail:
                raise RuntimeError("save")

    obj1 = DummySerialized(1, fail=False)
    obj2 = DummySerialized(2, fail=False)
    obj3 = DummySerialized(3, fail=True)

    mocker.patch(
        "core.management.commands.load_fixtures.serializers.deserialize",
        return_value=[obj1, obj2, obj3],
    )
    mocker.patch("core.management.commands.load_fixtures.transaction.atomic", return_value=nullcontext())

    cmd.upsert_fixture(str(fixture))

    output = cmd.stdout.getvalue()
    assert "created=1" in output
    assert "updated≈1" in output
    assert "failed=1" in output


def test_load_fixtures_discovers_and_loads_only_eligible(mocker):
    cmd = _command()
    mocker.patch(
        "core.management.commands.load_fixtures.os.walk",
        return_value=[(".", ["fixtures"], [])],
    )
    mocker.patch(
        "core.management.commands.load_fixtures.os.listdir",
        return_value=["a.json", "b.txt", "a.json"],
    )
    mock_should = mocker.patch.object(cmd, "should_load_fixture", side_effect=[True])
    mock_upsert = mocker.patch.object(cmd, "upsert_fixture")

    cmd.load_fixtures()

    assert "Cargando fixtures" in cmd.stdout.getvalue()
    mock_should.assert_called_once()
    mock_upsert.assert_called_once()


def test_load_fixtures_when_none_found(mocker):
    cmd = _command()
    mocker.patch(
        "core.management.commands.load_fixtures.os.walk",
        return_value=[],
    )

    cmd.load_fixtures()

    assert "No se encontraron fixtures" in cmd.stdout.getvalue()
