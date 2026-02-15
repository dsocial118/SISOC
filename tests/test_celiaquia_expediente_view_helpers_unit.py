"""Tests for test celiaquia expediente view helpers unit."""

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


def test_confirm_view_ajax_with_pending_errors_returns_400(mocker):
    """Confirm endpoint should fail when there are unresolved erroneous records."""
    view = module.ExpedienteConfirmView()
    view.request = SimpleNamespace(user=SimpleNamespace())

    req = SimpleNamespace(
        user=SimpleNamespace(),
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    expediente = SimpleNamespace()
    mocker.patch("celiaquia.views.expediente._is_admin", return_value=True)
    mocker.patch("celiaquia.views.expediente.get_object_or_404", return_value=expediente)
    mocker.patch(
        "celiaquia.models.RegistroErroneo.objects.filter",
        return_value=SimpleNamespace(exists=lambda: True, count=lambda: 2),
    )

    response = view.post(req, pk=1)
    assert response.status_code == 400


def test_recepcionar_view_permission_and_success_paths(mocker):
    """Recepcionar endpoint should enforce permissions and state validation."""
    view = module.RecepcionarExpedienteView()

    req_forbidden = SimpleNamespace(user=SimpleNamespace(), headers={"X-Requested-With": "XMLHttpRequest"})
    view.request = req_forbidden
    mocker.patch("celiaquia.views.expediente._is_admin", return_value=False)
    mocker.patch("celiaquia.views.expediente._user_in_group", return_value=False)
    resp_forbidden = view.post(req_forbidden, pk=1)
    assert resp_forbidden.status_code == 403

    req_ok = SimpleNamespace(user=SimpleNamespace(), headers={"X-Requested-With": "XMLHttpRequest"})
    view.request = req_ok
    mocker.patch("celiaquia.views.expediente._is_admin", return_value=True)
    expediente = SimpleNamespace(estado=SimpleNamespace(nombre="CONFIRMACION_DE_ENVIO"))
    mocker.patch("celiaquia.views.expediente.get_object_or_404", return_value=expediente)
    set_estado = mocker.patch("celiaquia.views.expediente._set_estado")
    resp_ok = view.post(req_ok, pk=1)
    assert resp_ok.status_code == 200
    assert set_estado.called


def test_asignar_tecnico_post_and_delete_paths(mocker):
    """Asignar técnico endpoint should validate input and support deletion."""
    view = module.AsignarTecnicoView()
    user = SimpleNamespace()

    req_missing = SimpleNamespace(user=user, POST={}, headers={"X-Requested-With": "XMLHttpRequest"})
    view.request = req_missing
    mocker.patch("celiaquia.views.expediente._is_admin", return_value=True)
    mocker.patch("celiaquia.views.expediente.get_object_or_404", return_value=SimpleNamespace(estado=SimpleNamespace(nombre="RECEPCIONADO")))
    resp_missing = view.post(req_missing, pk=1)
    assert resp_missing.status_code == 400

    tecnico = SimpleNamespace(username="tec", get_full_name=lambda: "")
    expediente = SimpleNamespace(estado=SimpleNamespace(nombre="RECEPCIONADO"))
    req_ok = SimpleNamespace(user=user, POST={"tecnico_id": "9"}, headers={"X-Requested-With": "XMLHttpRequest"})
    view.request = req_ok

    def _go404(obj, **kwargs):
        if obj is module.Expediente:
            return expediente
        return tecnico

    mocker.patch("celiaquia.views.expediente.get_object_or_404", side_effect=_go404)
    mocker.patch("celiaquia.views.expediente.User.objects.filter", return_value=SimpleNamespace())
    mocker.patch("celiaquia.views.expediente.AsignacionTecnico.objects.get_or_create")
    set_estado = mocker.patch("celiaquia.views.expediente._set_estado")
    resp_ok = view.post(req_ok, pk=1)
    assert resp_ok.status_code == 200
    assert set_estado.called

    req_delete = SimpleNamespace(user=user, GET={"tecnico_id": "9"})
    view.request = req_delete
    asignacion = SimpleNamespace(delete=mocker.Mock())
    mocker.patch("celiaquia.views.expediente.AsignacionTecnico.objects.get", return_value=asignacion)
    resp_del = view.delete(req_delete, pk=1)
    assert resp_del.status_code == 200


def test_subir_cruce_excel_and_revisar_legajo_branches(mocker):
    """Cruce and review endpoints should return expected JSON for core actions."""
    subir = module.SubirCruceExcelView()

    req_no_file = SimpleNamespace(user=SimpleNamespace(id=1), FILES={}, headers={})
    subir.request = req_no_file
    mocker.patch("celiaquia.views.expediente._is_admin", return_value=True)
    mocker.patch("celiaquia.views.expediente.get_object_or_404", return_value=SimpleNamespace(asignaciones_tecnicos=SimpleNamespace(all=lambda: [])))
    resp_no_file = subir.post(req_no_file, pk=1)
    assert resp_no_file.status_code == 400

    req_ok = SimpleNamespace(user=SimpleNamespace(id=1), FILES={"archivo": object()}, headers={})
    subir.request = req_ok
    mocker.patch("celiaquia.views.expediente.CruceService.procesar_cruce_por_cuit", return_value={"ok": 1})
    resp_ok = subir.post(req_ok, pk=1)
    assert resp_ok.status_code == 200

    revisar = module.RevisarLegajoView()
    expediente = SimpleNamespace(asignaciones_tecnicos=SimpleNamespace(all=lambda: [SimpleNamespace(tecnico_id=1)]))
    leg = SimpleNamespace(pk=3, revision_tecnico="PENDIENTE", estado_cupo="NO_EVAL", es_titular_activo=True, save=mocker.Mock(), delete=mocker.Mock())

    def _go404(obj, **kwargs):
        if obj is module.Expediente:
            return expediente
        return leg

    mocker.patch("celiaquia.views.expediente.get_object_or_404", side_effect=_go404)
    mocker.patch("celiaquia.views.expediente._user_in_group", side_effect=lambda _u, g: g == "TecnicoCeliaquia")
    mocker.patch("celiaquia.views.expediente._is_admin", return_value=False)
    mocker.patch("celiaquia.views.expediente.HistorialValidacionTecnica.objects.create")

    req_aprobar = SimpleNamespace(user=SimpleNamespace(id=1), POST={"accion": "APROBAR"})
    resp_ap = revisar.post(req_aprobar, pk=1, legajo_id=3)
    assert resp_ap.status_code == 200

    req_subs = SimpleNamespace(user=SimpleNamespace(id=1), POST={"accion": "SUBSANAR", "motivo": "faltan docs"})
    resp_sub = revisar.post(req_subs, pk=1, legajo_id=3)
    assert resp_sub.status_code == 200
