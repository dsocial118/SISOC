"""Contratos del endpoint RENAPER desacoplado del proveedor tecnico."""

from rest_framework.test import APIRequestFactory

from core.api_views import RenaperConsultaViewSet


def test_consulta_renaper_usa_el_proveedor_registrado(mocker):
    consultar = mocker.patch(
        "core.api_views.consultar_datos_renaper",
        return_value={"success": True, "data": {"nombre": "Ana"}},
    )
    mocker.patch.object(RenaperConsultaViewSet, "permission_classes", [])
    request = APIRequestFactory().post(
        "/api/renaper/consultar/",
        {"dni": "12345678", "sexo": "F"},
        format="json",
    )

    response = RenaperConsultaViewSet.as_view({"post": "consultar"})(request)

    assert response.status_code == 200
    assert response.data == {"success": True, "data": {"nombre": "Ana"}}
    consultar.assert_called_once_with("12345678", "F")


def test_consulta_renaper_no_expone_excepcion_del_proveedor(mocker):
    mocker.patch(
        "core.api_views.consultar_datos_renaper",
        side_effect=RuntimeError("detalle remoto sensible"),
    )
    mocker.patch.object(RenaperConsultaViewSet, "permission_classes", [])
    log_error = mocker.patch("core.api_views.logger.error")
    request = APIRequestFactory().post(
        "/api/renaper/consultar/",
        {"dni": "00000001", "sexo": "F"},
        format="json",
    )

    response = RenaperConsultaViewSet.as_view({"post": "consultar"})(request)

    assert response.status_code == 500
    assert response.data == {
        "success": False,
        "error": "No se pudo consultar RENAPER en este momento.",
    }
    assert "detalle remoto sensible" not in str(log_error.call_args)
