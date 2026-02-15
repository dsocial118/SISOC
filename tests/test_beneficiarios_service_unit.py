"""Unit tests for centrodefamilia beneficiarios service helpers."""

from types import SimpleNamespace

import pytest
from django.http import QueryDict

from centrodefamilia.services import beneficiarios_service as service


class DummySession(dict):
    """Simple session stub with mutable modified flag."""

    modified = False


@pytest.mark.parametrize(
    "value,expected",
    [
        ("f", "F"),
        ("femenino", "F"),
        ("m", "M"),
        ("masculino", "M"),
        ("x", "X"),
        ("otro/no binario", "X"),
        ("Desconocido", "Desconocido"),
    ],
)
def test_normalize_genero_mapea_valores_humanos(value, expected):
    """Normaliza variantes de género a los códigos esperados."""
    assert service._normalize_genero(value) == expected


def test_normalize_genero_no_string_devuelve_sin_cambios():
    """Devuelve el mismo valor cuando no recibe string."""
    sentinel = object()
    assert service._normalize_genero(sentinel) is sentinel


def test_separar_datos_post_separa_prefijos_y_listas(rf):
    """Separa datos de beneficiario/responsable preservando campos multivalor."""
    request = rf.post(
        "/",
        data={
            "beneficiario_nombre": "Ana",
            "beneficiario_actividad_preferida": ["arte", "musica"],
            "beneficiario_actividades_detalle": ["danza", "teatro"],
            "responsable_dni": "123",
            "responsable_vinculo_parental": "madre",
        },
    )

    beneficiario_data, responsable_data = service.separar_datos_post(request)

    assert beneficiario_data["nombre"] == "Ana"
    assert beneficiario_data["actividad_preferida"] == ["arte", "musica"]
    assert beneficiario_data["actividades_detalle"] == ["danza", "teatro"]
    assert responsable_data["dni"] == "123"
    assert responsable_data["vinculo_parental"] == "madre"


def test_guardar_datos_renaper_usa_cache_en_sesion(rf, mocker):
    """Persiste RENAPER usando datos cacheados sin consultar API externa."""
    request = rf.get("/")
    request.session = {
        "renaper_cache": {"responsable_123_F": {"dni": "123", "genero": "F"}}
    }
    persona = SimpleNamespace(dni="123", genero="F")

    update_or_create = mocker.patch(
        "centrodefamilia.services.beneficiarios_service.BeneficiariosResponsablesRenaper.objects.update_or_create"
    )
    consultar = mocker.patch(
        "centrodefamilia.services.beneficiarios_service.consultar_datos_renaper"
    )

    service.guardar_datos_renaper(request, persona, "Responsable", es_nuevo=True)

    consultar.assert_not_called()
    update_or_create.assert_called_once()


def test_guardar_datos_renaper_consulta_api_si_no_hay_cache(rf, mocker):
    """Consulta RENAPER cuando no encuentra cache y persiste la respuesta."""
    request = rf.get("/")
    request.session = {}
    persona = SimpleNamespace(dni="123", genero="F")

    mocker.patch(
        "centrodefamilia.services.beneficiarios_service.consultar_datos_renaper",
        return_value={"success": True, "datos_api": {"dni": "123", "genero": "F"}},
    )
    update_or_create = mocker.patch(
        "centrodefamilia.services.beneficiarios_service.BeneficiariosResponsablesRenaper.objects.update_or_create"
    )

    service.guardar_datos_renaper(request, persona, "Beneficiario", es_nuevo=True)

    update_or_create.assert_called_once_with(
        dni="123",
        genero="F",
        tipo="Beneficiario",
        defaults=mocker.ANY,
    )


def test_guardar_datos_renaper_no_hace_nada_para_responsable_existente(rf, mocker):
    """No persiste datos de RENAPER para responsable existente."""
    request = rf.get("/")
    request.session = {}
    persona = SimpleNamespace(dni="123", genero="F")

    update_or_create = mocker.patch(
        "centrodefamilia.services.beneficiarios_service.BeneficiariosResponsablesRenaper.objects.update_or_create"
    )
    service.guardar_datos_renaper(request, persona, "Responsable", es_nuevo=False)
    update_or_create.assert_not_called()


def test_generar_respuesta_success_ajax_devuelve_json(rf, mocker):
    """En éxito vía AJAX retorna respuesta JSON de confirmación."""
    request = rf.get("/")
    request.headers = {"X-Requested-With": "XMLHttpRequest"}
    success = mocker.patch(
        "centrodefamilia.services.beneficiarios_service.messages.success"
    )

    response = service.generar_respuesta(
        request,
        beneficiario=object(),
        forms_data={},
        template_name="x.html",
    )

    assert response.status_code == 200
    assert b'"status": "success"' in response.content
    success.assert_called_once()


def test_generar_respuesta_error_ajax_devuelve_400(rf):
    """En error vía AJAX devuelve status 400 y detalle de errores."""
    request = rf.get("/")
    request.headers = {"X-Requested-With": "XMLHttpRequest"}
    invalid_form = SimpleNamespace(
        is_valid=lambda: False, errors={"dni": ["obligatorio"]}
    )

    response = service.generar_respuesta(
        request,
        beneficiario=None,
        forms_data={
            "beneficiario_form": invalid_form,
            "responsable_form": invalid_form,
        },
        template_name="x.html",
    )

    assert response.status_code == 400
    assert b'"status": "error"' in response.content


def test_generar_respuesta_success_no_ajax_redirige(rf, mocker):
    """En éxito no AJAX redirige al alta de beneficiarios."""
    request = rf.get("/")
    request.headers = {}
    mocker.patch("centrodefamilia.services.beneficiarios_service.messages.success")
    redirect_mock = mocker.patch(
        "centrodefamilia.services.beneficiarios_service.redirect",
        return_value="REDIRECTED",
    )

    out = service.generar_respuesta(
        request, beneficiario=object(), forms_data={}, template_name="x.html"
    )

    assert out == "REDIRECTED"
    redirect_mock.assert_called_once_with("beneficiarios_crear")


def test_manejar_request_beneficiarios_limpia_cache_en_success(rf, mocker):
    """Limpia renaper_cache en sesión cuando la creación fue exitosa."""
    request = rf.post("/")
    request.session = DummySession({"renaper_cache": {"k": "v"}})
    request.user = SimpleNamespace(username="u")
    mocker.patch(
        "centrodefamilia.services.beneficiarios_service.separar_datos_post",
        return_value=({}, {}),
    )
    mocker.patch(
        "centrodefamilia.services.beneficiarios_service.procesar_formularios",
        return_value=(object(), None, None),
    )
    mocker.patch(
        "centrodefamilia.services.beneficiarios_service.generar_respuesta",
        return_value="OK",
    )

    out = service.manejar_request_beneficiarios(request, "template.html")

    assert out == "OK"
    assert "renaper_cache" not in request.session
    assert request.session.modified is True


def test_manejar_request_beneficiarios_excepcion_devuelve_500(rf, mocker):
    """Controla excepción inesperada y responde JSON de error 500."""
    request = rf.post("/")
    request.session = {}
    request.user = SimpleNamespace(username="u")
    mocker.patch(
        "centrodefamilia.services.beneficiarios_service.separar_datos_post",
        side_effect=RuntimeError("boom"),
    )

    response = service.manejar_request_beneficiarios(request, "template.html")
    assert response.status_code == 500
    assert b'"status": "error"' in response.content


def test_get_beneficiarios_y_responsables_context_usan_builder(mocker):
    """Arma contexto de tablas delegando en column preferences builder."""
    builder = mocker.patch(
        "centrodefamilia.services.beneficiarios_service.build_columns_context_from_fields",
        return_value={"columns": ["x"]},
    )

    b_ctx = service.get_beneficiarios_list_context(request=None)
    r_ctx = service.get_responsables_list_context(request=None)

    assert b_ctx["columns"] == ["x"]
    assert r_ctx["columns"] == ["x"]
    assert len(b_ctx["table_actions"]) == 1
    assert len(r_ctx["table_actions"]) == 1
    assert builder.call_count == 2


def test_prepare_helpers_agregan_campos_display():
    """Completa campos calculados para renderizar listados."""
    beneficiario = SimpleNamespace(
        apellido="Perez",
        nombre="Ana",
        responsable=SimpleNamespace(apellido="Lopez", nombre="Mario"),
        get_genero_display=lambda: "Femenino",
    )
    responsable = SimpleNamespace(
        apellido="Lopez",
        nombre="Mario",
        get_genero_display=lambda: "Masculino",
        get_vinculo_parental_display=lambda: "Padre",
    )

    service.prepare_beneficiarios_for_display([beneficiario])
    service.prepare_responsables_for_display([responsable])

    assert beneficiario.apellido_nombre == "Perez, Ana"
    assert beneficiario.responsable_nombre == "Lopez, Mario"
    assert responsable.vinculo_display == "Padre"


def test_filtered_wrappers_delegan_a_motor_avanzado(mocker):
    """Delegan en AdvancedFilterEngine con queryset base correspondiente."""
    rq = QueryDict("q=1")
    b_qs = object()
    r_qs = object()
    mocker.patch(
        "centrodefamilia.services.beneficiarios_service.get_beneficiarios_queryset",
        return_value=b_qs,
    )
    mocker.patch(
        "centrodefamilia.services.beneficiarios_service.get_responsables_queryset",
        return_value=r_qs,
    )
    b_filter = mocker.patch.object(
        service.BENEFICIARIO_ADVANCED_FILTER, "filter_queryset", return_value="BQ"
    )
    r_filter = mocker.patch.object(
        service.RESPONSABLE_ADVANCED_FILTER, "filter_queryset", return_value="RQ"
    )

    assert service.get_filtered_beneficiarios(rq) == "BQ"
    assert service.get_filtered_responsables(rq) == "RQ"
    b_filter.assert_called_once_with(b_qs, rq)
    r_filter.assert_called_once_with(r_qs, rq)


def test_get_beneficiarios_queryset_encadena_select_related_order(mocker):
    """Construye queryset optimizada para beneficiarios."""
    order_qs = object()
    select_related = mocker.Mock(
        return_value=SimpleNamespace(order_by=mocker.Mock(return_value=order_qs))
    )
    mocker.patch(
        "centrodefamilia.services.beneficiarios_service.Beneficiario.objects.select_related",
        select_related,
    )

    out = service.get_beneficiarios_queryset()

    assert out is order_qs
    select_related.assert_called_once_with("responsable", "provincia", "municipio")


def test_get_responsables_queryset_encadena_annotate_select_related_order(mocker):
    """Construye queryset optimizada para responsables con conteo."""
    order_qs = object()
    order_by = mocker.Mock(return_value=order_qs)
    select_related = mocker.Mock(return_value=SimpleNamespace(order_by=order_by))
    annotate = mocker.Mock(return_value=SimpleNamespace(select_related=select_related))
    mocker.patch(
        "centrodefamilia.services.beneficiarios_service.Responsable.objects.annotate",
        annotate,
    )

    out = service.get_responsables_queryset()

    assert out is order_qs
    select_related.assert_called_once_with("provincia", "municipio")
    order_by.assert_called_once_with("-id", "apellido", "nombre")


def test_get_responsable_detail_context_filtra_y_select_related(mocker):
    """Devuelve contexto de detalle con vínculos asociados al responsable."""
    responsable = object()
    filtered = SimpleNamespace(select_related=mocker.Mock(return_value="QS"))
    filter_mock = mocker.patch(
        "centrodefamilia.services.beneficiarios_service.BeneficiarioResponsable.objects.filter",
        return_value=filtered,
    )

    ctx = service.get_responsable_detail_context(responsable)

    filter_mock.assert_called_once_with(responsable=responsable)
    assert ctx["vinculos_beneficiarios"] == "QS"
