from types import SimpleNamespace

from admisiones import audit_signals


def test_registrar_alta_admision_delega_en_audittrail(mocker):
    registrar_evento = mocker.patch("admisiones.audit_signals.registrar_evento")
    comedor = SimpleNamespace()
    admision = SimpleNamespace(pk=8, comedor=comedor, estado_mostrar="Activa")

    audit_signals.registrar_alta_admision(None, admision, created=True)

    registrar_evento.assert_called_once_with(
        comedor,
        {"Admisión": [None, "Admisión #8 (Activa)"]},
        audit_signals.ACTION_CREATE,
    )
