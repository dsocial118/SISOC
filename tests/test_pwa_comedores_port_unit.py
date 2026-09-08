import pytest

from users import pwa_comedores


def test_es_comedor_alimentar_comunidad_no_consulta_sin_id(monkeypatch):
    monkeypatch.setattr(pwa_comedores, "_es_alimentar_comunidad", None)

    assert pwa_comedores.es_comedor_alimentar_comunidad(None) is False


def test_es_comedor_alimentar_comunidad_requiere_capacidad(monkeypatch):
    monkeypatch.setattr(pwa_comedores, "_es_alimentar_comunidad", None)

    with pytest.raises(RuntimeError, match="No hay una capacidad"):
        pwa_comedores.es_comedor_alimentar_comunidad(1)


def test_es_comedor_alimentar_comunidad_delega_en_comedores(monkeypatch):
    monkeypatch.setattr(pwa_comedores, "_es_alimentar_comunidad", lambda _id: True)

    assert pwa_comedores.es_comedor_alimentar_comunidad(1) is True
