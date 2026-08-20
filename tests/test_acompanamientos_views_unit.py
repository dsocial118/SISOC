"""Tests unitarios para acompanamientos.views."""

from types import SimpleNamespace
from unittest.mock import call

from django.test import RequestFactory

from acompanamientos import views as module


def _acompanamiento_stub(
    nro_convenio="CONV",
    finalizado=False,
    puede_finalizarse=True,
    es_gestionable=True,
):
    """Stub con la superficie de Acompanamiento que consumen las vistas."""

    return SimpleNamespace(
        nro_convenio=nro_convenio,
        finalizado=finalizado,
        puede_finalizarse=puede_finalizarse,
        es_gestionable=es_gestionable,
    )


def _call_restaurar_hito_unwrapped(request, comedor_id):
    return module.restaurar_hito.__wrapped__.__wrapped__(
        request,
        comedor_id=comedor_id,
    )


def _call_finalizar_unwrapped(request, comedor_id):
    return module.finalizar_acompanamiento.__wrapped__.__wrapped__(
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
    hito = SimpleNamespace(
        retiro_tarjeta=True,
        save=mocker.Mock(),
        acompanamiento=_acompanamiento_stub(),
    )

    get_comedor = mocker.patch(
        "acompanamientos.views.ComedorService.get_scoped_comedor_or_404",
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
    get_comedor.assert_called_once_with(5, req.user)
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

    mocker.patch(
        "acompanamientos.views.ComedorService.get_scoped_comedor_or_404",
        return_value=comedor,
    )
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


def test_restaurar_hito_bloqueado_si_el_acompanamiento_no_es_gestionable(mocker):
    rf = RequestFactory()
    req = rf.post(
        "/acompanamientos/comedor/5/restaurar-hito/",
        {"campo": "retiro_tarjeta", "admision_id": "11"},
    )
    req.user = SimpleNamespace(is_authenticated=True)

    hito = SimpleNamespace(
        retiro_tarjeta=True,
        save=mocker.Mock(),
        acompanamiento=_acompanamiento_stub(finalizado=True, es_gestionable=False),
    )

    mocker.patch(
        "acompanamientos.views.ComedorService.get_scoped_comedor_or_404",
        return_value=SimpleNamespace(pk=5),
    )
    mocker.patch(
        "acompanamientos.views.AcompanamientoService.obtener_hitos",
        return_value=hito,
    )
    error = mocker.patch("acompanamientos.views.messages.error")
    mocker.patch("acompanamientos.views.safe_redirect", return_value="redir")

    resp = _call_restaurar_hito_unwrapped(req, comedor_id=5)

    assert resp == "redir"
    error.assert_called_once()
    hito.save.assert_not_called()
    assert hito.retiro_tarjeta is True


def test_finalizar_acompanamiento_delega_en_el_service_y_confirma(mocker):
    rf = RequestFactory()
    req = rf.post(
        "/acompanamientos/acompanamiento/5/finalizar/",
        {"admision_id": "9"},
    )
    req.user = SimpleNamespace(is_authenticated=True)

    comedor = SimpleNamespace(pk=5)
    mocker.patch(
        "acompanamientos.views.ComedorService.get_scoped_comedor_or_404",
        return_value=comedor,
    )
    finalizar = mocker.patch(
        "acompanamientos.views.AcompanamientoService.finalizar_acompanamiento",
        return_value=(_acompanamiento_stub(finalizado=True), None),
    )
    success = mocker.patch("acompanamientos.views.messages.success")
    error = mocker.patch("acompanamientos.views.messages.error")
    mocker.patch("acompanamientos.views.safe_redirect", return_value="redir")

    resp = _call_finalizar_unwrapped(req, comedor_id=5)

    assert resp == "redir"
    finalizar.assert_called_once_with(comedor, 9, req.user)
    success.assert_called_once()
    error.assert_not_called()


def test_finalizar_acompanamiento_propaga_el_error_del_service(mocker):
    rf = RequestFactory()
    req = rf.post("/acompanamientos/acompanamiento/5/finalizar/", {"admision_id": "9"})
    req.user = SimpleNamespace(is_authenticated=True)

    mocker.patch(
        "acompanamientos.views.ComedorService.get_scoped_comedor_or_404",
        return_value=SimpleNamespace(pk=5),
    )
    mocker.patch(
        "acompanamientos.views.AcompanamientoService.finalizar_acompanamiento",
        return_value=(None, "El acompañamiento ya se encuentra finalizado."),
    )
    success = mocker.patch("acompanamientos.views.messages.success")
    error = mocker.patch("acompanamientos.views.messages.error")
    mocker.patch("acompanamientos.views.safe_redirect", return_value="redir")

    resp = _call_finalizar_unwrapped(req, comedor_id=5)

    assert resp == "redir"
    error.assert_called_once_with(
        req,
        "El acompañamiento ya se encuentra finalizado.",
    )
    success.assert_not_called()


def test_finalizar_acompanamiento_toma_admision_id_desde_el_referer(mocker):
    rf = RequestFactory()
    req = rf.post("/acompanamientos/acompanamiento/5/finalizar/")
    req.user = SimpleNamespace(is_authenticated=True)
    req.META["HTTP_REFERER"] = (
        "http://testserver/acompanamientos/acompanamiento/5/detalle/?admision_id=21"
    )

    comedor = SimpleNamespace(pk=5)
    mocker.patch(
        "acompanamientos.views.ComedorService.get_scoped_comedor_or_404",
        return_value=comedor,
    )
    finalizar = mocker.patch(
        "acompanamientos.views.AcompanamientoService.finalizar_acompanamiento",
        return_value=(_acompanamiento_stub(), None),
    )
    mocker.patch("acompanamientos.views.messages.success")
    mocker.patch("acompanamientos.views.safe_redirect", return_value="redir")

    _call_finalizar_unwrapped(req, comedor_id=5)

    finalizar.assert_called_once_with(comedor, 21, req.user)


def test_acompanamiento_detail_expone_flags_de_finalizacion(mocker):
    rf = RequestFactory()
    req = rf.get("/acompanamientos/acompanamiento/5/detalle/?admision_id=7")
    req.user = SimpleNamespace(is_superuser=False)

    acompanamiento = _acompanamiento_stub(
        "CONV-7",
        finalizado=True,
        puede_finalizarse=False,
        es_gestionable=False,
    )
    admision = SimpleNamespace(id=7, acompanamiento=acompanamiento)

    mocker.patch(
        "django.views.generic.detail.DetailView.get_context_data",
        return_value={},
    )
    mocker.patch("acompanamientos.views.user_has_permission_code", return_value=False)
    mocker.patch(
        "acompanamientos.views.AcompanamientoService.obtener_datos_admision",
        return_value={
            "admision": admision,
            "info_relevante": None,
            "numero_if": None,
            "numero_disposicion": None,
        },
    )
    mocker.patch(
        "acompanamientos.views.AcompanamientoService.obtener_hitos",
        return_value=None,
    )
    mocker.patch(
        "acompanamientos.views.AcompanamientoService.obtener_fechas_hitos",
        return_value={},
    )
    mocker.patch(
        "acompanamientos.views.AcompanamientoService.obtener_admisiones_para_selector",
        return_value=[
            SimpleNamespace(id=7, activa=True, acompanamiento=acompanamiento)
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
    view.object = SimpleNamespace(id=5)

    ctx = view.get_context_data()

    assert ctx["acompanamiento"] is acompanamiento
    assert ctx["acompanamiento_finalizado"] is True
    assert ctx["puede_finalizar_acompanamiento"] is False
    assert ctx["acompanamiento_gestionable"] is False


def test_acompanamiento_detail_aplica_scope_del_usuario(mocker):
    user = SimpleNamespace()
    scoped_queryset = object()
    get_scoped_queryset = mocker.patch(
        "acompanamientos.views.ComedorService.get_scoped_comedor_queryset",
        return_value=scoped_queryset,
    )
    view = module.AcompanamientoDetailView()
    view.request = SimpleNamespace(user=user)

    assert view.get_queryset() is scoped_queryset
    get_scoped_queryset.assert_called_once_with(user)


def test_acompanamiento_detail_view_normaliza_admision_id_y_reusa_el_mismo_scope(
    mocker,
):
    rf = RequestFactory()
    req = rf.get("/acompanamientos/acompanamiento/5/detalle/?admision_id=7")
    req.user = SimpleNamespace(is_superuser=False)

    comedor = SimpleNamespace(id=5)
    admision = SimpleNamespace(
        id=7,
        acompanamiento=_acompanamiento_stub("CONV-7"),
    )

    mocker.patch(
        "django.views.generic.detail.DetailView.get_context_data",
        return_value={},
    )
    mocker.patch("acompanamientos.views.user_has_permission_code", return_value=True)
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
    informe = SimpleNamespace(id=70, tipo="base")
    informe_filter = mocker.patch(
        "acompanamientos.views.InformeTecnico.objects.filter",
        return_value=SimpleNamespace(
            order_by=lambda *_args: SimpleNamespace(first=lambda: informe)
        ),
    )

    view = module.AcompanamientoDetailView()
    view.request = req
    view.object = comedor

    ctx = view.get_context_data()

    obtener_datos.assert_called_once_with(comedor, admision_id=7)
    obtener_hitos.assert_called_once_with(comedor, admision_id=7)
    assert ctx["admision_id_activa"] == 7
    assert ctx["nro_convenio"] == "CONV-7"
    assert ctx["informe_tecnico_complementario"] == informe
    informe_filter.assert_called_once_with(
        admision=admision,
        estado_formulario="finalizado",
    )


def test_acompanamiento_detail_view_toma_ultima_cerrada_si_no_hay_activa(mocker):
    rf = RequestFactory()
    req = rf.get("/acompanamientos/acompanamiento/5/detalle/")
    req.user = SimpleNamespace(is_superuser=False)

    comedor = SimpleNamespace(id=5)
    admision_cerrada = SimpleNamespace(
        id=13,
        acompanamiento=_acompanamiento_stub("CONV-13"),
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
