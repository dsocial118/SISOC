"""Tests unitarios para vistas web de rendiciones mensuales."""

import json
from io import BytesIO
from types import SimpleNamespace

import pytest
from django.test import RequestFactory
from django.http import FileResponse

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
    rendicion = SimpleNamespace(id=7, estado="finalizada")
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
    assert contexto["puede_revisar_documentos"] is False
    agrupada_mock.assert_called_once_with(rendicion)
    scope_mock.assert_called_once_with(rendicion)


def test_detail_view_post_actualiza_documento_y_redirige(mocker):
    request = RequestFactory().post(
        "/rendicioncuentasmensual/detalle/7/",
        data={
            "documento_id": "9",
            "estado": "validado",
            "observaciones": "",
        },
    )
    request.user = _user()
    setattr(request, "_messages", mocker.Mock())

    rendicion = SimpleNamespace(
        pk=7,
        archivos_adjuntos=SimpleNamespace(
            filter=lambda **_kwargs: SimpleNamespace(
                first=lambda: SimpleNamespace(id=9)
            )
        ),
    )

    get_object_mock = mocker.patch.object(
        module.RendicionCuentaMensualDetailView,
        "get_object",
        return_value=rendicion,
    )
    mocker.patch.object(
        module.RendicionCuentaMensualDetailView,
        "_user_can_review_documentos",
        return_value=True,
    )
    update_mock = mocker.patch(
        "rendicioncuentasmensual.views.RendicionCuentaMensualService.actualizar_estado_documento_revision"
    )
    success_mock = mocker.patch("rendicioncuentasmensual.views.messages.success")

    view = module.RendicionCuentaMensualDetailView()
    view.request = request
    view.kwargs = {"pk": 7}

    response = view.post(request)

    assert response.status_code == 302
    assert response.url.endswith("/rendicioncuentasmensual/detalle/7/")
    get_object_mock.assert_called_once_with()
    update_mock.assert_called_once()
    assert update_mock.call_args.kwargs["actor"] is request.user
    success_mock.assert_called_once()


def test_detail_view_post_ajax_actualiza_documento_y_devuelve_json(mocker):
    request = RequestFactory().post(
        "/rendicioncuentasmensual/detalle/7/",
        data={
            "documento_id": "9",
            "estado": "validado",
            "observaciones": "",
        },
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    request.user = _user()
    setattr(request, "_messages", mocker.Mock())

    documento = SimpleNamespace(
        id=9,
        estado="validado",
        observaciones=None,
        refresh_from_db=mocker.Mock(),
        get_estado_display=lambda: "Validado",
        get_estado_visual=lambda: "validado",
        get_estado_visual_display=lambda: "Validado",
    )
    rendicion = SimpleNamespace(
        pk=7,
        estado="finalizada",
        refresh_from_db=mocker.Mock(),
        get_estado_display=lambda: "Presentación finalizada",
        archivos_adjuntos=SimpleNamespace(
            filter=lambda **_kwargs: SimpleNamespace(first=lambda: documento)
        ),
    )

    mocker.patch.object(
        module.RendicionCuentaMensualDetailView,
        "get_object",
        return_value=rendicion,
    )
    mocker.patch.object(
        module.RendicionCuentaMensualDetailView,
        "_user_can_review_documentos",
        return_value=True,
    )
    update_mock = mocker.patch(
        "rendicioncuentasmensual.views.RendicionCuentaMensualService.actualizar_estado_documento_revision"
    )
    mocker.patch(
        "rendicioncuentasmensual.views.RendicionCuentaMensualService.rendicion_esta_completamente_validada",
        return_value=True,
    )

    view = module.RendicionCuentaMensualDetailView()
    view.request = request
    view.kwargs = {"pk": 7}

    response = view.post(request)

    assert response.status_code == 200
    body = json.loads(response.content)
    assert body["success"] is True
    assert body["rendicion"]["puede_descargar_pdf"] is True
    update_mock.assert_called_once()


def test_detail_view_post_ajax_rechaza_revision_sin_permiso(mocker):
    request = RequestFactory().post(
        "/rendicioncuentasmensual/detalle/7/",
        data={"documento_id": "9", "estado": "validado"},
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    request.user = _user()
    setattr(request, "_messages", mocker.Mock())

    rendicion = SimpleNamespace(
        pk=7,
        archivos_adjuntos=SimpleNamespace(
            filter=lambda **_kwargs: SimpleNamespace(
                first=lambda: SimpleNamespace(id=9)
            )
        ),
    )
    mocker.patch.object(
        module.RendicionCuentaMensualDetailView,
        "get_object",
        return_value=rendicion,
    )
    update_mock = mocker.patch(
        "rendicioncuentasmensual.views.RendicionCuentaMensualService.actualizar_estado_documento_revision"
    )

    view = module.RendicionCuentaMensualDetailView()
    view.request = request
    view.kwargs = {"pk": 7}

    response = view.post(request)

    assert response.status_code == 403
    body = json.loads(response.content)
    assert body == {
        "success": False,
        "message": "No tiene permisos para revisar documentos.",
    }
    update_mock.assert_not_called()


def test_download_pdf_view_devuelve_archivo(mocker):
    request = RequestFactory().get("/rendicioncuentasmensual/detalle/7/descargar-pdf/")
    request.user = _user()
    setattr(request, "_messages", mocker.Mock())

    rendicion = SimpleNamespace(pk=7, id=7, numero_rendicion=12)
    buffer = BytesIO(b"%PDF-1.4 test")
    mocker.patch(
        "rendicioncuentasmensual.views.RendicionCuentaMensualService.obtener_rendicion_cuenta_mensual",
        return_value=rendicion,
    )
    pdf_mock = mocker.patch(
        "rendicioncuentasmensual.views.RendicionCuentaMensualService.generar_pdf_descarga_rendicion",
        return_value=buffer,
    )

    view = module.RendicionCuentaMensualDownloadPdfView()
    view.request = request
    view.kwargs = {"pk": 7}

    response = view.get(request)

    assert isinstance(response, FileResponse)
    assert 'filename="rendicion-12.pdf"' in response.headers["Content-Disposition"]
    pdf_mock.assert_called_once_with(rendicion)


def test_detail_view_post_muestra_error_si_documento_no_existe(mocker):
    request = RequestFactory().post(
        "/rendicioncuentasmensual/detalle/7/",
        data={"documento_id": "999", "estado": "validado"},
    )
    request.user = _user()
    setattr(request, "_messages", mocker.Mock())

    rendicion = SimpleNamespace(
        pk=7,
        archivos_adjuntos=SimpleNamespace(
            filter=lambda **_kwargs: SimpleNamespace(first=lambda: None)
        ),
    )
    mocker.patch.object(
        module.RendicionCuentaMensualDetailView,
        "get_object",
        return_value=rendicion,
    )
    mocker.patch.object(
        module.RendicionCuentaMensualDetailView,
        "_user_can_review_documentos",
        return_value=True,
    )
    error_mock = mocker.patch("rendicioncuentasmensual.views.messages.error")

    view = module.RendicionCuentaMensualDetailView()
    view.request = request
    view.kwargs = {"pk": 7}

    response = view.post(request)

    assert response.status_code == 302
    assert response.url.endswith("/rendicioncuentasmensual/detalle/7/")
    error_mock.assert_called_once_with(request, "El documento seleccionado no existe.")
