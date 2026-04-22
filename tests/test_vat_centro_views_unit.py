"""Tests unitarios para VAT.views.centro."""

from types import SimpleNamespace

from django.http import JsonResponse

from VAT.views import centro as module


class _QS:
    def __init__(self):
        self.filtered = False

    def filter(self, *_args, **_kwargs):
        self.filtered = True
        return self

    def order_by(self, *_args, **_kwargs):
        return self

    def only(self, *_args, **_kwargs):
        return self

    def values_list(self, *_args, **_kwargs):
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
    def __init__(self, *_args, **_kwargs):
        self.count = None
        self.num_pages = None

    def get_page(self, _page):
        return _Page()


def test_build_vat_centro_list_queryset_applies_scope_and_search(mocker):
    base_qs = _QS()
    mocker.patch(
        "VAT.views.centro._build_vat_centro_list_base_queryset",
        return_value=base_qs,
    )
    mocker.patch(
        "VAT.views.centro.filter_centros_queryset_for_user",
        return_value=base_qs,
    )
    adv = mocker.patch(
        "VAT.views.centro.BOOL_ADVANCED_FILTER.filter_queryset",
        side_effect=lambda queryset, _params: queryset,
    )

    request = SimpleNamespace(user=SimpleNamespace(), GET={"busqueda": "123"})

    assert module._build_vat_centro_list_queryset(request) is base_qs
    assert base_qs.filtered is True
    assert adv.called


def test_vat_centro_list_view_paginates_without_count(mocker):
    hydrate = mocker.patch(
        "VAT.views.centro._hydrate_vat_centro_page", return_value=["row-1", "row-2"]
    )
    view = module.CentroListView()
    view.request = SimpleNamespace(GET={"page": "1"})
    view.page_kwarg = "page"

    paginator, page_obj, object_list, is_paginated = view.paginate_queryset(_QS(), 10)

    assert paginator.count is None
    assert object_list == ["row-1", "row-2"]
    assert page_obj.object_list == ["row-1", "row-2"]
    assert hydrate.called
    assert is_paginated is False


def test_vat_centros_ajax_returns_json(mocker):
    mocker.patch("VAT.views.centro._build_vat_centro_list_queryset", return_value=_QS())
    mocker.patch(
        "VAT.views.centro._hydrate_vat_centro_page", return_value=["row-1", "row-2"]
    )
    mocker.patch("VAT.views.centro.NoCountPaginator", _PaginatorFake)
    mocker.patch("VAT.views.centro.can_user_create_centro", return_value=True)
    mocker.patch("VAT.views.centro.build_no_count_page_range", return_value=[1, "…"])
    mocker.patch(
        "django.template.loader.render_to_string", side_effect=["<rows>", "<pager>"]
    )

    request = SimpleNamespace(
        GET={"busqueda": "abc", "page": "1"},
        user=SimpleNamespace(is_authenticated=True),
    )

    response = module.centros_ajax(request)

    assert isinstance(response, JsonResponse)
    assert response.status_code == 200
