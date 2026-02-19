"""Unit tests for centrodefamilia beneficiarios service helpers."""

import contextlib

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


def test_obtener_o_crear_responsable_ramas_principales(mocker):
    """Cubre paths de responsable existente, nuevo y formularios inválidos."""
    data = {"dni": "123"}
    usuario = object()

    existing = object()
    form_ok = SimpleNamespace(is_valid=lambda: True, save=mocker.Mock())
    mocker.patch(
        "centrodefamilia.services.beneficiarios_service.Responsable.objects.get",
        return_value=existing,
    )
    mocker.patch(
        "centrodefamilia.services.beneficiarios_service.ResponsableForm",
        return_value=form_ok,
    )
    resp, form, created = service.obtener_o_crear_responsable(data, usuario)
    assert resp is existing and form is form_ok and created is False

    form_bad = SimpleNamespace(is_valid=lambda: False)
    mocker.patch(
        "centrodefamilia.services.beneficiarios_service.ResponsableForm",
        return_value=form_bad,
    )
    resp2, form2, created2 = service.obtener_o_crear_responsable(data, usuario)
    assert resp2 is None and form2 is form_bad and created2 is False

    new_obj = SimpleNamespace(creado_por=None, save=mocker.Mock())
    form_new = SimpleNamespace(
        is_valid=lambda: True,
        save=lambda commit=False: new_obj,
    )
    mocker.patch(
        "centrodefamilia.services.beneficiarios_service.Responsable.objects.get",
        side_effect=service.Responsable.DoesNotExist(),
    )
    mocker.patch(
        "centrodefamilia.services.beneficiarios_service.ResponsableForm",
        return_value=form_new,
    )
    resp3, _form3, created3 = service.obtener_o_crear_responsable(data, usuario)
    assert resp3 is new_obj and created3 is True
    assert new_obj.creado_por is usuario


def test_crear_beneficiario_invalido_y_valido(mocker):
    """Valida ramas de formulario inválido y persistencia correcta."""
    resp = object()
    usuario = object()

    bad_form = SimpleNamespace(is_valid=lambda: False)
    mocker.patch(
        "centrodefamilia.services.beneficiarios_service.BeneficiarioForm",
        return_value=bad_form,
    )
    ben, form = service.crear_beneficiario({}, resp, "madre", usuario)
    assert ben is None and form is bad_form

    ben_obj = SimpleNamespace(
        responsable=None,
        creado_por=None,
        actividad_preferida=None,
        save=mocker.Mock(),
    )
    ok_form = SimpleNamespace(
        is_valid=lambda: True,
        save=lambda commit=False: ben_obj,
        save_m2m=mocker.Mock(),
    )
    mocker.patch(
        "centrodefamilia.services.beneficiarios_service.BeneficiarioForm",
        return_value=ok_form,
    )
    br_create = mocker.patch(
        "centrodefamilia.services.beneficiarios_service.BeneficiarioResponsable.objects.create"
    )

    ben2, _form2 = service.crear_beneficiario(
        {
            "actividad_preferida": "arte",
            "actividades_detalle": ["a"],
        },
        resp,
        "madre",
        usuario,
    )
    assert ben2 is ben_obj
    assert ben_obj.actividad_preferida == ["arte"]
    assert ben_obj.responsable is resp
    assert ben_obj.creado_por is usuario
    assert br_create.called
    assert ok_form.save_m2m.called


def test_procesar_formularios_ramas(mocker, rf):
    """Cubre falta de vínculo, error de responsable y path exitoso."""
    request = rf.post("/")
    request.user = object()
    mocker.patch(
        "centrodefamilia.services.beneficiarios_service.transaction.atomic",
        return_value=contextlib.nullcontext(),
    )

    assert service.procesar_formularios(request, {}, {}) == (None, None, None)

    mocker.patch(
        "centrodefamilia.services.beneficiarios_service.obtener_o_crear_responsable",
        return_value=(None, "resp_form", False),
    )
    out_err_resp = service.procesar_formularios(
        request, {}, {"vinculo_parental": "madre"}
    )
    assert out_err_resp == (None, None, "resp_form")

    mocker.patch(
        "centrodefamilia.services.beneficiarios_service.obtener_o_crear_responsable",
        return_value=("resp", "resp_form", True),
    )
    mocker.patch(
        "centrodefamilia.services.beneficiarios_service.crear_beneficiario",
        return_value=("ben", "ben_form"),
    )
    guardar = mocker.patch(
        "centrodefamilia.services.beneficiarios_service.guardar_datos_renaper"
    )
    out_ok = service.procesar_formularios(
        request, {"x": 1}, {"vinculo_parental": "madre"}
    )
    assert out_ok == ("ben", "ben_form", "resp_form")
    assert guardar.call_count == 2


def test_buscar_responsable_renaper_ramas(rf, mocker):
    """Cubre validaciones, existente, no encontrado y cache de RENAPER."""
    request = rf.get("/")
    request.session = DummySession()

    missing = service.buscar_responsable_renaper(request, "", "")
    assert missing.status_code == 400

    responsable = SimpleNamespace(
        nombre="Ana",
        apellido="Perez",
        genero="F",
        fecha_nacimiento=None,
        cuil="20-1",
        dni="1",
        correo_electronico="a@a.com",
        calle="x",
        altura="10",
        piso_vivienda=None,
        departamento_vivienda=None,
        codigo_postal=None,
        barrio=None,
        monoblock=None,
        provincia=None,
        municipio=None,
        localidad=None,
        prefijo_celular=None,
        numero_celular=None,
        prefijo_telefono_fijo=None,
        numero_telefono_fijo=None,
        beneficiarios=SimpleNamespace(count=lambda: 2),
    )
    mocker.patch(
        "centrodefamilia.services.beneficiarios_service.Responsable.objects.get",
        return_value=responsable,
    )
    exists_resp = service.buscar_responsable_renaper(request, "1", "F")
    assert b'"status": "exists"' in exists_resp.content

    mocker.patch(
        "centrodefamilia.services.beneficiarios_service.Responsable.objects.get",
        side_effect=service.Responsable.DoesNotExist(),
    )
    mocker.patch(
        "centrodefamilia.services.beneficiarios_service.consultar_datos_renaper",
        return_value={"success": False, "error": "nf"},
    )
    nf_resp = service.buscar_responsable_renaper(request, "2", "M")
    assert b'"status": "not_found"' in nf_resp.content

    request2 = rf.get("/")
    request2.session = DummySession()
    mocker.patch(
        "centrodefamilia.services.beneficiarios_service.Responsable.objects.get",
        side_effect=service.Responsable.DoesNotExist(),
    )
    mocker.patch(
        "centrodefamilia.services.beneficiarios_service.consultar_datos_renaper",
        return_value={"success": True, "datos_api": {"dni": "2"}, "data": {"n": 1}},
    )
    ok_resp = service.buscar_responsable_renaper(request2, "2", "M")
    assert b'"status": "possible"' in ok_resp.content
    assert request2.session.modified is True


def test_buscar_cuil_beneficiario_ramas(rf, mocker):
    """Cubre validaciones, existencia local, padrón y éxito con cache."""
    request = rf.get("/")
    request.session = DummySession()

    missing = service.buscar_cuil_beneficiario(request, "")
    assert missing.status_code == 400

    mocker.patch(
        "centrodefamilia.services.beneficiarios_service.Beneficiario.objects.filter",
        return_value=SimpleNamespace(exists=lambda: True),
    )
    exists = service.buscar_cuil_beneficiario(request, "20")
    assert b'"status": "exists"' in exists.content

    mocker.patch(
        "centrodefamilia.services.beneficiarios_service.Beneficiario.objects.filter",
        return_value=SimpleNamespace(exists=lambda: False),
    )
    mocker.patch(
        "centrodefamilia.services.beneficiarios_service.PadronBeneficiarios.objects.filter",
        return_value=SimpleNamespace(first=lambda: None),
    )
    nf = service.buscar_cuil_beneficiario(request, "21")
    assert b'"status": "not_found"' in nf.content

    padron = SimpleNamespace(
        dni="12345678",
        genero="F",
        provincia_tabla="BA",
        municipio_tabla="LP",
    )
    mocker.patch(
        "centrodefamilia.services.beneficiarios_service.PadronBeneficiarios.objects.filter",
        return_value=SimpleNamespace(first=lambda: padron),
    )
    mocker.patch(
        "centrodefamilia.services.beneficiarios_service.consultar_datos_renaper",
        return_value={"success": False, "error": "nf"},
    )
    nf2 = service.buscar_cuil_beneficiario(request, "22")
    assert b'"status": "not_found"' in nf2.content

    request_ok = rf.get("/")
    request_ok.session = DummySession()
    mocker.patch(
        "centrodefamilia.services.beneficiarios_service.consultar_datos_renaper",
        return_value={
            "success": True,
            "datos_api": {
                "nombres": "Ana",
                "apellido": "Perez",
                "genero": "F",
                "fechaNacimiento": "2000-01-01",
                "cuil": "20",
                "calle": "Mitre",
                "numero": "10",
                "piso": "2",
                "departamento": "A",
                "cpostal": "1900",
                "barrio": "Centro",
                "monoblock": "B",
                "provincia": "BA",
                "municipio": "LP",
                "ciudad": "LP",
            },
        },
    )
    ok = service.buscar_cuil_beneficiario(request_ok, "23")
    assert b'"status": "possible"' in ok.content
    assert request_ok.session.modified is True
