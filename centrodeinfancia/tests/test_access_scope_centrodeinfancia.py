from datetime import date

import pytest
from django.contrib.auth.models import User
from django.http import Http404
from django.test import RequestFactory

from ciudadanos.models import Ciudadano
from centrodeinfancia.models import (
    CentroDeInfancia,
    IntervencionCentroInfancia,
    NominaCentroInfancia,
    ObservacionCentroInfancia,
)
from centrodeinfancia.views import (
    CentroDeInfanciaDetailView,
    IntervencionCentroInfanciaUpdateView,
    NominaCentroInfanciaDeleteView,
    NominaCentroInfanciaDetailView,
    ObservacionCentroInfanciaDetailView,
    eliminar_archivo_intervencion_centrodeinfancia,
    nomina_centrodeinfancia_editar_ajax,
    subir_archivo_intervencion_centrodeinfancia,
)
from core.models import Provincia
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


def _crear_ciudadano(documento):
    return Ciudadano.objects.create(
        apellido="Perez",
        nombre="Juan",
        fecha_nacimiento=date(2010, 1, 1),
        documento=documento,
    )


@pytest.mark.django_db
def test_detalle_cdi_no_permite_centro_fuera_de_provincia():
    provincia_a = Provincia.objects.create(nombre="Buenos Aires")
    provincia_b = Provincia.objects.create(nombre="Cordoba")
    user = _crear_usuario("user-prov-a", provincia=provincia_a)
    centro_b = CentroDeInfancia.objects.create(nombre="CDI B", provincia=provincia_b)

    request = RequestFactory().get(f"/centrodeinfancia/detalle/{centro_b.pk}")
    request.user = user
    view = _build_view(CentroDeInfanciaDetailView, request, pk=centro_b.pk)

    with pytest.raises(Http404):
        view.get_object()


@pytest.mark.django_db
def test_nomina_detalle_no_permite_centro_fuera_de_provincia():
    provincia_a = Provincia.objects.create(nombre="Mendoza")
    provincia_b = Provincia.objects.create(nombre="Salta")
    user = _crear_usuario("user-prov-mza", provincia=provincia_a)
    centro_b = CentroDeInfancia.objects.create(
        nombre="CDI Salta", provincia=provincia_b
    )

    request = RequestFactory().get(f"/centrodeinfancia/{centro_b.pk}/nomina/")
    request.user = user
    view = _build_view(NominaCentroInfanciaDetailView, request, pk=centro_b.pk)

    with pytest.raises(Http404):
        view.get_queryset()


@pytest.mark.django_db
def test_intervencion_update_exige_pertenencia_al_centro_de_la_url():
    provincia = Provincia.objects.create(nombre="San Juan")
    user = _crear_usuario("user-global-1", provincia=None)
    centro_a = CentroDeInfancia.objects.create(nombre="CDI A", provincia=provincia)
    centro_b = CentroDeInfancia.objects.create(nombre="CDI B", provincia=provincia)
    intervencion = IntervencionCentroInfancia.objects.create(centro=centro_b)

    request = RequestFactory().get(
        f"/centrodeinfancia/intervencion/editar/{centro_a.pk}/{intervencion.pk}"
    )
    request.user = user
    view = _build_view(
        IntervencionCentroInfanciaUpdateView,
        request,
        pk=centro_a.pk,
        pk2=intervencion.pk,
    )

    with pytest.raises(Http404):
        view.get_object()


@pytest.mark.django_db
def test_nomina_delete_exige_pertenencia_al_centro_de_la_url():
    provincia = Provincia.objects.create(nombre="Entre Rios")
    user = _crear_usuario("user-global-2", provincia=None)
    centro_a = CentroDeInfancia.objects.create(nombre="CDI A", provincia=provincia)
    centro_b = CentroDeInfancia.objects.create(nombre="CDI B", provincia=provincia)
    ciudadano = _crear_ciudadano(documento=11111111)
    nomina = NominaCentroInfancia.objects.create(centro=centro_b, ciudadano=ciudadano)

    request = RequestFactory().post(
        f"/centrodeinfancia/{centro_a.pk}/nomina/{nomina.pk}/eliminar/"
    )
    request.user = user
    view = _build_view(
        NominaCentroInfanciaDeleteView,
        request,
        pk=centro_a.pk,
        pk2=nomina.pk,
    )

    with pytest.raises(Http404):
        view.get_object()


@pytest.mark.django_db
def test_observacion_detalle_respeta_scope_por_provincia():
    provincia_a = Provincia.objects.create(nombre="La Pampa")
    provincia_b = Provincia.objects.create(nombre="Neuquen")
    user = _crear_usuario("user-prov-lp", provincia=provincia_a)
    centro_b = CentroDeInfancia.objects.create(nombre="CDI NQN", provincia=provincia_b)
    observacion = ObservacionCentroInfancia.objects.create(
        centro=centro_b,
        observacion="Observación restringida",
    )

    request = RequestFactory().get(f"/centrodeinfancia/observacion/{observacion.pk}/")
    request.user = user
    view = _build_view(ObservacionCentroInfanciaDetailView, request, pk=observacion.pk)

    with pytest.raises(Http404):
        view.get_object()


@pytest.mark.django_db
def test_nomina_editar_ajax_no_permite_registro_fuera_de_scope():
    provincia_a = Provincia.objects.create(nombre="Chaco")
    provincia_b = Provincia.objects.create(nombre="Chubut")
    user = _crear_usuario("user-prov-chaco", provincia=provincia_a)
    centro_b = CentroDeInfancia.objects.create(nombre="CDI CHU", provincia=provincia_b)
    ciudadano = _crear_ciudadano(documento=22222222)
    nomina = NominaCentroInfancia.objects.create(centro=centro_b, ciudadano=ciudadano)

    request = RequestFactory().get(f"/centrodeinfancia/editar-nomina/{nomina.pk}/")
    request.user = user

    with pytest.raises(Http404):
        nomina_centrodeinfancia_editar_ajax(request, pk=nomina.pk)


@pytest.mark.django_db
def test_upload_documentacion_no_permite_intervencion_fuera_de_scope():
    provincia_a = Provincia.objects.create(nombre="Jujuy")
    provincia_b = Provincia.objects.create(nombre="Misiones")
    user = _crear_usuario("user-prov-jujuy", provincia=provincia_a)
    centro_b = CentroDeInfancia.objects.create(
        nombre="CDI Mision", provincia=provincia_b
    )
    intervencion = IntervencionCentroInfancia.objects.create(centro=centro_b)

    request = RequestFactory().post(
        f"/centrodeinfancia/intervencion/{intervencion.pk}/documentacion/subir/",
        data={},
    )
    request.user = user

    with pytest.raises(Http404):
        subir_archivo_intervencion_centrodeinfancia(request, intervencion.pk)


@pytest.mark.django_db
def test_eliminar_documentacion_no_permite_intervencion_fuera_de_scope():
    provincia_a = Provincia.objects.create(nombre="Tucuman")
    provincia_b = Provincia.objects.create(nombre="Formosa")
    user = _crear_usuario("user-prov-tuc", provincia=provincia_a)
    centro_b = CentroDeInfancia.objects.create(nombre="CDI FOR", provincia=provincia_b)
    intervencion = IntervencionCentroInfancia.objects.create(centro=centro_b)

    request = RequestFactory().post(
        f"/centrodeinfancia/intervencion/{intervencion.pk}/documentacion/eliminar/",
        data={},
    )
    request.user = user

    with pytest.raises(Http404):
        eliminar_archivo_intervencion_centrodeinfancia(request, intervencion.pk)

