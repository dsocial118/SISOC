import pytest

from users import form_catalogs


def test_obtener_queryset_formulario_requiere_provider(monkeypatch):
    monkeypatch.setattr(form_catalogs, "_providers", {})

    with pytest.raises(RuntimeError, match="No hay un queryset"):
        form_catalogs.obtener_queryset_formulario("duplas_asignadas")


def test_obtener_queryset_formulario_delega_en_el_provider(monkeypatch):
    monkeypatch.setattr(form_catalogs, "_providers", {})
    expected = object()
    form_catalogs.registrar_queryset_formulario("duplas_asignadas", lambda: expected)

    assert form_catalogs.obtener_queryset_formulario("duplas_asignadas") is expected
