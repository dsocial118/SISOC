"""Tests for test image tags unit."""

from types import SimpleNamespace

from core.templatetags.image_tags import (
    image_info,
    optimized_image,
    picture_tag,
    webp_exists,
    webp_url,
)


def test_optimized_image_returns_empty_when_missing():
    assert optimized_image(None) == ""


def test_optimized_image_returns_empty_when_url_is_blank():
    assert optimized_image(SimpleNamespace(url="")) == ""


def test_optimized_image_renders_picture_with_webp(mocker):
    mocker.patch(
        "core.templatetags.image_tags.get_or_create_webp", return_value="/media/a.webp"
    )
    image = SimpleNamespace(url="/media/a.jpg")

    html = optimized_image(
        image,
        alt_text="Foto",
        css_class="img-fluid",
        loading="lazy",
        width="100",
        height=50,
        extra_attrs='data-x="1"',
    )

    assert "<picture>" in html
    assert 'type="image/webp"' in html
    assert 'src="/media/a.jpg"' in html
    assert 'loading="lazy"' in html
    assert 'width="100"' in html
    assert 'height="50"' in html


def test_optimized_image_renders_img_fallback_when_no_webp(mocker):
    mocker.patch(
        "core.templatetags.image_tags.get_or_create_webp", return_value="/media/a.jpg"
    )

    html = optimized_image("/media/a.jpg", alt_text="A")

    assert "<picture>" not in html
    assert '<img src="/media/a.jpg"' in html


def test_optimized_image_ignores_invalid_dimensions(mocker):
    mocker.patch(
        "core.templatetags.image_tags.get_or_create_webp", return_value="/media/a.jpg"
    )

    html = optimized_image("/media/a.jpg", width="abc", height="xyz")

    assert "width=" not in html
    assert "height=" not in html


def test_optimized_image_exception_fallback_with_url(mocker):
    mocker.patch(
        "core.templatetags.image_tags.get_or_create_webp", side_effect=RuntimeError
    )
    image = SimpleNamespace(url="/media/a.jpg")

    html = optimized_image(image, alt_text="A", css_class="c")

    assert '<img src="/media/a.jpg"' in html
    assert 'class="c"' in html


def test_optimized_image_exception_without_url_returns_empty(mocker):
    class FailingImage:
        @property
        def url(self):
            raise RuntimeError("boom")

    mocker.patch(
        "core.templatetags.image_tags.get_or_create_webp", side_effect=RuntimeError
    )

    assert optimized_image(FailingImage()) == ""


def test_webp_exists_paths(mocker):
    mocker.patch("core.services.image_service._get_absolute_path", return_value="/tmp/a.jpg")
    mocker.patch("core.services.image_service._get_webp_path", return_value="/tmp/a.webp")
    mock_exists = mocker.patch("os.path.exists", return_value=True)

    assert webp_exists(SimpleNamespace(url="/media/a.jpg")) is True
    assert mock_exists.called


def test_webp_exists_handles_empty_and_exception(mocker):
    assert webp_exists(None) is False
    mocker.patch("core.services.image_service._get_absolute_path", side_effect=RuntimeError)

    assert webp_exists("/media/a.jpg") is False


def test_webp_url_branches(mocker):
    mocker.patch("core.templatetags.image_tags.get_or_create_webp", return_value="/media/a.webp")
    assert webp_url("/media/a.jpg") == "/media/a.webp"
    assert webp_url(None) == ""


def test_webp_url_exception_fallback(mocker):
    mocker.patch("core.templatetags.image_tags.get_or_create_webp", side_effect=RuntimeError)
    image = SimpleNamespace(url="/media/a.jpg")

    assert webp_url(image) == "/media/a.jpg"
    assert webp_url("x.jpg") == "x.jpg"


def test_picture_tag_alias(mocker):
    spy = mocker.patch("core.templatetags.image_tags.optimized_image", return_value="ok")

    result = picture_tag("x.jpg", "Alt", css_class="c")

    spy.assert_called_once_with("x.jpg", "Alt", css_class="c")
    assert result == "ok"


def test_image_info_branches(mocker):
    mock_get_info = mocker.patch("core.services.image_service.get_image_info", return_value={"ok": True})

    assert image_info(SimpleNamespace(url="/media/a.jpg")) == {"ok": True}
    assert image_info("x.jpg") == {"ok": True}
    assert image_info(None) is None
    assert mock_get_info.call_count == 2


def test_image_info_exception_returns_none(mocker):
    mocker.patch("core.services.image_service.get_image_info", side_effect=RuntimeError)

    assert image_info("/media/a.jpg") is None
