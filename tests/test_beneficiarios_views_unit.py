"""Tests unitarios para vistas de beneficiarios de Centro de Familia."""

from types import SimpleNamespace

from centrodefamilia.views import beneficiarios as module


class _QS:
    def values_list(self, *_args, **_kwargs):
        return [1, 2]


def test_responsable_list_view_pagina_sin_count_exacto(mocker):
    """Pagina responsables con NoCountPaginator e hidrata solo filas visibles."""
    hydrate = mocker.patch(
        "centrodefamilia.views.beneficiarios.hydrate_responsables_page",
        return_value=["row-1", "row-2"],
    )
    view = module.ResponsableListView()
    view.request = SimpleNamespace(GET={"page": "1"})
    view.page_kwarg = "page"

    paginator, page_obj, object_list, is_paginated = view.paginate_queryset(_QS(), 10)

    assert paginator.count is None
    assert object_list == ["row-1", "row-2"]
    assert page_obj.object_list == ["row-1", "row-2"]
    hydrate.assert_called_once_with([1, 2])
    assert is_paginated is False
