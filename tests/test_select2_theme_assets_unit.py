"""Regresiones unitarias para la carga y alcance del tema global de Select2."""

from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (_repo_root() / relative_path).read_text(encoding="utf-8")


def test_select2_theme_se_carga_en_las_bases_compartidas():
    assert "custom/css/select2_theme.css" in _read("templates/includes/base.html")
    assert "custom/css/select2_theme.css" in _read("templates/includes/new_base.html")


def test_select2_theme_cubre_variantes_bootstrap():
    content = _read("static/custom/css/select2_theme.css")

    assert ".select2-container--default" in content
    assert ".select2-container--bootstrap4" in content
    assert ".select2-container--bootstrap5" in content


def test_templates_migrados_no_cargan_override_legacy_de_select2():
    templates = (
        "users/templates/group/group_form.html",
        "users/templates/user/user_form.html",
        "relevamientos/templates/relevamiento_form.html",
    )

    for template_path in templates:
        assert "admin/css/select2templated.css" not in _read(template_path)
