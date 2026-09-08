from datetime import date
from types import SimpleNamespace

from relevamientos import audit_signals


def test_registrar_alta_relevamiento_delega_en_audittrail(mocker):
    registrar_evento = mocker.patch("relevamientos.audit_signals.registrar_evento")
    comedor = SimpleNamespace()
    relevamiento = SimpleNamespace(
        pk=4,
        comedor=comedor,
        fecha_visita=date(2026, 8, 12),
    )

    audit_signals.registrar_alta_relevamiento(None, relevamiento, created=True)

    registrar_evento.assert_called_once_with(
        comedor,
        {"Relevamiento": [None, "Relevamiento #4 - 2026-08-12"]},
        audit_signals.ACTION_CREATE,
    )
