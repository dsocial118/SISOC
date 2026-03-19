import json
from pathlib import Path


def test_subintervencion_fixture_no_contiene_nombres_vacios():
    path = Path("intervenciones/fixtures/subintervencion_tipointervencion.json")
    data = json.loads(path.read_text())

    vacios = [
        obj["pk"]
        for obj in data
        if not (obj.get("fields", {}).get("nombre") or "").strip()
    ]

    assert vacios == []
