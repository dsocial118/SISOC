"""Tests de ordenamiento persistente para listados paginados."""

from django.http import QueryDict
from django.test import RequestFactory

from core.services.list_ordering import (
    apply_allowed_ordering,
    build_ordering_header,
)


class _QuerysetSpy:
    def __init__(self):
        self.ordering = None

    def order_by(self, *fields):
        self.ordering = fields
        return self


def test_apply_allowed_ordering_valida_campo_y_agrega_desempate():
    queryset = _QuerysetSpy()

    result = apply_allowed_ordering(
        queryset,
        QueryDict("ordering=-nombre"),
        {"nombre": "comedor__nombre"},
        default=("-creado",),
    )

    assert result is queryset
    assert queryset.ordering == ("-comedor__nombre", "pk")


def test_apply_allowed_ordering_usa_default_ante_parametro_desconocido():
    queryset = _QuerysetSpy()

    apply_allowed_ordering(
        queryset,
        QueryDict("ordering=campo_invalido"),
        {"nombre": "nombre"},
        default=("-id",),
    )

    assert queryset.ordering == ("-id",)


def test_build_ordering_header_conserva_filtros_y_descarta_pagina():
    request = RequestFactory().get(
        "/listado/",
        {"filters": '{"logic":"AND"}', "ordering": "nombre", "page": "3"},
    )

    header = build_ordering_header(request, key="nombre", title="Nombre")

    assert header["sort_direction"] == "asc"
    assert "ordering=-nombre" in header["sort_url"]
    assert "filters=" in header["sort_url"]
    assert "page=" not in header["sort_url"]
