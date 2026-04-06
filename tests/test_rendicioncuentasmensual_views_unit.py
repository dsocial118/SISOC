"""Tests unitarios para vistas web de rendiciones mensuales."""

from types import SimpleNamespace

from rendicioncuentasmensual import views as module


class _Req(SimpleNamespace):
    pass


def _user():
    return SimpleNamespace(is_authenticated=True)


def test_global_list_view_get_queryset_delega_en_service(mocker):
    view = module.RendicionCuentaMensualGlobalListView()
    view.request = _Req(user=_user(), GET={})

    expected = [SimpleNamespace(id=1)]
    service_mock = mocker.patch(
        "rendicioncuentasmensual.views.RendicionCuentaMensualService.obtener_todas_rendiciones_cuentas_mensuales",
        return_value=expected,
    )

    assert view.get_queryset() == expected
    service_mock.assert_called_once_with()


def test_global_list_view_contexto_expone_titulo(mocker):
    view = module.RendicionCuentaMensualGlobalListView()
    view.request = _Req(user=_user(), GET={})

    mocker.patch(
        "django.views.generic.list.MultipleObjectMixin.get_context_data",
        return_value={"rendiciones_cuentas_mensuales": []},
    )

    contexto = view.get_context_data()

    assert contexto["titulo_listado"] == "Rendiciones"
    assert contexto["rendiciones_cuentas_mensuales"] == []
    assert contexto["breadcrumb_items"][0]["text"] == "Comedores"


def test_detail_view_contexto_expone_documentacion_agrupada(mocker):
    view = module.RendicionCuentaMensualDetailView()
    rendicion = SimpleNamespace(id=7)
    view.request = _Req(user=_user(), GET={})
    view.kwargs = {"pk": 7}

    mocker.patch(
        "django.views.generic.detail.SingleObjectMixin.get_context_data",
        return_value={},
    )
    mocker.patch(
        "rendicioncuentasmensual.views.RendicionCuentaMensualService.obtener_rendicion_cuenta_mensual",
        return_value=rendicion,
    )
    agrupada = [{"codigo": "formulario_ii", "label": "Formulario II", "archivos": []}]
    agrupada_mock = mocker.patch(
        "rendicioncuentasmensual.views.RendicionCuentaMensualService.obtener_documentacion_para_detalle",
        return_value=agrupada,
    )
    scope = {
        "organizacion": SimpleNamespace(nombre="Org"),
        "proyecto_codigo": "PROY-01",
        "comedores_relacionados": [],
    }
    scope_mock = mocker.patch(
        "rendicioncuentasmensual.views.RendicionCuentaMensualService.obtener_scope_proyecto",
        return_value=scope,
    )

    contexto = view.get_context_data()

    assert contexto["rendicion"] is rendicion
    assert contexto["documentacion_por_categoria"] == agrupada
    assert contexto["scope_proyecto"] == scope
    agrupada_mock.assert_called_once_with(rendicion)
    scope_mock.assert_called_once_with(rendicion)
