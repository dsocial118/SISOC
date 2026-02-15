from io import StringIO

import pytest
from django.core.management.base import CommandError

from core.management.commands.generate_webp_images import Command


class FakeQuerySet:
    def __init__(self, items):
        self._items = list(items)

    def exclude(self, **_kwargs):
        return self

    def count(self):
        return len(self._items)

    def __iter__(self):
        return iter(self._items)

    def __getitem__(self, item):
        if isinstance(item, slice):
            return FakeQuerySet(self._items[item])
        return self._items[item]


def _command():
    cmd = Command()
    cmd.stdout = StringIO()
    cmd.stderr = StringIO()
    return cmd


def test_handle_rejects_invalid_quality():
    cmd = _command()

    with pytest.raises(CommandError):
        cmd.handle(quality=101, app=None, model=None, limit=None, dry_run=False, stats=False)


def test_handle_when_no_image_fields(mocker):
    cmd = _command()
    mocker.patch.object(cmd, "_find_image_fields", return_value=[])

    cmd.handle(quality=85, app=None, model=None, limit=None, dry_run=False, stats=False)

    assert "No se encontraron ImageFields" in cmd.stdout.getvalue()


def test_handle_dry_run_with_count_zero(mocker):
    cmd = _command()
    model_class = mocker.Mock()
    queryset = mocker.Mock()
    manager_qs = mocker.Mock()
    model_class.__name__ = "ModelA"
    model_class.objects.exclude.return_value = manager_qs
    manager_qs.exclude.return_value = queryset
    queryset.count.return_value = 0
    mocker.patch.object(cmd, "_find_image_fields", return_value=[("app", model_class, "imagen")])
    mocker.patch("core.management.commands.generate_webp_images.tqdm", side_effect=lambda x, **_: x)

    cmd.handle(quality=85, app=None, model=None, limit=None, dry_run=True, stats=False)

    out = cmd.stdout.getvalue()
    assert "Modo DRY RUN" in out
    assert "Sin imágenes, saltando" in out


def test_handle_processes_success_skipped_and_error(mocker):
    cmd = _command()
    instance_ok = type("InstOk", (), {"imagen": None})()
    instance_skip = type("InstSkip", (), {"imagen": None})()

    instance_err = type("InstErr", (), {"imagen": None})()

    class ImageObj:
        def __init__(self, url):
            self.url = url

        def __bool__(self):
            return True

    instance_ok.imagen = ImageObj("/media/a.jpg")
    instance_skip.imagen = ImageObj("/media/b.jpg")
    instance_err.imagen = ImageObj("/media/c.jpg")

    model_class = mocker.Mock()
    model_class.__name__ = "ModelB"
    queryset = FakeQuerySet([instance_ok, instance_skip, instance_err])
    model_class.objects.exclude.return_value = queryset
    mocker.patch.object(cmd, "_find_image_fields", return_value=[("app", model_class, "imagen")])
    mocker.patch("core.management.commands.generate_webp_images.tqdm", side_effect=lambda x, **_: x)
    mocker.patch(
        "core.management.commands.generate_webp_images.get_or_create_webp",
        side_effect=["/media/a.webp", "/media/b.jpg", RuntimeError("fail")],
    )

    cmd.handle(quality=85, app=None, model=None, limit=None, dry_run=False, stats=False)

    out = cmd.stdout.getvalue()
    assert "Total procesadas: 2" in out
    assert "Exitosas: 1" in out
    assert "Omitidas: 1" in out
    assert "Errores: 1" in out


def test_handle_with_stats_uses_size_summary(mocker):
    cmd = _command()
    instance = type("Inst", (), {"imagen": None})()

    class ImageObj:
        url = "/media/a.jpg"

        def __bool__(self):
            return True

    model_class = mocker.Mock()
    model_class.__name__ = "ModelC"
    queryset = FakeQuerySet([instance])
    model_class.objects.exclude.return_value = queryset
    mocker.patch.object(cmd, "_find_image_fields", return_value=[("app", model_class, "imagen")])
    mocker.patch("core.management.commands.generate_webp_images.tqdm", side_effect=lambda x, **_: x)
    instance.imagen = ImageObj()
    mocker.patch(
        "core.management.commands.generate_webp_images.get_image_info",
        side_effect=[
            {"file_size": 1000, "has_webp": False},
            {"file_size": 1000, "has_webp": True, "webp_size": 700},
        ],
    )
    mocker.patch(
        "core.management.commands.generate_webp_images.get_or_create_webp",
        return_value="/media/a.webp",
    )

    cmd.handle(quality=85, app=None, model=None, limit=None, dry_run=False, stats=True)

    out = cmd.stdout.getvalue()
    assert "AHORRO DE ESPACIO" in out
    assert "Ahorro:" in out


def test_find_image_fields_with_invalid_app_raises():
    cmd = _command()

    with pytest.raises(CommandError):
        cmd._find_image_fields(app_name="nope")


def test_find_image_fields_filters_model_and_detects_image_fields(mocker):
    cmd = _command()
    image_field = mocker.Mock()
    from django.db.models import ImageField

    image_field.__class__ = ImageField
    model_a = mocker.Mock()
    model_a.__name__ = "Target"
    model_a._meta.get_fields.return_value = [image_field]
    app_config = mocker.Mock()
    app_config.label = "appx"
    app_config.get_models.return_value = [model_a]
    mocker.patch("core.management.commands.generate_webp_images.apps.get_app_configs", return_value=[app_config])

    result = cmd._find_image_fields(model_name="Target")

    assert result == [("appx", model_a, image_field.name)]


def test_format_bytes_units():
    cmd = _command()
    assert cmd._format_bytes(10).endswith("B")
    assert cmd._format_bytes(1024).endswith("KB")
    assert cmd._format_bytes(1024 * 1024).endswith("MB")
