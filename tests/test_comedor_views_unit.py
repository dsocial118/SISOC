"""Tests unitarios para comedores.views.comedor."""

import contextlib
from types import SimpleNamespace

from comedores.views import comedor as module


class _Req:
    def __init__(self, user=None, post=None, files=None):
        self.user = user or SimpleNamespace(is_superuser=False)
        self.POST = post or {}
        self.FILES = files or SimpleNamespace(getlist=lambda _k: [])


def test_comedor_list_queryset_and_context(mocker):
    view = module.ComedorListView()
    req = _Req(user=SimpleNamespace(), post={})
    view.request = req

    get_filtered = mocker.patch(
        "comedores.views.comedor.ComedorService.get_filtered_comedores",
        return_value="qs",
    )
    assert view.get_queryset() == "qs"
    get_filtered.assert_called_once_with(req, user=req.user)

    mocker.patch("django.views.generic.list.ListView.get_context_data", return_value={})
    mocker.patch(
        "comedores.views.comedor.reverse", side_effect=lambda name, **_k: f"/{name}/"
    )
    mocker.patch(
        "comedores.views.comedor.get_filters_ui_config", return_value={"ok": 1}
    )
    mocker.patch(
        "comedores.views.comedor.build_columns_context_from_fields",
        return_value={"column_active_keys": ["nombre"], "columns": ["x"]},
    )

    ctx = view.get_context_data()
    assert ctx["add_url"] == "/comedor_crear/"
    assert ctx["filters_mode"] is True
    assert ctx["active_columns"] == ["nombre"]


def test_comedor_create_helpers_and_form_valid_paths(mocker):
    view = module.ComedorCreateView()
    user = SimpleNamespace(id=1)
    req = _Req(
        user=user,
        files=SimpleNamespace(getlist=lambda _k: ["img1", "img2"]),
    )
    view.request = req

    mocker.patch(
        "django.views.generic.edit.ModelFormMixin.get_form_kwargs", return_value={}
    )
    kwargs = view.get_form_kwargs()
    assert kwargs["user"] is user

    mocker.patch(
        "django.views.generic.edit.FormMixin.get_context_data", return_value={}
    )
    rf = mocker.patch("comedores.views.comedor.ReferenteForm", return_value="rform")
    ctx = view.get_context_data()
    assert ctx["referente_form"] == "rform"
    assert rf.called

    # form_valid success
    ref_form = SimpleNamespace(is_valid=lambda: True, save=lambda: "ref")
    mocker.patch.object(
        view, "get_context_data", return_value={"referente_form": ref_form}
    )
    mocker.patch(
        "comedores.views.comedor.transaction.atomic",
        return_value=contextlib.nullcontext(),
    )
    create_img = mocker.patch("comedores.views.comedor.ComedorService.create_imagenes")
    super_valid = mocker.patch(
        "django.views.generic.edit.ModelFormMixin.form_valid", return_value="ok"
    )

    form = SimpleNamespace(
        instance=SimpleNamespace(referente=None),
        save=lambda: SimpleNamespace(pk=9),
        add_error=mocker.Mock(),
    )
    assert view.form_valid(form) == "ok"
    assert create_img.call_count == 2
    assert super_valid.called

    # form_valid invalid referente
    bad_ref = SimpleNamespace(is_valid=lambda: False)
    mocker.patch.object(
        view, "get_context_data", return_value={"referente_form": bad_ref}
    )
    mocker.patch.object(view, "form_invalid", return_value="invalid")
    assert view.form_valid(form) == "invalid"


def test_comedor_detail_get_object_presupuestos_and_post_paths(mocker):
    view = module.ComedorDetailView()
    view.kwargs = {"pk": 7}

    get_obj = mocker.patch(
        "comedores.views.comedor.ComedorService.get_comedor_detail_object",
        return_value="obj",
    )
    assert view.get_object() == "obj"
    get_obj.assert_called_once_with(7)

    # get_presupuestos_data cache hit
    view.object = SimpleNamespace(id=1, relevamientos_optimized=[1])
    mocker.patch("comedores.views.comedor.cache.get", return_value=(1, 2, 3, 4, 5, 6))
    data = view.get_presupuestos_data()
    assert data["count_beneficiarios"] == 1
    assert data["monto_prestacion_mensual"] == 6

    # post descartar_expediente sin permisos
    req = _Req(
        user=SimpleNamespace(is_superuser=False),
        post={"action": "descartar_expediente"},
    )
    view.get_object = lambda: SimpleNamespace(pk=7)
    err = mocker.patch("comedores.views.comedor.messages.error")
    mocker.patch("comedores.views.comedor.redirect", return_value="redir")
    assert view.post(req) == "redir"
    assert err.called

    # post descartar_expediente con permisos y datos completos
    admision = SimpleNamespace(
        enviada_a_archivo=False,
        motivo_descarte_expediente=None,
        fecha_descarte_expediente=None,
        estado=None,
        estado_legales=None,
        save=mocker.Mock(),
    )
    req2 = _Req(
        user=SimpleNamespace(is_superuser=True),
        post={
            "action": "descartar_expediente",
            "admision_id": "11",
            "motivo_descarte": "x",
        },
    )
    view.get_object = lambda: SimpleNamespace(pk=7)
    mocker.patch("comedores.views.comedor.Admision.objects.get", return_value=admision)
    mocker.patch(
        "comedores.views.comedor.EstadoAdmision.objects.get_or_create",
        return_value=("desc", True),
    )
    success = mocker.patch("comedores.views.comedor.messages.success")
    mocker.patch("comedores.views.comedor.redirect", return_value="redir2")
    assert view.post(req2) == "redir2"
    assert success.called
