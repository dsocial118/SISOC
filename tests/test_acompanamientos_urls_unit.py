"""Regresiones unitarias para el wiring de acompanamientos.urls."""

from django.urls import resolve, reverse

from acompanamientos import views as module


def test_lista_comedores_acompanamiento_resuelve_a_la_view_real():
    match = resolve(reverse("lista_comedores_acompanamiento"))

    assert match.func.view_class is module.ComedoresAcompanamientoListView


def test_detalle_acompanamiento_resuelve_a_la_view_real():
    match = resolve(reverse("detalle_acompanamiento", kwargs={"comedor_id": 5}))

    assert match.func.view_class is module.AcompanamientoDetailView
