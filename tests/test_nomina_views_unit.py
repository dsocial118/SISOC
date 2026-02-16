"""Tests unitarios para comedores.views.nomina."""

from types import SimpleNamespace

from django.http import JsonResponse

from comedores.views import nomina as module


def test_nomina_editar_ajax_get_and_post_paths(mocker):
    req_get = SimpleNamespace(method="GET")
    req_post = SimpleNamespace(method="POST", POST={})
    nomina = object()

    mocker.patch("comedores.views.nomina.get_object_or_404", return_value=nomina)

    form_get = object()
    form_post_ok = SimpleNamespace(is_valid=lambda: True, save=mocker.Mock())
    form_post_bad = SimpleNamespace(is_valid=lambda: False, errors={"x": ["e"]})

    form_ctor = mocker.patch(
        "comedores.views.nomina.NominaForm",
        side_effect=[form_get, form_post_ok, form_post_bad],
    )
    render = mocker.patch("comedores.views.nomina.render", return_value="html")

    out_get = module.nomina_editar_ajax.__wrapped__(req_get, 1)
    assert out_get == "html"
    assert render.called

    out_ok = module.nomina_editar_ajax.__wrapped__(req_post, 1)
    assert isinstance(out_ok, JsonResponse)
    assert b'"success": true' in out_ok.content

    out_bad = module.nomina_editar_ajax.__wrapped__(req_post, 1)
    assert b'"success": false' in out_bad.content
    assert form_ctor.call_count == 3


def test_nomina_detail_context_data(mocker):
    mocker.patch("django.views.generic.base.ContextMixin.get_context_data", return_value={})
    mocker.patch(
        "comedores.views.nomina.ComedorService.get_nomina_detail",
        return_value=("page_obj", 1, 2, 3, 4, 10, {"ninos": 2, "adolescentes": 3}),
    )
    mocker.patch("comedores.views.nomina.ComedorService.get_comedor", return_value="comedor")

    view = module.NominaDetailView()
    view.kwargs = {"pk": 9}
    view.request = SimpleNamespace(GET={"page": "2"})

    ctx = view.get_context_data()
    assert ctx["object"] == "comedor"
    assert ctx["cantidad_nomina"] == 10
    assert ctx["menores"] == 5


def test_prepare_renaper_initial_data_uses_data_and_datos_api(mocker):
    mocker.patch(
        "comedores.views.nomina.ComedorService._parse_fecha_renaper",
        return_value=SimpleNamespace(isoformat=lambda: "2000-01-01"),
    )

    out_data = module.NominaCreateView._prepare_renaper_initial_data(
        {"data": {"fecha_nacimiento": "01/01/2000"}}
    )
    assert out_data["fecha_nacimiento"] == "2000-01-01"

    out_api = module.NominaCreateView._prepare_renaper_initial_data(
        {"data": {"nombre": "A"}, "datos_api": {"fechaNacimiento": "2000-01-01"}}
    )
    assert out_api["fecha_nacimiento"] == "2000-01-01"


def test_nomina_create_get_context_data_with_renaper(mocker):
    mocker.patch("django.views.generic.base.ContextMixin.get_context_data", return_value={})
    mocker.patch("comedores.views.nomina.ComedorService.get_comedor", return_value="comedor")
    mocker.patch("comedores.views.nomina.ComedorService.buscar_ciudadanos_por_documento", return_value=[])
    mocker.patch(
        "comedores.views.nomina.ComedorService.obtener_datos_ciudadano_desde_renaper",
        return_value={"success": True, "message": "precargado", "data": {"dni": "1"}},
    )
    mocker.patch.object(module.NominaCreateView, "_prepare_renaper_initial_data", return_value={"dni": "1"})
    info = mocker.patch("comedores.views.nomina.messages.info")

    view = module.NominaCreateView()
    view.kwargs = {"pk": 1}
    view.object = None
    view.request = SimpleNamespace(method="GET", GET={"query": "12345678"}, POST={})
    mocker.patch.object(view, "get_form", return_value="main_form")

    form_ciudadano = mocker.patch("comedores.views.nomina.CiudadanoFormParaNomina", return_value="form")
    mocker.patch("comedores.views.nomina.NominaExtraForm", return_value="extra")

    ctx = view.get_context_data()
    assert ctx["renaper_precarga"] is True
    assert ctx["form_ciudadano"] == "form"
    assert info.called
    assert form_ciudadano.called


def test_nomina_create_post_ciudadano_existente(mocker):
    view = module.NominaCreateView()
    view.kwargs = {"pk": 5}
    view.object = None

    req = SimpleNamespace(POST={"ciudadano_id": "10"}, user="u")
    view.request = req

    form = SimpleNamespace(is_valid=lambda: True, cleaned_data={"estado": "A", "observaciones": "o"})
    mocker.patch("comedores.views.nomina.NominaExtraForm", return_value=form)
    mocker.patch("comedores.views.nomina.ComedorService.agregar_ciudadano_a_nomina", return_value=(True, "ok"))
    mocker.patch("comedores.views.nomina.messages.success")
    mocker.patch.object(view, "get_success_url", return_value="/ok")
    redir = mocker.patch("comedores.views.nomina.redirect", return_value="redir")

    out = view.post(req)
    assert out == "redir"
    redir.assert_called_once_with("/ok")


def test_nomina_create_post_ciudadano_nuevo_success_and_error(mocker):
    view = module.NominaCreateView()
    view.kwargs = {"pk": 5}
    view.object = None

    req = SimpleNamespace(POST={"origen_dato": "renaper"}, user="u")
    view.request = req

    form_ciudadano = SimpleNamespace(is_valid=lambda: True, cleaned_data={"nombre": "A"})
    form_extra = SimpleNamespace(is_valid=lambda: True, cleaned_data={"estado": "A", "observaciones": "o"})
    mocker.patch("comedores.views.nomina.CiudadanoFormParaNomina", return_value=form_ciudadano)
    mocker.patch("comedores.views.nomina.NominaExtraForm", return_value=form_extra)
    mocker.patch(
        "comedores.views.nomina.ComedorService.crear_ciudadano_y_agregar_a_nomina",
        return_value=(True, "ok"),
    )
    mocker.patch("comedores.views.nomina.messages.success")
    mocker.patch.object(view, "get_success_url", return_value="/ok")
    mocker.patch("comedores.views.nomina.redirect", return_value="redir")

    assert view.post(req) == "redir"

    # rama error de formularios
    bad_ciudadano = SimpleNamespace(is_valid=lambda: False, cleaned_data={})
    bad_extra = SimpleNamespace(is_valid=lambda: False, cleaned_data={})
    mocker.patch("comedores.views.nomina.CiudadanoFormParaNomina", return_value=bad_ciudadano)
    mocker.patch("comedores.views.nomina.NominaExtraForm", return_value=bad_extra)
    mocker.patch("comedores.views.nomina.messages.warning")
    mocker.patch.object(view, "get_context_data", return_value={"x": 1})
    mocker.patch.object(view, "render_to_response", return_value="render")

    assert view.post(req) == "render"
