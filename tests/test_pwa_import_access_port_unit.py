import pytest

from users import pwa_import_access


def test_resolver_accesos_pwa_importacion_requiere_proveedor(monkeypatch):
    monkeypatch.setattr(pwa_import_access, "_resolver", None)

    with pytest.raises(RuntimeError, match="No hay un resolvedor"):
        pwa_import_access.resolver_accesos_pwa_importacion("1", "2")


def test_resolver_accesos_pwa_importacion_delega_en_proveedor(monkeypatch):
    esperado = pwa_import_access.SeleccionAccesosPWAImportacion(
        organizacion_ids=(1,),
        comedor_ids=(2,),
    )
    monkeypatch.setattr(pwa_import_access, "_resolver", lambda *_: esperado)

    assert pwa_import_access.resolver_accesos_pwa_importacion("1", "2") == esperado
