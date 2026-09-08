from types import SimpleNamespace

from intervenciones import audit_signals


def test_registrar_alta_intervencion_delega_en_audittrail(mocker):
    registrar_evento = mocker.patch("intervenciones.audit_signals.registrar_evento")
    comedor = SimpleNamespace()
    intervencion = SimpleNamespace(
        pk=3,
        comedor=comedor,
        tipo_intervencion="Territorial",
    )

    audit_signals.registrar_alta_intervencion(None, intervencion, created=True)

    registrar_evento.assert_called_once_with(
        comedor,
        {"Intervención": [None, "Intervención #3 - Territorial"]},
        audit_signals.ACTION_CREATE,
    )
