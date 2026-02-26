"""Regresiones de templates de ciudadanos."""

from pathlib import Path


def test_ciudadano_detail_template_incluye_accion_eliminar():
    repo_root = Path(__file__).resolve().parents[1]
    template_path = repo_root / "ciudadanos" / "templates" / "ciudadanos" / "ciudadano_detail.html"

    content = template_path.read_text(encoding="utf-8")

    assert "ciudadanos_eliminar" in content
