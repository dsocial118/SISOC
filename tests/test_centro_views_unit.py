"""Tests unitarios para centrodefamilia.views.centro."""

from types import SimpleNamespace

import pytest
from django.core.exceptions import PermissionDenied
from django.http import Http404, JsonResponse

from centrodefamilia.views import centro as module


class _Groups:
    def __init__(self, names=None):
        self.names = set(names or [])
        self._last = None

    def filter(self, name):
        self._last = name
        return self

    def exists(self):
        return self._last in self.names


class _QS:
    def __init__(self):
        self.filtered = False

    def order_by(self, *_a, **_k):
        return self

    def filter(self, *_a, **_k):
        self.filtered = True
        return self

    def select_related(self, *_a, **_k):
        return self

    def annotate(self, *_a, **_k):
        return self

    def exclude(self, *_a, **_k):
        return self

    def only(self, *_a, **_k):
        return self

    def count(self):
        return 0

    def distinct(self):
        return self


class _Page:
    number = 1

    def has_previous(self):
        return False

    def has_next(self):
        return True

    def has_other_pages(self):
        return False


class _PaginatorFake:
    def __init__(self, *_a, **_k):
        self.count = 1
        self.num_pages = 1

    def get_page(self, page):
        if page == "boom":
            raise ValueError("bad page")
        return _Page()


def test_centro_list_get_queryset_permissions_and_filter(mocker):
    base_qs = _QS()
    mocker.patch("centrodefamilia.views.centro.Centro.objects.select_related", return_value=base_qs)
    none_qs = mocker.patch("centrodefamilia.views.centro.Centro.objects.none", return_value="none")
    adv = mocker.patch("centrodefamilia.views.centro.BOOL_ADVANCED_FILTER.filter_queryset", return_value="filtered")

    # superuser
    view = module.CentroListView()
    view.request = SimpleNamespace(user=SimpleNamespace(is_superuser=True, groups=_Groups()), GET={"busqueda": "abc"})
    assert view.get_queryset() == "filtered"
    assert adv.called

    # referente
    view_ref = module.CentroListView()
    view_ref.request = SimpleNamespace(
        user=SimpleNamespace(is_superuser=False, groups=_Groups({"ReferenteCentro"})),
        GET={},
    )
    assert view_ref.get_queryset() == "filtered"
    assert base_qs.filtered is True

    # sin permisos
    view_no = module.CentroListView()
    view_no.request = SimpleNamespace(user=SimpleNamespace(is_superuser=False, groups=_Groups()), GET={})
    assert view_no.get_queryset() == "none"
    assert none_qs.called


def test_centro_list_get_context_data_can_add_and_buttons(mocker):
    mocker.patch("django.views.generic.list.ListView.get_context_data", return_value={})
    mocker.patch("centrodefamilia.views.centro.reverse", side_effect=lambda name: f"/{name}/")
    mocker.patch("centrodefamilia.views.centro.get_centro_filters_ui_config", return_value={"ok": 1})

    view = module.CentroListView()
    view.request = SimpleNamespace(user=SimpleNamespace(is_superuser=False, groups=_Groups({"CDF SSE"})))
    ctx = view.get_context_data()

    assert ctx["can_add"] is True
    assert len(ctx["table_headers"]) == 6
    assert len(ctx["centro_additional_buttons"]) == 2


def test_centro_create_helpers_and_form_valid(mocker):
    view = module.CentroCreateView()
    view.request = SimpleNamespace(
        GET={"faro": "10"},
        user=SimpleNamespace(),
    )

    mocker.patch("django.views.generic.edit.FormMixin.get_initial", return_value={})
    mocker.patch("django.views.generic.edit.FormMixin.get_form_kwargs", return_value={})
    super_valid = mocker.patch("django.views.generic.edit.ModelFormMixin.form_valid", return_value="ok")
    success = mocker.patch("centrodefamilia.views.centro.messages.success")

    initial = view.get_initial()
    assert initial["tipo"] == "adherido"
    assert initial["faro_asociado"] == "10"

    kwargs = view.get_form_kwargs()
    assert kwargs["from_faro"] is True

    form = SimpleNamespace(cleaned_data={"tipo": "adherido"}, instance=SimpleNamespace(faro_asociado_id=None))
    assert view.form_valid(form) == "ok"
    assert form.instance.faro_asociado_id == "10"
    assert super_valid.called and success.called


def test_centro_update_delete_permissions_and_success_url(mocker):
    user = SimpleNamespace(
        id=5,
        is_superuser=False,
        is_authenticated=True,
        groups=_Groups({"CDF SSE"}),
    )
    request = SimpleNamespace(user=user)
    obj = SimpleNamespace(referente_id=1, pk=7)

    view_upd = module.CentroUpdateView()
    view_upd.request = request
    view_upd.kwargs = {}
    view_upd.object = obj
    mocker.patch.object(view_upd, "get_object", return_value=obj)
    mocker.patch("django.views.generic.base.View.dispatch", return_value="ok")
    mocker.patch("centrodefamilia.views.centro.reverse", return_value="/detail/7/")
    assert view_upd.dispatch(request) == "ok"
    assert view_upd.get_success_url() == "/detail/7/"

    view_del = module.CentroDeleteView()
    view_del.request = request
    mocker.patch.object(view_del, "get_object", return_value=obj)
    mocker.patch("django.views.generic.base.View.dispatch", return_value="ok")
    assert view_del.dispatch(request) == "ok"

    bad_user = SimpleNamespace(
        id=99,
        is_superuser=False,
        is_authenticated=True,
        groups=_Groups(),
    )
    bad_req = SimpleNamespace(user=bad_user)
    view_bad = module.CentroUpdateView()
    mocker.patch.object(view_bad, "get_object", return_value=obj)
    with pytest.raises(PermissionDenied):
        view_bad.dispatch(bad_req)


def test_informe_cabal_archivo_por_centro_detail_context_paths(mocker):
    view = module.InformeCabalArchivoPorCentroDetailView()
    view.object = SimpleNamespace(id=1)

    # centro_id inválido
    view.kwargs = {"centro_id": "x"}
    mocker.patch("django.views.generic.detail.DetailView.get_context_data", return_value={})
    with pytest.raises(Http404):
        view.get_context_data()

    # centro_id válido + fallback de paginación
    view.kwargs = {"centro_id": "2"}
    view.request = SimpleNamespace(GET={"page": "boom"})
    mocker.patch("centrodefamilia.views.centro.get_object_or_404", return_value="centro")
    mocker.patch(
        "centrodefamilia.views.centro.InformeCabalRegistro.objects.filter",
        return_value=_QS(),
    )
    mocker.patch("centrodefamilia.views.centro.Paginator", _PaginatorFake)

    ctx = view.get_context_data()
    assert ctx["centro"] == "centro"
    assert hasattr(ctx["registros"], "number")


def test_centros_ajax_returns_json(mocker):
    qs = _QS()
    mocker.patch("centrodefamilia.views.centro.Centro.objects.select_related", return_value=qs)
    mocker.patch("centrodefamilia.views.centro.Centro.objects.none", return_value=_QS())
    mocker.patch("django.template.loader.render_to_string", side_effect=["<rows>", "<pag>"])
    mocker.patch("django.core.paginator.Paginator", _PaginatorFake)

    request = SimpleNamespace(
        GET={"busqueda": "abc", "page": "1"},
        user=SimpleNamespace(is_superuser=True, groups=_Groups()),
    )
    response = module.centros_ajax(request)
    assert isinstance(response, JsonResponse)
    assert response.status_code == 200
