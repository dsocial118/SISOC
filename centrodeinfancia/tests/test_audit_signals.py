from datetime import date
from types import SimpleNamespace

from centrodeinfancia import signals


def test_registrar_alta_nomina_delega_evento_al_contrato_publico(mocker):
    registrar_evento = mocker.patch("centrodeinfancia.signals.registrar_evento")
    centro = SimpleNamespace()
    instancia = SimpleNamespace(pk=10, centro=centro, ciudadano_id=None)

    signals.registrar_alta_nomina(None, instancia, created=True)

    registrar_evento.assert_called_once_with(
        centro,
        {"Nómina": [None, "Nómina #10"]},
        signals.ACTION_CREATE,
    )


def test_registrar_alta_formulario_conserva_fecha(mocker):
    registrar_evento = mocker.patch("centrodeinfancia.signals.registrar_evento")
    centro = SimpleNamespace()
    instancia = SimpleNamespace(
        pk=4,
        centro=centro,
        fecha_relevamiento=date(2026, 8, 11),
    )

    signals.registrar_alta_formulario(None, instancia, created=True)

    registrar_evento.assert_called_once_with(
        centro,
        {"Formulario CDI": [None, "Formulario CDI #4 - 2026-08-11"]},
        signals.ACTION_CREATE,
    )
