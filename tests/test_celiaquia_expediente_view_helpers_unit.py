from types import SimpleNamespace

from django.http import JsonResponse

from celiaquia.views import expediente as module


def test_helper_functions_for_user_and_request(mocker):
    groups_filter = mocker.Mock()
    groups_filter.exists.side_effect = [True, False]
    user = SimpleNamespace(
        is_authenticated=True,
        is_superuser=True,
        groups=SimpleNamespace(filter=mocker.Mock(return_value=groups_filter)),
    )

    assert module._user_in_group(user, "X") is True
    assert module._is_admin(user) is True

    req = SimpleNamespace(headers={"X-Requested-With": "XMLHttpRequest"})
    assert module._is_ajax(req) is True


def test_provincial_helpers_and_parse_limit():
    user_no_auth = SimpleNamespace(is_authenticated=False)
    assert module._is_provincial(user_no_auth) is False

    profile = SimpleNamespace(es_usuario_provincial=True, provincia_id=7, provincia="PBA")
    user = SimpleNamespace(is_authenticated=True, profile=profile)
    assert module._is_provincial(user) is True
    assert module._user_provincia(user) == "PBA"

    assert module._parse_limit(None, default=10) == 10
    assert module._parse_limit("all", default=10) is None
    assert module._parse_limit("0", default=10) is None
    assert module._parse_limit("-1", default=10) is None
    assert module._parse_limit("7", default=10, max_cap=5) == 5
    assert module._parse_limit("x", default=10) == 10


def test_localidades_lookup_view_filters_and_returns_json(mocker):
    view = module.LocalidadesLookupView()

    loc = SimpleNamespace(
        id=1,
        nombre="Localidad",
        municipio_id=2,
        municipio=SimpleNamespace(id=2, nombre="Mun", provincia_id=3, provincia=SimpleNamespace(id=3, nombre="Prov")),
    )

    qs = mocker.Mock()
    qs.filter.return_value = qs
    qs.order_by.return_value = [loc]
    mocker.patch("celiaquia.views.expediente.Localidad.objects.select_related", return_value=qs)

    mocker.patch("celiaquia.views.expediente._user_in_group", return_value=False)
    mocker.patch("celiaquia.views.expediente._is_provincial", return_value=True)
    mocker.patch("celiaquia.views.expediente._user_provincia", return_value="prov_obj")

    request = SimpleNamespace(
        user=SimpleNamespace(),
        GET={"provincia": "3", "municipio": "2"},
    )

    response = view.get(request)

    assert isinstance(response, JsonResponse)
    assert response.status_code == 200
    assert qs.filter.call_count >= 3


def test_expediente_preview_excel_view_error_and_success(mocker):
    view = module.ExpedientePreviewExcelView()

    request_no_file = SimpleNamespace(FILES={}, POST={}, GET={}, method="POST", get_full_path=lambda: "/x")
    resp = view.post(request_no_file)
    assert resp.status_code == 400

    archivo = object()
    request_ok = SimpleNamespace(FILES={"excel_masivo": archivo}, POST={"limit": "3"}, GET={}, method="POST", get_full_path=lambda: "/x")

    mocker.patch("celiaquia.views.expediente.ImportacionService.preview_excel", return_value={"rows": []})
    resp_ok = view.post(request_ok)
    assert resp_ok.status_code == 200

    mocker.patch(
        "celiaquia.views.expediente.ImportacionService.preview_excel",
        side_effect=Exception("boom"),
    )
    resp_err = view.post(request_ok)
    assert resp_err.status_code == 500


def test_expediente_plantilla_excel_view_download(mocker):
    view = module.ExpedientePlantillaExcelView()
    mocker.patch("celiaquia.views.expediente.ImportacionService.generar_plantilla_excel", return_value=b"xlsx")

    response = view.get(SimpleNamespace())

    assert response.status_code == 200
    assert "attachment; filename=\"plantilla_expediente.xlsx\"" in response["Content-Disposition"]


def test_expediente_create_view_context_by_user_type(mocker):
    view = module.ExpedienteCreateView()
    mocker.patch("django.views.generic.edit.ModelFormMixin.get_context_data", return_value={})

    mocker.patch("celiaquia.views.expediente._is_provincial", return_value=True)
    mocker.patch("celiaquia.views.expediente._user_provincia", return_value="prov")
    view.request = SimpleNamespace(user=SimpleNamespace())
    ctx = view.get_context_data()
    assert ctx["provincias"] == ["prov"]

    mocker.patch("celiaquia.views.expediente._is_provincial", return_value=False)
    mocker.patch("celiaquia.views.expediente.Provincia.objects.order_by", return_value=["p1", "p2"])
    ctx2 = view.get_context_data()
    assert ctx2["provincias"] == ["p1", "p2"]
