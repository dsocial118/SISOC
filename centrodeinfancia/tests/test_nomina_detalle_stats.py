from datetime import date

import pytest
from django.contrib.auth.models import User
from django.test import RequestFactory

from ciudadanos.models import Ciudadano
from centrodeinfancia.models import CentroDeInfancia, NominaCentroInfancia
from centrodeinfancia.views import (
    CentroDeInfanciaDetailView,
    NominaCentroInfanciaDetailView,
)
from core.models import Provincia, Sexo
from users.models import Profile


def _build_view(view_cls, request, **kwargs):
    view = view_cls()
    view.setup(request, **kwargs)
    return view


def _crear_usuario(username, provincia=None):
    user = User.objects.create_user(username=username, password="test1234")
    profile, _ = Profile.objects.get_or_create(user=user)
    profile.provincia = provincia
    profile.save()
    return user


@pytest.mark.django_db
def test_detalle_cdi_y_nomina_exponen_conteo_genero_x():
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    sexo_x = Sexo.objects.create(sexo="X")
    user = _crear_usuario("user-cdi-genero-x", provincia=provincia)
    centro = CentroDeInfancia.objects.create(nombre="CDI Test", provincia=provincia)
    ciudadano = Ciudadano.objects.create(
        apellido="Perez",
        nombre="Alex",
        fecha_nacimiento=date(2012, 1, 1),
        documento=12345678,
        sexo=sexo_x,
    )
    NominaCentroInfancia.objects.create(
        centro=centro,
        ciudadano=ciudadano,
        estado=NominaCentroInfancia.ESTADO_ACTIVO,
    )

    detail_request = RequestFactory().get(f"/centrodeinfancia/detalle/{centro.pk}")
    detail_request.user = user
    detail_view = _build_view(CentroDeInfanciaDetailView, detail_request, pk=centro.pk)
    detail_view.object = centro
    detail_context = detail_view.get_context_data()

    assert detail_context["nomina_x"] == 1
    assert detail_context["nomina_resumen"]["x"] == 1

    nomina_request = RequestFactory().get(f"/centrodeinfancia/{centro.pk}/nomina/")
    nomina_request.user = user
    nomina_view = _build_view(
        NominaCentroInfanciaDetailView,
        nomina_request,
        pk=centro.pk,
    )
    nomina_view.object_list = nomina_view.get_queryset()
    nomina_view.object = centro
    nomina_context = nomina_view.get_context_data()

    assert nomina_context["nominaX"] == 1
