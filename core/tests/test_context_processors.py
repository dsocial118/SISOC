from core.context_processors import _build_footer_version_label


def test_build_footer_version_label_formatea_fecha_de_release():
    assert _build_footer_version_label("06.04.2026") == "v06.04.26"


def test_build_footer_version_label_devuelve_fallback_si_formato_invalido():
    assert _build_footer_version_label("desconocida") == "Versiones"
