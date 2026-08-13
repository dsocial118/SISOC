"""Tests del queryset liviano usado por el listado de comedores."""

from comedores.services.comedor_service.impl import (
    _build_comedores_list_values_queryset,
)


class _ValuesQuerysetSpy:
    def __init__(self):
        self.selected_values = ()

    def select_related(self, *_fields):
        return self

    def annotate(self, **_annotations):
        return self

    def values(self, *fields):
        self.selected_values = fields
        return self

    def order_by(self, *_fields):
        return self


def test_listado_selecciona_nombres_de_estado_proceso_y_detalle():
    queryset = _ValuesQuerysetSpy()

    _build_comedores_list_values_queryset(queryset)

    assert (
        "ultimo_estado__estado_general__estado_proceso__estado"
        in queryset.selected_values
    )
    assert (
        "ultimo_estado__estado_general__estado_detalle__estado"
        in queryset.selected_values
    )
    assert (
        "ultimo_estado__estado_general__estado_proceso" not in queryset.selected_values
    )
    assert (
        "ultimo_estado__estado_general__estado_detalle" not in queryset.selected_values
    )
