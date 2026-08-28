from pathlib import Path


def _repo_root() -> Path:
    asset_relative_path = Path("static/custom/js/dispositivoFormModerno.js")
    for ancestor in Path(__file__).resolve().parents:
        if (ancestor / asset_relative_path).is_file():
            return ancestor
    raise FileNotFoundError(asset_relative_path)


def test_dispositivo_form_bindings_include_click_for_collapsible_sections():
    asset_path = _repo_root() / "static/custom/js/dispositivoFormModerno.js"
    content = asset_path.read_text(encoding="utf-8")

    assert 'header.addEventListener("keydown"' in content
    assert 'header.addEventListener("click"' in content
