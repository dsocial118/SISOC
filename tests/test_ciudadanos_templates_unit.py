"""Regresiones de templates de ciudadanos."""

from pathlib import Path


def test_ciudadano_detail_template_incluye_accion_eliminar():
    repo_root = Path(__file__).resolve().parents[1]
    template_path = (
        repo_root / "ciudadanos" / "templates" / "ciudadanos" / "ciudadano_detail.html"
    )

    content = template_path.read_text(encoding="utf-8")

    assert "ciudadanos_eliminar" in content


def test_ciudadano_detail_template_usa_admision_comedor_con_guardas():
    repo_root = Path(__file__).resolve().parents[1]
    template_path = (
        repo_root / "ciudadanos" / "templates" / "ciudadanos" / "ciudadano_detail.html"
    )

    content = template_path.read_text(encoding="utf-8")

    assert "nomina_actual.admision.comedor" in content
    assert "nomina.admision.comedor" in content
    assert "nomina_actual.comedor.id" not in content
    assert "nomina.comedor.id" not in content


def test_ciudadano_detail_template_incluye_pestana_vat():
    repo_root = Path(__file__).resolve().parents[1]
    template_path = (
        repo_root / "ciudadanos" / "templates" / "ciudadanos" / "ciudadano_detail.html"
    )

    content = template_path.read_text(encoding="utf-8")

    assert 'href="#vat"' in content
    assert 'id="vat"' in content
    assert "Cursos asignados" in content
    assert "Créditos actuales" in content
