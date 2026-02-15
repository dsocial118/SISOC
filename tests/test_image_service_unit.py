"""Tests for test image service unit."""

from pathlib import Path

from PIL import Image

from core.services.image_service import (
    _convert_to_webp,
    _get_absolute_path,
    _get_webp_path,
    clear_webp_cache,
    get_image_info,
    get_or_create_webp,
)


def _create_image(path: Path, mode: str = "RGB", color=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new(mode, (10, 10), color=color or (255, 0, 0))
    image.save(path, format="PNG" if path.suffix.lower() == ".png" else "JPEG")


def test_get_or_create_webp_empty_or_unsupported_returns_original():
    assert get_or_create_webp("") == ""
    assert get_or_create_webp("foto.gif") == "foto.gif"


def test_get_or_create_webp_returns_original_when_missing_file(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path

    assert get_or_create_webp("missing.jpg") == "missing.jpg"


def test_get_or_create_webp_uses_cache_hit(settings, tmp_path, mocker):
    settings.MEDIA_ROOT = tmp_path
    original = tmp_path / "a" / "b" / "foto.jpg"
    _create_image(original)
    mocker.patch("core.services.image_service.cache.get", return_value=True)
    cache_set = mocker.patch("core.services.image_service.cache.set")
    convert = mocker.patch("core.services.image_service._convert_to_webp")
    image_path = "a/b/foto.jpg"

    result = get_or_create_webp(image_path)

    assert result == "a/b/foto.webp"
    cache_set.assert_not_called()
    convert.assert_not_called()


def test_get_or_create_webp_reuses_existing_webp(settings, tmp_path, mocker):
    settings.MEDIA_ROOT = tmp_path
    original = tmp_path / "a" / "foto.jpg"
    webp = tmp_path / "a" / "foto.webp"
    _create_image(original)
    webp.parent.mkdir(parents=True, exist_ok=True)
    webp.write_bytes(b"x")
    mocker.patch("core.services.image_service.cache.get", return_value=False)
    cache_set = mocker.patch("core.services.image_service.cache.set")

    result = get_or_create_webp("a/foto.jpg")

    assert result == "a/foto.webp"
    cache_set.assert_called_once()


def test_get_or_create_webp_converts_when_missing_webp(settings, tmp_path, mocker):
    settings.MEDIA_ROOT = tmp_path
    original = tmp_path / "a" / "foto.jpg"
    _create_image(original)
    mocker.patch("core.services.image_service.cache.get", return_value=False)
    mocker.patch("core.services.image_service._convert_to_webp", return_value=True)

    result = get_or_create_webp("a/foto.jpg")

    assert result == "a/foto.webp"


def test_get_or_create_webp_returns_original_when_conversion_fails(settings, tmp_path, mocker):
    settings.MEDIA_ROOT = tmp_path
    original = tmp_path / "a" / "foto.jpg"
    _create_image(original)
    mocker.patch("core.services.image_service.cache.get", return_value=False)
    mocker.patch("core.services.image_service._convert_to_webp", return_value=False)

    result = get_or_create_webp("a/foto.jpg")

    assert result == "a/foto.jpg"


def test_get_or_create_webp_handles_unexpected_exception(mocker):
    mocker.patch("core.services.image_service._get_absolute_path", side_effect=RuntimeError)

    assert get_or_create_webp("a/foto.jpg") == "a/foto.jpg"


def test_convert_to_webp_creates_non_empty_file(tmp_path):
    input_path = tmp_path / "in.png"
    output_path = tmp_path / "out" / "image.webp"
    _create_image(input_path, mode="P")

    assert _convert_to_webp(str(input_path), str(output_path), quality=80) is True
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_convert_to_webp_handles_rgba_l_and_other_modes(tmp_path):
    rgba_path = tmp_path / "rgba.png"
    l_path = tmp_path / "l.png"
    cmyk_path = tmp_path / "cmyk.jpg"
    _create_image(rgba_path, mode="RGBA", color=(255, 0, 0, 128))
    Image.new("L", (10, 10), color=120).save(l_path, format="PNG")
    Image.new("CMYK", (10, 10), color=(0, 0, 0, 0)).save(cmyk_path, format="JPEG")

    assert _convert_to_webp(str(rgba_path), str(tmp_path / "rgba.webp"), quality=80) is True
    assert _convert_to_webp(str(l_path), str(tmp_path / "l.webp"), quality=80) is True
    assert _convert_to_webp(str(cmyk_path), str(tmp_path / "cmyk.webp"), quality=80) is True


def test_convert_to_webp_returns_false_when_output_is_empty(tmp_path, mocker):
    input_path = tmp_path / "in.png"
    output_path = tmp_path / "out.webp"
    _create_image(input_path)
    mocker.patch("core.services.image_service.os.path.getsize", return_value=0)

    assert _convert_to_webp(str(input_path), str(output_path), quality=80) is False


def test_convert_to_webp_cleans_partial_file_on_error(mocker, tmp_path):
    output_path = tmp_path / "out.webp"
    output_path.write_bytes(b"partial")
    mocker.patch("core.services.image_service.Image.open", side_effect=RuntimeError("boom"))
    removed = {}

    def _remove(path):
        removed["path"] = path
        output_path.unlink(missing_ok=True)

    mocker.patch("core.services.image_service.os.remove", side_effect=_remove)

    assert _convert_to_webp("in.jpg", str(output_path), quality=80) is False
    assert removed["path"] == str(output_path)


def test_convert_to_webp_logs_cleanup_error(mocker, tmp_path):
    output_path = tmp_path / "out.webp"
    output_path.write_bytes(b"partial")
    mocker.patch("core.services.image_service.Image.open", side_effect=RuntimeError("boom"))
    mocker.patch("core.services.image_service.os.remove", side_effect=OSError("nope"))

    assert _convert_to_webp("in.jpg", str(output_path), quality=80) is False


def test_get_absolute_path_variants(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    settings.MEDIA_URL = "/media/"
    abs_path = "/tmp/file.jpg"

    assert _get_absolute_path(abs_path) == abs_path
    assert _get_absolute_path("/media/a/b.jpg") == str(tmp_path / "a" / "b.jpg")
    assert _get_absolute_path("http://host/media/a/b.jpg") == str(tmp_path / "a" / "b.jpg")
    assert _get_absolute_path("a/b.jpg") == str(tmp_path / "a" / "b.jpg")


def test_get_absolute_path_empty_returns_empty():
    assert _get_absolute_path("") == ""


def test_get_webp_path_changes_suffix():
    assert _get_webp_path("a/b/foto.jpg") == "a/b/foto.webp"


def test_get_image_info_returns_none_when_missing(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path

    assert get_image_info("missing.jpg") is None


def test_get_image_info_handles_exception(mocker):
    mocker.patch("core.services.image_service._get_absolute_path", side_effect=RuntimeError)

    assert get_image_info("broken.jpg") is None


def test_get_image_info_includes_webp_savings(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    original = tmp_path / "a" / "foto.jpg"
    webp = tmp_path / "a" / "foto.webp"
    _create_image(original)
    webp.parent.mkdir(parents=True, exist_ok=True)
    webp.write_bytes(b"x")

    info = get_image_info("a/foto.jpg")

    assert info is not None
    assert info["has_webp"] is True
    assert "savings_bytes" in info
    assert "savings_percent" in info


def test_clear_webp_cache_for_single_image_and_global(mocker, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    settings.MEDIA_URL = "/media/"
    delete = mocker.patch("core.services.image_service.cache.delete")
    clear = mocker.patch("core.services.image_service.cache.clear")

    clear_webp_cache("/media/a/foto.jpg")
    clear_webp_cache()

    delete.assert_called_once()
    clear.assert_called_once()
