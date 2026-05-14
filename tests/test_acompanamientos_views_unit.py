"""Tests unitarios para acompanamientos.views."""

from types import SimpleNamespace
from unittest.mock import call

from django.test import RequestFactory

from acompanamientos import views as module


def _call_restaurar_hito_unwrapped(request, comedor_id):
    return module.restaurar_hito.__wrapped__.__wrapped__(
        request,
        comedor_id=comedor_id,
    )


def test_restaurar_hito_usa_admision_id_desde_referer(mocker):
    rf = RequestFactory()
    req = rf.post(
        "/acompanamientos/comedor/5/restaurar-hito/",
        {"campo": "retiro_tarjeta"},
    )
    req.user = SimpleNamespace(is_authenticated=True)
    req.META["HTTP_REFERER"] = (
        "http://testserver/acompanamientos/acompanamiento/5/detalle/?admision_id=9"
    )

    comedor = SimpleNamespace(pk=5)
    hito = SimpleNamespace(retiro_tarjeta=True, save=mocker.Mock())

    get_comedor = mocker.patch(
        "acompanamientos.views.get_object_or_404",
        return_value=comedor,
    )
    obtener_hitos = mocker.patch(
        "acompanamientos.views.AcompanamientoService.obtener_hitos",
        return_value=hito,
    )
    success = mocker.patch("acompanamientos.views.messages.success")
    safe_redirect = mocker.patch(
        "acompanamientos.views.safe_redirect",
        return_value="redir",
    )

    resp = _call_restaurar_hito_unwrapped(req, comedor_id=5)

    assert resp == "redir"
    get_comedor.assert_called_once_with(module.Comedor, pk=5)
    obtener_hitos.assert_called_once_with(comedor, admision_id=9)
    assert hito.retiro_tarjeta is False
    hito.save.assert_called_once()
    success.assert_called_once()
    safe_redirect.assert_called_once()


def test_restaurar_hito_sin_hitos_redirige_con_error(mocker):
    rf = RequestFactory()
    req = rf.post(
        "/acompanamientos/comedor/5/restaurar-hito/",
        {"campo": "retiro_tarjeta", "admision_id": "11"},
    )
    req.user = SimpleNamespace(is_authenticated=True)

    comedor = SimpleNamespace(pk=5)

    mocker.patch("acompanamientos.views.get_object_or_404", return_value=comedor)
    mocker.patch(
        "acompanamientos.views.AcompanamientoService.obtener_hitos",
        return_value=None,
    )
    error = mocker.patch("acompanamientos.views.messages.error")
    safe_redirect = mocker.patch(
        "acompanamientos.views.safe_redirect",
        return_value="redir",
    )

    resp = _call_restaurar_hito_unwrapped(req, comedor_id=5)

    assert resp == "redir"
    error.assert_called_once()
    safe_redirect.assert_called_once()


def test_acompanamiento_detail_view_normaliza_admision_id_y_reusa_el_mismo_scope(
    mocker,
):
    rf = RequestFactory()
    req = rf.get("/acompanamientos/acompanamiento/5/detalle/?admision_id=7")
    req.user = SimpleNamespace(is_superuser=False)

    comedor = SimpleNamespace(id=5)
    admision = SimpleNamespace(
        id=7,
        acompanamiento=SimpleNamespace(nro_convenio="CONV-7"),
    )

    mocker.patch(
        "django.views.generic.detail.DetailView.get_context_data",
        return_value={},
    )
    mocker.patch("acompanamientos.views.user_has_permission_code", return_value=False)
    obtener_hitos = mocker.patch(
        "acompanamientos.views.AcompanamientoService.obtener_hitos",
        return_value="hitos",
    )
    obtener_datos = mocker.patch(
        "acompanamientos.views.AcompanamientoService.obtener_datos_admision",
        return_value={
            "admision": admision,
            "info_relevante": "info",
            "numero_if": "IF-7",
            "numero_disposicion": "DISP-7",
        },
    )
    mocker.patch(
        "acompanamientos.views.AcompanamientoService.obtener_fechas_hitos",
        return_value={},
    )
    mocker.patch(
        "acompanamientos.views.AcompanamientoService.obtener_admisiones_para_selector",
        return_value=[
            SimpleNamespace(
                id=7,
                activa=False,
                acompanamiento=admision.acompanamiento,
            )
        ],
    )
    mocker.patch(
        "acompanamientos.views.AcompanamientoService.obtener_prestaciones_detalladas",
        return_value={
            "prestaciones_por_dia": [],
            "prestaciones_dias": [],
            "dias_semana": [],
        },
    )

    view = module.AcompanamientoDetailView()
    view.request = req
    view.object = comedor

    ctx = view.get_context_data()

    obtener_datos.assert_called_once_with(comedor, admision_id=7)
    obtener_hitos.assert_called_once_with(comedor, admision_id=7)
    assert ctx["admision_id_activa"] == 7
    assert ctx["nro_convenio"] == "CONV-7"


def test_acompanamiento_detail_view_toma_ultima_cerrada_si_no_hay_activa(mocker):
    rf = RequestFactory()
    req = rf.get("/acompanamientos/acompanamiento/5/detalle/")
    req.user = SimpleNamespace(is_superuser=False)

    comedor = SimpleNamespace(id=5)
    admision_cerrada = SimpleNamespace(
        id=13,
        acompanamiento=SimpleNamespace(nro_convenio="CONV-13"),
    )

    mocker.patch(
        "django.views.generic.detail.DetailView.get_context_data",
        return_value={},
    )
    mocker.patch("acompanamientos.views.user_has_permission_code", return_value=False)
    obtener_datos = mocker.patch(
        "acompanamientos.views.AcompanamientoService.obtener_datos_admision",
        side_effect=[
            {
                "admision": None,
                "info_relevante": None,
                "numero_if": None,
                "numero_disposicion": None,
            },
            {
                "admision": admision_cerrada,
                "info_relevante": "info-cerrada",
                "numero_if": "IF-13",
                "numero_disposicion": "DISP-13",
            },
        ],
    )
    obtener_hitos = mocker.patch(
        "acompanamientos.views.AcompanamientoService.obtener_hitos",
        return_value="hitos-cerrados",
    )
    mocker.patch(
        "acompanamientos.views.AcompanamientoService.obtener_fechas_hitos",
        return_value={},
    )
    mocker.patch(
        "acompanamientos.views.AcompanamientoService.obtener_admisiones_para_selector",
        return_value=[
            SimpleNamespace(
                id=13,
                activa=False,
                acompanamiento=admision_cerrada.acompanamiento,
            )
        ],
    )
    mocker.patch(
        "acompanamientos.views.AcompanamientoService.obtener_prestaciones_detalladas",
        return_value={
            "prestaciones_por_dia": [],
            "prestaciones_dias": [],
            "dias_semana": [],
        },
    )

    view = module.AcompanamientoDetailView()
    view.request = req
    view.object = comedor

    ctx = view.get_context_data()

    assert obtener_datos.call_args_list == [
        call(comedor, admision_id=None),
        call(comedor, admision_id=13),
    ]
    obtener_hitos.assert_called_once_with(comedor, admision_id=13)
    assert ctx["admision_id_activa"] == 13
    assert ctx["numero_if"] == "IF-13"
