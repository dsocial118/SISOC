"""Tests for test pago service unit."""

from io import BytesIO
from types import SimpleNamespace

import pandas as pd
import pytest
from django.core.exceptions import ValidationError

from celiaquia.services import pago_service as module

pytestmark = pytest.mark.django_db


def test_norm_digits_and_leer_tabla_fallbacks(mocker):
    assert module._norm_digits("20-123") == "20123"

    class F:
        def open(self):
            return None

        def read(self):
            return b"a,b\n1,2\n"

        def seek(self, _):
            return None

    mocker.patch(
        "celiaquia.services.pago_service.pd.read_excel", side_effect=Exception("x")
    )
    df = module._leer_tabla(F())
    assert list(df.columns) == ["a", "b"]


def test_qs_consolidado_activo_filters(mocker):
    qs = SimpleNamespace(filter=lambda **kwargs: ("ok", kwargs))
    mocker.patch(
        "celiaquia.services.pago_service.ExpedienteCiudadano.objects.select_related",
        return_value=qs,
    )
    out = module.PagoService._qs_consolidado_activo("P")
    assert out[0] == "ok"
    assert out[1]["estado_cupo"] == module.EstadoCupo.DENTRO


def test_crear_expediente_pago_generates_file_and_updates_state(mocker):
    pago = SimpleNamespace(
        pk=1,
        total_candidatos=0,
        archivo_envio=SimpleNamespace(save=mocker.Mock()),
        estado=None,
        save=mocker.Mock(),
    )
    mocker.patch(
        "celiaquia.services.pago_service.PagoExpediente.objects.create",
        return_value=pago,
    )

    leg = SimpleNamespace(
        ciudadano=SimpleNamespace(
            documento="123", cuil="20-12345678-3", nombre="A", apellido="B"
        ),
        expediente_id=9,
    )
    mocker.patch.object(
        module.PagoService, "_qs_consolidado_activo", return_value=[leg]
    )

    out = module.PagoService.crear_expediente_pago(
        provincia=SimpleNamespace(id=2), usuario="u", periodo="2026-01"
    )
    assert out is pago
    assert pago.total_candidatos == 1
    pago.archivo_envio.save.assert_called_once()
    pago.save.assert_called_once()


def test_procesar_respuesta_validations_and_processing(mocker):
    pago = SimpleNamespace(
        pk=1,
        provincia="P",
        estado=module.PagoEstado.ENVIADO,
        total_candidatos=2,
        save=mocker.Mock(),
    )

    with pytest.raises(ValidationError):
        module.PagoService.procesar_respuesta(
            pago=SimpleNamespace(estado="X"), archivo_respuesta=None, usuario="u"
        )

    mocker.patch(
        "celiaquia.services.pago_service._leer_tabla",
        return_value=pd.DataFrame({"x": [1]}),
    )
    with pytest.raises(ValidationError):
        module.PagoService.procesar_respuesta(
            pago=pago, archivo_respuesta=BytesIO(b"x"), usuario="u"
        )

    mocker.patch(
        "celiaquia.services.pago_service._leer_tabla",
        return_value=pd.DataFrame({"dni": ["", None]}),
    )
    with pytest.raises(ValidationError):
        module.PagoService.procesar_respuesta(
            pago=pago, archivo_respuesta=BytesIO(b"x"), usuario="u"
        )

    leg1 = SimpleNamespace(
        ciudadano=SimpleNamespace(documento="123", nombre="A", apellido="B"),
        pk=1,
        observacion_cruce=None,
        save=mocker.Mock(),
    )
    leg2 = SimpleNamespace(
        ciudadano=SimpleNamespace(documento="999", nombre="C", apellido="D"),
        pk=2,
        observacion_cruce=None,
        save=mocker.Mock(),
    )
    mocker.patch(
        "celiaquia.services.pago_service._leer_tabla",
        return_value=pd.DataFrame({"dni": ["123"]}),
    )
    mocker.patch.object(
        module.PagoService, "_qs_consolidado_activo", return_value=[leg1, leg2]
    )
    mocker.patch(
        "celiaquia.services.pago_service.PagoNomina.objects.get_or_create",
        return_value=(object(), True),
    )
    mocker.patch(
        "celiaquia.services.pago_service.CupoService.suspender_slot", return_value=True
    )

    result = module.PagoService.procesar_respuesta(
        pago=pago, archivo_respuesta=BytesIO(b"x"), usuario="u"
    )
    assert result["validados"] == 1
    assert result["excluidos"] == 1
    assert pago.save.called


def test_exportar_nomina_actual_excel(mocker):
    leg = SimpleNamespace(
        ciudadano=SimpleNamespace(
            documento="123", cuil="20-12345678-3", nombre="A", apellido="B"
        ),
        expediente_id=9,
    )
    mocker.patch.object(
        module.PagoService, "_qs_consolidado_activo", return_value=[leg]
    )
    out = module.PagoService.exportar_nomina_actual_excel(provincia="P")
    assert isinstance(out, (bytes, bytearray))
    assert len(out) > 0
