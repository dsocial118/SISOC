from datetime import date

from expedientespagos.forms import ExpedientePagoForm
from expedientespagos.models import ExpedientePago


def test_expediente_pago_form_renderiza_fecha_acreditacion_inicial():
    expediente = ExpedientePago(
        expediente_convenio="EX-2025-FECHA",
        fecha_pago_al_banco=date(2025, 2, 10),
        fecha_acreditacion=date(2025, 2, 20),
        prestaciones_mensuales_desayuno=0,
        prestaciones_mensuales_almuerzo=0,
        prestaciones_mensuales_merienda=0,
        prestaciones_mensuales_cena=0,
        monto_mensual_desayuno=0,
        monto_mensual_almuerzo=0,
        monto_mensual_merienda=0,
        monto_mensual_cena=0,
    )

    form = ExpedientePagoForm(instance=expediente)
    fecha_pago_html = form["fecha_pago_al_banco"].as_widget()
    fecha_acreditacion_html = form["fecha_acreditacion"].as_widget()

    assert 'name="fecha_pago_al_banco"' in fecha_pago_html
    assert 'value="2025-02-10"' in fecha_pago_html
    assert 'name="fecha_acreditacion"' in fecha_acreditacion_html
    assert 'value="2025-02-20"' in fecha_acreditacion_html
