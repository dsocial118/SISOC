from types import SimpleNamespace

from comedores import audit_signals


def test_registrar_alta_imagen_delega_en_audittrail(mocker):
    registrar_evento = mocker.patch("comedores.audit_signals.registrar_evento")
    comedor = SimpleNamespace()
    imagen = SimpleNamespace(comedor=comedor, imagen=SimpleNamespace(name="foto.png"))

    audit_signals.registrar_cambios_imagen_comedor(None, imagen, created=True)

    registrar_evento.assert_called_once_with(
        comedor,
        {"Imagen": [None, "foto.png"]},
        audit_signals.ACTION_CREATE,
    )


def test_registrar_baja_imagen_delega_en_audittrail(mocker):
    registrar_evento = mocker.patch("comedores.audit_signals.registrar_evento")
    comedor = SimpleNamespace()
    imagen = SimpleNamespace(comedor=comedor, imagen=SimpleNamespace(name="foto.png"))

    audit_signals.registrar_baja_imagen_comedor(None, imagen)

    registrar_evento.assert_called_once_with(
        comedor,
        {"Imagen": ["foto.png", "Eliminada"]},
        audit_signals.ACTION_DELETE,
    )
