import importlib.util
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts/operacion"


@pytest.fixture
def renderer(monkeypatch):
    monkeypatch.syspath_prepend(str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(
        "render_pwa_nginx", SCRIPTS / "render_pwa_nginx.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_active_nginx_exposes_only_legacy_espacios(renderer):
    content = renderer.render(renderer.configuration(SCRIPTS / "pwas.json"))
    assert "location ^~ /mobile/" in content
    assert "127.0.0.1:8080/" in content
    assert "127.0.0.1:8081/" not in content
    assert "127.0.0.1:8082/" not in content
    assert "rewrite ^/mobile/" not in content


def test_new_ready_pwa_routes_keep_suffix_and_query_without_cross_environment_host(
    renderer,
):
    apps = renderer.configuration(SCRIPTS / "pwas.json")
    apps[1]["enabled"] = True
    content = renderer.render(apps)
    assert "rewrite ^/mobile2/(.*)$ /pwa/datacalle/$1 redirect;" in content
    assert "location = /mobile2 { return 302 /pwa/datacalle/$is_args$args; }" in content
    assert "location ^~ /pwa/datacalle/" in content
    assert "https://" not in content  # Location uses the current environment.


def test_espacios_migration_cannot_be_activated_accidentally(renderer):
    apps = renderer.configuration(SCRIPTS / "pwas.json")
    apps[0]["base_path"] = apps[0]["canonical_path"]
    with pytest.raises(ValueError, match="service worker"):
        renderer.render(apps)


def test_preview_is_marked_and_not_the_active_include(renderer):
    content = renderer.render(
        renderer.configuration(SCRIPTS / "pwas.json"), preview=True
    )
    assert "PREVIEW ONLY" in content
    for path in ("espacioscomunitarios", "datacalle", "gestionar"):
        assert f"location ^~ /pwa/{path}/" in content
