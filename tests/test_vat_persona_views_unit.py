from decimal import Decimal
from types import SimpleNamespace

from VAT.views import persona as persona_views
from VAT.services.inscripcion_service import InscripcionService
from VAT.services.voucher_service.impl import VoucherService


class _QuerySetStub:
    def __init__(self, items):
        self._items = list(items)

    def filter(self, **_kwargs):
        return self

    def order_by(self, *_args, **_kwargs):
        return self

    def first(self):
        return self._items[0] if self._items else None

    def exists(self):
        return bool(self._items)

    def count(self):
        return len(self._items)

    def __iter__(self):
        return iter(self._items)


def test_inscripcion_create_descuenta_costo_del_voucher(mocker):
    view = persona_views.InscripcionCreateView()
    view.request = SimpleNamespace(user=SimpleNamespace(id=9, is_authenticated=True))

    inscripcion = SimpleNamespace(
        ciudadano="Ciudadano Demo",
        estado="inscripta",
        voucher_debito=12500,
        voucher_saldo=12500,
    )
    mocker.patch(
        "VAT.views.persona.InscripcionService.crear_inscripcion",
        return_value=inscripcion,
    )
    success_mock = mocker.patch("VAT.views.persona.messages.success")
    form = SimpleNamespace(
        cleaned_data={
            "ciudadano": SimpleNamespace(id=1),
            "comision": SimpleNamespace(id=2),
            "programa": SimpleNamespace(id=3),
            "estado": "inscripta",
            "origen_canal": "api",
            "observaciones": "",
        }
    )

    response = view.form_valid(form)

    assert response.status_code == 302
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


def test_inscripcion_service_crea_y_debita_voucher(mocker):
    ciudadano = SimpleNamespace(id=1, __str__=lambda self: "Ciudadano Demo")
    programa = SimpleNamespace(id=4, nombre="VAT")
    oferta = SimpleNamespace(
        programa=programa,
        programa_id=4,
        usa_voucher=True,
        costo=Decimal("12500"),
    )
    comision = SimpleNamespace(
        id=6,
        oferta=oferta,
        oferta_id=10,
        cupo_total=1,
        __str__=lambda self: "COM-6",
    )
    voucher = SimpleNamespace(cantidad_disponible=12500, parametria=None)
    inscripcion = SimpleNamespace(
        id=8,
        comision_id=6,
        comision_curso_id=None,
        comision=comision,
        entidad_comision=comision,
    )

    mocker.patch(
        "VAT.services.inscripcion_service.Inscripcion.objects.create",
        return_value=inscripcion,
    )
    mocker.patch(
        "VAT.services.inscripcion_service.Inscripcion.objects.filter",
        return_value=_QuerySetStub([]),
    )
    mocker.patch(
        "VAT.services.inscripcion_service.Voucher.objects.select_related",
        return_value=_QuerySetStub([voucher]),
    )
    debitar_mock = mocker.patch(
        "VAT.services.inscripcion_service.VoucherService.debitar_voucher",
        return_value=(True, "ok"),
    )

    result = InscripcionService.crear_inscripcion(
        ciudadano=ciudadano,
        comision=comision,
        programa=programa,
        usuario=SimpleNamespace(is_authenticated=True),
    )

    assert result is inscripcion
    assert debitar_mock.call_args.kwargs["cantidad"] == 12500
