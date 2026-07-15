from datetime import date

import pytest
from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.test import RequestFactory

from ciudadanos.models import Ciudadano
from centrodeinfancia.models import (
    CentroDeInfancia,
    AccesoCDI,
    IntervencionCentroInfancia,
    NominaCentroInfancia,
    ObservacionCentroInfancia,
    Trabajador,
)
from centrodeinfancia.access import aplicar_scope_centros_cdi
from centrodeinfancia.views import (
    CentroDeInfanciaDetailView,
    CentroDeInfanciaCreateView,
    IntervencionCentroInfanciaUpdateView,
    NominaCentroInfanciaDeleteView,
    NominaCentroInfanciaDetailView,
    ObservacionCentroInfanciaDetailView,
    eliminar_archivo_intervencion_centrodeinfancia,
    nomina_centrodeinfancia_editar_ajax,
    subir_archivo_intervencion_centrodeinfancia,
)
from centrodeinfancia.views_formulario_cdi import FormularioCDICreateView
from core.models import Localidad, Municipio, Provincia
from core.constants import UserGroups
from users.models import Profile, ProfileTerritorialScope


def _build_view(view_cls, request, **kwargs):
    view = view_cls()
    view.setup(request, **kwargs)
    return view


def _crear_usuario(username, provincia=None):
    user = User.objects.create_user(username=username, password="test1234")
    profile, _ = Profile.objects.get_or_create(user=user)
    profile.provincia = provincia
    profile.es_usuario_provincial = provincia is not None
    profile.save()
    if provincia:
        ProfileTerritorialScope.objects.create(profile=profile, provincia=provincia)
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


@pytest.mark.django_db
def test_scope_centros_cdi_municipio_no_habilita_toda_la_provincia():
    provincia = Provincia.objects.create(nombre="Rio Negro")
    municipio_scope = Municipio.objects.create(nombre="Viedma", provincia=provincia)
    municipio_fuera = Municipio.objects.create(nombre="Bariloche", provincia=provincia)
    localidad_scope = Localidad.objects.create(
        nombre="Viedma", municipio=municipio_scope
    )
    localidad_fuera = Localidad.objects.create(
        nombre="Bariloche", municipio=municipio_fuera
    )
    user = User.objects.create_user(username="cdi-municipio", password="test1234")
    profile = user.profile
    profile.es_usuario_provincial = True
    profile.save()
    ProfileTerritorialScope.objects.create(
        profile=profile,
        provincia=provincia,
        municipio=municipio_scope,
    )
    centro_visible = CentroDeInfancia.objects.create(
        nombre="CDI Viedma",
        provincia=provincia,
        municipio=municipio_scope,
        localidad=localidad_scope,
    )
    CentroDeInfancia.objects.create(
        nombre="CDI Bariloche",
        provincia=provincia,
        municipio=municipio_fuera,
        localidad=localidad_fuera,
    )

    centros = list(aplicar_scope_centros_cdi(CentroDeInfancia.objects.all(), user))

    assert centros == [centro_visible]


@pytest.mark.django_db
def test_scope_centros_cdi_localidad_no_habilita_otra_localidad():
    provincia = Provincia.objects.create(nombre="Santa Cruz")
    municipio = Municipio.objects.create(nombre="Rio Gallegos", provincia=provincia)
    localidad_scope = Localidad.objects.create(nombre="Centro", municipio=municipio)
    localidad_fuera = Localidad.objects.create(nombre="Sur", municipio=municipio)
    user = User.objects.create_user(username="cdi-localidad", password="test1234")
    profile = user.profile
    profile.es_usuario_provincial = True
    profile.save()
    ProfileTerritorialScope.objects.create(
        profile=profile,
        provincia=provincia,
        municipio=municipio,
        localidad=localidad_scope,
    )
    centro_visible = CentroDeInfancia.objects.create(
        nombre="CDI Centro",
        provincia=provincia,
        municipio=municipio,
        localidad=localidad_scope,
    )
    CentroDeInfancia.objects.create(
        nombre="CDI Sur",
        provincia=provincia,
        municipio=municipio,
        localidad=localidad_fuera,
    )

    centros = list(aplicar_scope_centros_cdi(CentroDeInfancia.objects.all(), user))

    assert centros == [centro_visible]


@pytest.mark.django_db
def test_scope_centros_cdi_provincial_sin_scopes_no_es_global():
    provincia = Provincia.objects.create(nombre="Tierra del Fuego")
    user = User.objects.create_user(username="cdi-sin-scope", password="test1234")
    profile = user.profile
    profile.es_usuario_provincial = True
    profile.provincia = None
    profile.save()
    CentroDeInfancia.objects.create(nombre="CDI Ushuaia", provincia=provincia)

    centros = list(aplicar_scope_centros_cdi(CentroDeInfancia.objects.all(), user))

    assert centros == []


@pytest.mark.django_db
def test_referente_cdi_no_ve_otro_centro():
    user = User.objects.create_user(username="referente-scope", password="test1234")
    centro_propio = CentroDeInfancia.objects.create(nombre="CDI Propio")
    CentroDeInfancia.objects.create(nombre="CDI Ajeno")
    AccesoCDI.objects.create(user=user, centro=centro_propio)

    centros = list(aplicar_scope_centros_cdi(CentroDeInfancia.objects.all(), user))

    assert centros == [centro_propio]


@pytest.mark.django_db
def test_trabajador_cdi_no_ve_otro_centro():
    user = User.objects.create_user(username="trabajador-scope", password="test1234")
    centro_propio = CentroDeInfancia.objects.create(nombre="CDI Trabajador propio")
    centro_ajeno = CentroDeInfancia.objects.create(nombre="CDI Trabajador ajeno")
    Trabajador.objects.create(
        centro=centro_propio,
        usuario=user,
        nombre="Ana",
        apellido="Lopez",
    )
    Trabajador.objects.create(
        centro=centro_ajeno,
        nombre="Otra",
        apellido="Persona",
    )

    centros = list(aplicar_scope_centros_cdi(CentroDeInfancia.objects.all(), user))

    assert centros == [centro_propio]


@pytest.mark.django_db
def test_egp_no_ve_centros_de_otra_provincia():
    provincia_propia = Provincia.objects.create(nombre="EGP propia")
    provincia_ajena = Provincia.objects.create(nombre="EGP ajena")
    user = User.objects.create_user(username="egp-scope", password="test1234")
    egp, _ = Group.objects.get_or_create(name=UserGroups.SIMEPI_EGP)
    user.groups.add(egp)
    profile = user.profile
    profile.es_usuario_provincial = True
    profile.save(update_fields=["es_usuario_provincial"])
    ProfileTerritorialScope.objects.create(profile=profile, provincia=provincia_propia)
    centro_propio = CentroDeInfancia.objects.create(
        nombre="CDI EGP propio", provincia=provincia_propia
    )
    CentroDeInfancia.objects.create(nombre="CDI EGP ajeno", provincia=provincia_ajena)

    centros = list(aplicar_scope_centros_cdi(CentroDeInfancia.objects.all(), user))

    assert centros == [centro_propio]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "group_name",
    [UserGroups.SIMEPI_ADMINISTRADOR, UserGroups.SIMEPI_ANALISTA_DATOS],
)
def test_admin_y_analista_tienen_alcance_amplio(group_name):
    user = User.objects.create_user(username=f"scope-{group_name}", password="test1234")
    group, _ = Group.objects.get_or_create(name=group_name)
    user.groups.add(group)
    provincia_a = Provincia.objects.create(nombre=f"Amplio A {group_name}")
    provincia_b = Provincia.objects.create(nombre=f"Amplio B {group_name}")
    profile = user.profile
    profile.es_usuario_provincial = True
    profile.save(update_fields=["es_usuario_provincial"])
    ProfileTerritorialScope.objects.create(profile=profile, provincia=provincia_a)
    centro_a = CentroDeInfancia.objects.create(
        nombre="CDI amplio A", provincia=provincia_a
    )
    centro_b = CentroDeInfancia.objects.create(
        nombre="CDI amplio B", provincia=provincia_b
    )

    centros = list(aplicar_scope_centros_cdi(CentroDeInfancia.objects.all(), user))

    assert set(centros) == {centro_a, centro_b}


@pytest.mark.django_db
def test_auditoria_no_puede_mutar_centro():
    user = User.objects.create_user(username="auditoria-solo-lectura", password="test1234")
    auditoria, _ = Group.objects.get_or_create(name=UserGroups.SIMEPI_AUDITORIA)
    user.groups.add(auditoria)
    request = RequestFactory().post("/centrodeinfancia/crear")
    request.user = user
    view = _build_view(CentroDeInfanciaCreateView, request)

    with pytest.raises(PermissionDenied):
        view.dispatch(request)


@pytest.mark.django_db
def test_auditoria_no_puede_mutar_formulario_cdi():
    user = User.objects.create_user(
        username="auditoria-formulario-solo-lectura",
        password="test1234",
    )
    auditoria, _ = Group.objects.get_or_create(name=UserGroups.SIMEPI_AUDITORIA)
    user.groups.add(auditoria)
    request = RequestFactory().post("/centrodeinfancia/1/formularios/crear/")
    request.user = user
    view = _build_view(FormularioCDICreateView, request, pk=1)

    with pytest.raises(PermissionDenied):
        view.post(request)
