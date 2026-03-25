from decimal import Decimal
from types import SimpleNamespace

from VAT.views import persona as persona_views
from VAT.services.voucher_service.impl import VoucherService


def test_inscripcion_create_descuenta_costo_del_voucher(mocker):
    view = persona_views.InscripcionCreateView()
    view.request = SimpleNamespace(user=SimpleNamespace(id=9))

    programa = SimpleNamespace(id=1)
    oferta = SimpleNamespace(
        usa_voucher=True,
        programa=programa,
        programa_id=1,
        costo=Decimal("12500"),
    )
    comision = SimpleNamespace(oferta=oferta)
    inscripcion = SimpleNamespace(
        id=5,
        comision=comision,
        comision_id=7,
        programa_id=1,
        ciudadano="Ciudadano Demo",
    )

    def fake_super_form_valid(self, form):
        self.object = inscripcion
        return "ok"

    mocker.patch(
        "django.views.generic.edit.ModelFormMixin.form_valid",
        side_effect=fake_super_form_valid,
    )

    voucher = SimpleNamespace(cantidad_disponible=12500)
    mocker.patch(
        "VAT.views.persona.Voucher.objects.filter",
        return_value=SimpleNamespace(
            order_by=lambda *a, **k: SimpleNamespace(first=lambda: voucher)
        ),
    )
    debitar_mock = mocker.patch(
        "VAT.views.persona.VoucherService.debitar_voucher",
        return_value=(True, "ok"),
    )
    success_mock = mocker.patch("VAT.views.persona.messages.success")

    response = view.form_valid(SimpleNamespace())

    assert response == "ok"
    debitar_mock.assert_called_once()
    assert debitar_mock.call_args.kwargs["cantidad"] == 12500
    assert success_mock.called


def test_voucher_service_debitar_voucher_actualiza_saldo(mocker):
    voucher = SimpleNamespace(
        id=4,
        estado="activo",
        cantidad_disponible=25000,
        cantidad_usada=0,
        save=mocker.Mock(),
    )
    usuario = SimpleNamespace(id=1)

    mocker.patch(
        "VAT.services.voucher_service.impl.VoucherService.validar_vencimiento",
        return_value=(True, "Voucher vigente"),
    )
    log_create = mocker.patch(
        "VAT.services.voucher_service.impl.VoucherLog.objects.create"
    )

    ok, _msg = VoucherService.debitar_voucher(
        voucher=voucher,
        cantidad=12500,
        usuario=usuario,
        detalles={"origen": "test"},
    )

    assert ok is True
    assert voucher.cantidad_usada == 12500
    assert voucher.cantidad_disponible == 12500
    voucher.save.assert_called_once()
    log_create.assert_called_once()
