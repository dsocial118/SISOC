"""Tests unitarios para organizaciones.views."""

import json
from types import SimpleNamespace

from django.forms import ValidationError
from django.http import JsonResponse

from organizaciones import views as module


class _QS:
    def __init__(self):
        self.calls = []

    def filter(self, *args, **kwargs):
        self.calls.append(("filter", args, kwargs))
        return self

    def select_related(self, *args, **kwargs):
        self.calls.append(("select_related", args, kwargs))
        return self

    def annotate(self, *args, **kwargs):
        self.calls.append(("annotate", args, kwargs))
        return self

    def only(self, *args, **kwargs):
        self.calls.append(("only", args, kwargs))
        return self

    def order_by(self, *args, **kwargs):
        self.calls.append(("order_by", args, kwargs))
        return self

    def values_list(self, *args, **kwargs):
        self.calls.append(("values_list", args, kwargs))
        return [1, 2]


class _Page:
    def __init__(self):
        self.object_list = [1, 2]
        self.number = 1

    def has_previous(self):
        return False

    def has_next(self):
        return True

    def has_other_pages(self):
        return True


class _PaginatorFake:
    def __init__(self, _items, _per_page):
        self.count = None
        self.num_pages = None
        self._page = _Page()

    def get_page(self, page):
        if page == "bad":
            page = 1
        return self._page


def test_organizacion_list_view_uses_shared_builder(mocker):
    builder = mocker.patch(
        "organizaciones.views._build_organizacion_list_queryset", return_value="qs"
    )

    view = module.OrganizacionListView()
    view.request = SimpleNamespace(GET={"busqueda": "abc"})
    assert view.get_queryset() == "qs"
    builder.assert_called_once_with("abc")


def test_organizacion_list_view_paginates_without_count(mocker):
    hydrate = mocker.patch(
        "organizaciones.views._hydrate_organizaciones_page",
        return_value=["row1", "row2"],
    )
    view = module.OrganizacionListView()
    view.request = SimpleNamespace(GET={"page": "2"})
    view.page_kwarg = "page"

    paginator, page_obj, object_list, is_paginated = view.paginate_queryset(_QS(), 10)

    assert paginator.count is None
    assert object_list == ["row1", "row2"]
    assert page_obj.object_list == ["row1", "row2"]
    assert hydrate.called
    assert is_paginated is False


def test_organizacion_list_context_adds_page_range_for_no_count(mocker):
    page_obj = SimpleNamespace(
        paginator=SimpleNamespace(count=None),
        number=2,
        has_next=lambda: True,
    )
    mocker.patch(
        "django.views.generic.list.ListView.get_context_data",
        return_value={"page_obj": page_obj},
    )
    range_builder = mocker.patch(
        "organizaciones.views.build_no_count_page_range", return_value=[1, 2, "…"]
    )

    view = module.OrganizacionListView()
    view.request = SimpleNamespace(GET={"busqueda": "abc"})

    ctx = view.get_context_data()
    assert ctx["query"] == "abc"
    assert ctx["page_range"] == [1, 2, "…"]
    range_builder.assert_called_once_with(page_obj)


def test_firmante_create_roles_form_and_valid_paths(mocker):
    view = module.FirmanteCreateView()

    # get_allowed_roles_queryset branches
    none_qs = mocker.patch(
        "organizaciones.views.RolFirmante.objects.none", return_value="none"
    )
    all_qs = mocker.patch(
        "organizaciones.views.RolFirmante.objects.all", return_value="all"
    )
    filt = mocker.patch(
        "organizaciones.views.RolFirmante.objects.filter", return_value="filtered"
    )

    assert view.get_allowed_roles_queryset(None) == "none"
    org_pj = SimpleNamespace(tipo_entidad=SimpleNamespace(nombre="Personería jurídica"))
    assert view.get_allowed_roles_queryset(org_pj) == "filtered"
    assert filt.called

    org_other = SimpleNamespace(tipo_entidad=SimpleNamespace(nombre="Otro"))
    assert view.get_allowed_roles_queryset(org_other) == "all"
    assert none_qs.called and all_qs.called

    # get_form should set queryset according to organization
    form = SimpleNamespace(fields={"rol": SimpleNamespace(queryset=None)})
    mocker.patch("django.views.generic.edit.ModelFormMixin.get_form", return_value=form)
    mocker.patch(
        "organizaciones.views.Organizacion.objects.select_related",
        return_value=SimpleNamespace(get=lambda **kwargs: org_pj),
    )
    mocker.patch.object(view, "get_allowed_roles_queryset", return_value="roles")
    view.request = SimpleNamespace(GET={"organizacion": "1"}, POST={})
    view.kwargs = {}
    out_form = view.get_form()
    assert out_form.fields["rol"].queryset == "roles"

    # form_valid: missing organizacion id
    bad_form = SimpleNamespace(
        cleaned_data={"rol": None}, instance=SimpleNamespace(), add_error=mocker.Mock()
    )
    view.request = SimpleNamespace(POST={}, GET={})
    view.kwargs = {}
    mocker.patch("organizaciones.views.messages.error")
    mocker.patch.object(view, "form_invalid", return_value="invalid")
    assert view.form_valid(bad_form) == "invalid"

    # form_valid: duplicate rol
    dup_form = SimpleNamespace(
        cleaned_data={"rol": "R"},
        instance=SimpleNamespace(),
        add_error=mocker.Mock(),
    )
    view.request = SimpleNamespace(POST={"organizacion_id": "9"}, GET={})
    mocker.patch(
        "organizaciones.views.Firmante.objects.filter",
        return_value=SimpleNamespace(exists=lambda: True),
    )
    assert view.form_valid(dup_form) == "invalid"
    assert dup_form.add_error.called

    # form_valid: success + guardar_otro
    ok_form = SimpleNamespace(
        cleaned_data={"rol": "R"},
        instance=SimpleNamespace(organizacion_id=None),
        save=lambda: SimpleNamespace(organizacion=SimpleNamespace(pk=5)),
    )
    view.request = SimpleNamespace(
        POST={"organizacion_id": "9", "guardar_otro": "1"}, GET={}
    )
    mocker.patch(
        "organizaciones.views.Firmante.objects.filter",
        return_value=SimpleNamespace(exists=lambda: False),
    )
    resp = view.form_valid(ok_form)
    assert resp.status_code == 302


def test_aval_create_view_form_valid_paths(mocker):
    view = module.AvalCreateView()
    mocker.patch("organizaciones.views.messages.error")
    mocker.patch.object(view, "form_invalid", return_value="invalid")

    form_missing = SimpleNamespace(instance=SimpleNamespace(), save=lambda: None)
    view.request = SimpleNamespace(POST={}, GET={})
    view.kwargs = {}
    assert view.form_valid(form_missing) == "invalid"

    form_ok = SimpleNamespace(
        instance=SimpleNamespace(organizacion_id=None),
        save=lambda: SimpleNamespace(organizacion=SimpleNamespace(pk=3)),
    )
    view.request = SimpleNamespace(
        POST={"organizacion_id": "3", "guardar_otro": "1"}, GET={}
    )
    out = view.form_valid(form_ok)
    assert out.status_code == 302


def test_organizacion_delete_post_success_and_validation_error(mocker):
    view = module.OrganizacionDeleteView()
    obj = SimpleNamespace(nombre="Org", delete=mocker.Mock())
    view.success_url = "/ok"

    req = SimpleNamespace()
    msg_success = mocker.patch("organizaciones.views.messages.success")
    msg_error = mocker.patch("organizaciones.views.messages.error")
    mocker.patch.object(view, "get_object", return_value=obj)
    mocker.patch.object(view, "render_to_response", return_value="rendered")
    mocker.patch.object(view, "get_context_data", return_value={})

    ok = view.post(req)
    assert ok.status_code == 302
    assert msg_success.called

    obj2 = SimpleNamespace(
        nombre="Org2", delete=mocker.Mock(side_effect=ValidationError("bad"))
    )
    mocker.patch.object(view, "get_object", return_value=obj2)
    err = view.post(req)
    assert err == "rendered"
    assert msg_error.called


def test_ajax_views_subtipo_and_organizaciones(mocker):
    # sub_tipo_entidad_ajax
    subtipos = [SimpleNamespace(id=1, nombre="Sub1")]
    mocker.patch(
        "organizaciones.views.SubtipoEntidad.objects.filter",
        return_value=SimpleNamespace(order_by=lambda *_a, **_k: subtipos),
    )
    req = SimpleNamespace(
        GET={"tipo_entidad": "2"}, user=SimpleNamespace(is_authenticated=True)
    )
    resp = module.sub_tipo_entidad_ajax.__wrapped__(req)
    assert isinstance(resp, JsonResponse)
    assert resp.status_code == 200

    # organizaciones_ajax con paginacion sin count exacto
    org_qs = _QS()
    mocker.patch(
        "organizaciones.views._build_organizacion_list_queryset", return_value=org_qs
    )
    mocker.patch(
        "organizaciones.views._hydrate_organizaciones_page",
        return_value=["org-1", "org-2"],
    )
    mocker.patch("organizaciones.views.NoCountPaginator", _PaginatorFake)
    mocker.patch(
        "organizaciones.views.build_no_count_page_range", return_value=[1, "…"]
    )
    mocker.patch(
        "organizaciones.views.render_to_string", side_effect=["<rows>", "<pager>"]
    )

    req2 = SimpleNamespace(
        GET={"busqueda": "abc", "page": "bad"},
        user=SimpleNamespace(is_authenticated=True),
    )
    out = module.organizaciones_ajax.__wrapped__(req2)
    assert out.status_code == 200
    payload = json.loads(out.content)
    assert payload["count"] is None
