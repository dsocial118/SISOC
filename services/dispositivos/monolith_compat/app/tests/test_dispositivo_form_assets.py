from pathlib import Path


def test_dispositivo_form_bindings_include_click_for_collapsible_sections():
    asset_path = (
        Path(__file__).resolve().parents[2]
        / "static"
        / "custom"
        / "js"
        / "dispositivoFormModerno.js"
    )
    content = asset_path.read_text(encoding="utf-8")

    assert 'header.addEventListener("keydown"' in content
    assert 'header.addEventListener("click"' in content
