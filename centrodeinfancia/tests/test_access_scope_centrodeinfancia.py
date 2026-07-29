from datetime import date

import pytest
from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.test import RequestFactory
from django.urls import reverse

from ciudadanos.models import Ciudadano
from centrodeinfancia.models import (
    CentroDeInfancia,
    AccesoCDI,
    DepartamentoIpi,
    IntervencionCentroInfancia,
    NominaCentroInfancia,
    ObservacionCentroInfancia,
    OfertaServicio,
    Trabajador,
)
from centrodeinfancia.tests.test_centrodeinfancia_form import (
    datos_validos as _datos_validos_cdi,
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
from users.services_group_permissions import sync_permissions_for_group


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


def _payload_cdi_scope(provincia_ubicacion, **overrides):
    """Payload completo de CDI con ubicación bajo `provincia_ubicacion`.

    Los campos de ubicación son obligatorios y el form valida el departamento contra
    el queryset de la provincia efectiva (la del scope, no la posteada), así que la
    ubicación debe pertenecer a esa provincia. `provincia` se puede sobrescribir para
    simular el intento de cargar en otra jurisdicción.
    """

    departamento = DepartamentoIpi.objects.create(
        codigo_departamento=f"D{provincia_ubicacion.pk:04d}",
        provincia=provincia_ubicacion,
        nombre=f"Depto {provincia_ubicacion.pk}",
        decil_ipi=3,
    )
    municipio = Municipio.objects.create(
        nombre=f"Muni {provincia_ubicacion.pk}", provincia=provincia_ubicacion
    )
    localidad = Localidad.objects.create(
        nombre=f"Loc {provincia_ubicacion.pk}", municipio=municipio
    )
    servicio, _ = OfertaServicio.objects.get_or_create(
        codigo="multiedad", defaults={"orden": 5}
    )
    ubicacion = {
        "provincia": provincia_ubicacion,
        "departamento": departamento,
        "municipio": municipio,
        "localidad": localidad,
    }
    return _datos_validos_cdi(ubicacion, servicio, **overrides)


def _crear_ciudadano(documento):
    return Ciudadano.objects.create(
        apellido="Perez",
        nombre="Juan",
        fecha_nacimiento=date(2010, 1, 1),
        documento=documento,
    )


def _asignar_grupo_con_permisos(user, group_name):
    group, _ = Group.objects.get_or_create(name=group_name)
    sync_permissions_for_group(group)
    user.groups.add(group)


def _assert_read_scope_por_centro(client, centro_propio, centro_ajeno):
    trabajador_propio = Trabajador.objects.create(
        centro=centro_propio,
        nombre="Trabajador",
        apellido="Propio",
    )
    trabajador_ajeno = Trabajador.objects.create(
        centro=centro_ajeno,
        nombre="Trabajador",
        apellido="Ajeno",
    )
    paths = (
        (
            reverse("centrodeinfancia_detalle", kwargs={"pk": centro_propio.pk}),
            reverse("centrodeinfancia_detalle", kwargs={"pk": centro_ajeno.pk}),
        ),
        (
            reverse(
                "centrodeinfancia_trabajador_ver",
                kwargs={"pk": centro_propio.pk, "trabajador_id": trabajador_propio.pk},
            ),
            reverse(
                "centrodeinfancia_trabajador_ver",
                kwargs={"pk": centro_ajeno.pk, "trabajador_id": trabajador_ajeno.pk},
            ),
        ),
        (
            reverse("centrodeinfancia_nomina_ver", kwargs={"pk": centro_propio.pk}),
            reverse("centrodeinfancia_nomina_ver", kwargs={"pk": centro_ajeno.pk}),
        ),
        (
            reverse(
                "centrodeinfancia_formulario_listado",
                kwargs={"pk": centro_propio.pk},
            ),
            reverse(
                "centrodeinfancia_formulario_listado",
                kwargs={"pk": centro_ajeno.pk},
            ),
        ),
    )

    for own_path, foreign_path in paths:
        assert client.get(own_path).status_code == 200
        assert client.get(foreign_path).status_code == 404


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
    user = User.objects.create_user(
        username="auditoria-solo-lectura", password="test1234"
    )
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


@pytest.mark.django_db
def test_egp_respeta_scope_en_vistas_de_lectura(client):
    provincia_propia = Provincia.objects.create(nombre="EGP URL propia")
    provincia_ajena = Provincia.objects.create(nombre="EGP URL ajena")
    centro_propio = CentroDeInfancia.objects.create(
        nombre="CDI EGP URL propio",
        provincia=provincia_propia,
    )
    centro_ajeno = CentroDeInfancia.objects.create(
        nombre="CDI EGP URL ajeno",
        provincia=provincia_ajena,
    )
    user = _crear_usuario("egp-url", provincia=provincia_propia)
    _asignar_grupo_con_permisos(user, UserGroups.SIMEPI_EGP)
    client.force_login(user)

    _assert_read_scope_por_centro(client, centro_propio, centro_ajeno)


@pytest.mark.django_db
def test_referente_respeta_scope_en_vistas_de_lectura(client):
    centro_propio = CentroDeInfancia.objects.create(nombre="CDI referente URL propio")
    centro_ajeno = CentroDeInfancia.objects.create(nombre="CDI referente URL ajeno")
    user = _crear_usuario("referente-url")
    _asignar_grupo_con_permisos(user, UserGroups.CDI_REFERENTE_CENTRO)
    AccesoCDI.objects.create(user=user, centro=centro_propio)
    client.force_login(user)

    _assert_read_scope_por_centro(client, centro_propio, centro_ajeno)


@pytest.mark.django_db
def test_trabajador_respeta_scope_en_vistas_de_lectura(client):
    centro_propio = CentroDeInfancia.objects.create(nombre="CDI trabajador URL propio")
    centro_ajeno = CentroDeInfancia.objects.create(nombre="CDI trabajador URL ajeno")
    user = _crear_usuario("trabajador-url")
    _asignar_grupo_con_permisos(user, UserGroups.CDI_TRABAJADOR)
    Trabajador.objects.create(
        centro=centro_propio,
        usuario=user,
        nombre="Usuario",
        apellido="Trabajador",
    )
    client.force_login(user)

    _assert_read_scope_por_centro(client, centro_propio, centro_ajeno)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "group_name",
    [UserGroups.SIMEPI_ADMINISTRADOR, UserGroups.SIMEPI_ANALISTA_DATOS],
)
def test_admin_y_analista_ven_centros_fuera_de_scope_por_url(client, group_name):
    provincia_scope = Provincia.objects.create(nombre=f"URL scope {group_name}")
    provincia_ajena = Provincia.objects.create(nombre=f"URL ajena {group_name}")
    centro_ajeno = CentroDeInfancia.objects.create(
        nombre=f"CDI amplio URL {group_name}",
        provincia=provincia_ajena,
    )
    user = _crear_usuario(f"nacional-url-{group_name}", provincia=provincia_scope)
    _asignar_grupo_con_permisos(user, group_name)
    client.force_login(user)

    response = client.get(
        reverse("centrodeinfancia_detalle", kwargs={"pk": centro_ajeno.pk})
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_auditoria_no_puede_mutar_centro_por_url(client):
    user = _crear_usuario("auditoria-url")
    _asignar_grupo_con_permisos(user, UserGroups.SIMEPI_AUDITORIA)
    client.force_login(user)

    response = client.post(reverse("centrodeinfancia_crear"), {"nombre": "No crear"})

    assert response.status_code == 403
    assert not CentroDeInfancia.objects.filter(nombre="No crear").exists()


@pytest.mark.django_db
def test_egp_solo_edita_centros_de_su_provincia_por_url(client):
    provincia_propia = Provincia.objects.create(nombre="EGP edición propia")
    provincia_ajena = Provincia.objects.create(nombre="EGP edición ajena")
    centro_propio = CentroDeInfancia.objects.create(
        nombre="CDI EGP edición propio",
        provincia=provincia_propia,
    )
    centro_ajeno = CentroDeInfancia.objects.create(
        nombre="CDI EGP edición ajeno",
        provincia=provincia_ajena,
    )
    user = _crear_usuario("egp-edicion-url", provincia=provincia_propia)
    _asignar_grupo_con_permisos(user, UserGroups.SIMEPI_EGP)
    client.force_login(user)

    own_response = client.get(
        reverse("centrodeinfancia_editar", kwargs={"pk": centro_propio.pk})
    )
    foreign_response = client.get(
        reverse("centrodeinfancia_editar", kwargs={"pk": centro_ajeno.pk})
    )

    assert own_response.status_code == 200
    assert foreign_response.status_code == 404


@pytest.mark.django_db
def test_referente_solo_edita_trabajadores_de_su_centro_por_url(client):
    centro_propio = CentroDeInfancia.objects.create(
        nombre="CDI referente edición propio"
    )
    centro_ajeno = CentroDeInfancia.objects.create(nombre="CDI referente edición ajeno")
    trabajador_propio = Trabajador.objects.create(
        centro=centro_propio,
        nombre="Trabajador",
        apellido="Propio",
    )
    trabajador_ajeno = Trabajador.objects.create(
        centro=centro_ajeno,
        nombre="Trabajador",
        apellido="Ajeno",
    )
    user = _crear_usuario("referente-edicion-url")
    _asignar_grupo_con_permisos(user, UserGroups.CDI_REFERENTE_CENTRO)
    AccesoCDI.objects.create(user=user, centro=centro_propio)
    client.force_login(user)

    own_response = client.get(
        reverse(
            "centrodeinfancia_trabajador_editar",
            kwargs={"pk": centro_propio.pk, "trabajador_id": trabajador_propio.pk},
        )
    )
    foreign_response = client.get(
        reverse(
            "centrodeinfancia_trabajador_editar",
            kwargs={"pk": centro_ajeno.pk, "trabajador_id": trabajador_ajeno.pk},
        )
    )

    assert own_response.status_code == 200
    assert foreign_response.status_code == 404


@pytest.mark.django_db
def test_trabajador_no_puede_editar_trabajadores_por_url(client):
    centro = CentroDeInfancia.objects.create(nombre="CDI trabajador solo lectura")
    user = _crear_usuario("trabajador-solo-lectura-url")
    _asignar_grupo_con_permisos(user, UserGroups.CDI_TRABAJADOR)
    trabajador = Trabajador.objects.create(
        centro=centro,
        usuario=user,
        nombre="Usuario",
        apellido="Trabajador",
    )
    client.force_login(user)

    response = client.get(
        reverse(
            "centrodeinfancia_trabajador_editar",
            kwargs={"pk": centro.pk, "trabajador_id": trabajador.pk},
        )
    )

    assert response.status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize(
    "group_name",
    [UserGroups.SIMEPI_ADMINISTRADOR, UserGroups.SIMEPI_ANALISTA_DATOS],
)
def test_admin_y_analista_editan_fuera_de_scope_por_url(client, group_name):
    provincia_scope = Provincia.objects.create(nombre=f"Edición scope {group_name}")
    provincia_ajena = Provincia.objects.create(nombre=f"Edición ajena {group_name}")
    centro_ajeno = CentroDeInfancia.objects.create(
        nombre=f"CDI edición amplia {group_name}",
        provincia=provincia_ajena,
    )
    user = _crear_usuario(f"nacional-edita-{group_name}", provincia=provincia_scope)
    _asignar_grupo_con_permisos(user, group_name)
    client.force_login(user)

    response = client.get(
        reverse("centrodeinfancia_editar", kwargs={"pk": centro_ajeno.pk})
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_egp_no_puede_crear_cdi_fuera_de_su_scope(client):
    provincia_propia = Provincia.objects.create(nombre="EGP alta propia")
    provincia_ajena = Provincia.objects.create(nombre="EGP alta ajena")
    user = _crear_usuario("egp-alta-scope")
    user.profile.es_usuario_provincial = True
    user.profile.save(update_fields=["es_usuario_provincial"])
    ProfileTerritorialScope.objects.create(
        profile=user.profile,
        provincia=provincia_propia,
    )
    _asignar_grupo_con_permisos(user, UserGroups.SIMEPI_EGP)
    client.force_login(user)

    response = client.post(
        reverse("centrodeinfancia_crear"),
        _payload_cdi_scope(
            provincia_propia,
            nombre="CDI EGP alta acotada",
            provincia=provincia_ajena.pk,
        ),
    )

    assert response.status_code == 302
    centro = CentroDeInfancia.objects.get(nombre="CDI EGP alta acotada")
    assert centro.provincia_id == provincia_propia.pk


@pytest.mark.django_db
def test_egp_prioriza_scope_explicito_sobre_provincia_legacy(client):
    provincia_legacy = Provincia.objects.create(nombre="EGP scope legacy")
    provincia_scope = Provincia.objects.create(nombre="EGP scope explícito")
    user = _crear_usuario("egp-scope-explicito", provincia=provincia_legacy)
    user.profile.es_usuario_provincial = True
    user.profile.save(update_fields=["es_usuario_provincial"])
    user.profile.territorial_scopes.all().delete()
    ProfileTerritorialScope.objects.create(
        profile=user.profile,
        provincia=provincia_scope,
    )
    _asignar_grupo_con_permisos(user, UserGroups.SIMEPI_EGP)
    client.force_login(user)

    response = client.post(
        reverse("centrodeinfancia_crear"),
        _payload_cdi_scope(
            provincia_scope,
            nombre="CDI EGP scope explícito",
            provincia=provincia_legacy.pk,
        ),
    )

    assert response.status_code == 302
    centro = CentroDeInfancia.objects.get(nombre="CDI EGP scope explícito")
    assert centro.provincia_id == provincia_scope.pk


@pytest.mark.django_db
def test_egp_sin_scope_no_puede_crear_cdi(client):
    provincia = Provincia.objects.create(nombre="EGP sin scope")
    user = _crear_usuario("egp-sin-scope")
    user.profile.es_usuario_provincial = True
    user.profile.save(update_fields=["es_usuario_provincial"])
    _asignar_grupo_con_permisos(user, UserGroups.SIMEPI_EGP)
    client.force_login(user)

    response = client.post(
        reverse("centrodeinfancia_crear"),
        _payload_cdi_scope(provincia, nombre="CDI EGP sin scope"),
    )

    assert response.status_code == 200
    assert not CentroDeInfancia.objects.filter(nombre="CDI EGP sin scope").exists()


@pytest.mark.django_db
def test_egp_no_puede_mover_cdi_fuera_de_su_scope(client):
    provincia_propia = Provincia.objects.create(nombre="EGP mover propia")
    provincia_ajena = Provincia.objects.create(nombre="EGP mover ajena")
    centro = CentroDeInfancia.objects.create(
        nombre="CDI EGP no mover",
        provincia=provincia_propia,
        telefono="1122334455",
        telefono_referente="1199887766",
    )
    user = _crear_usuario("egp-mover-scope")
    user.profile.es_usuario_provincial = True
    user.profile.save(update_fields=["es_usuario_provincial"])
    ProfileTerritorialScope.objects.create(
        profile=user.profile,
        provincia=provincia_propia,
    )
    _asignar_grupo_con_permisos(user, UserGroups.SIMEPI_EGP)
    client.force_login(user)

    response = client.post(
        reverse("centrodeinfancia_editar", kwargs={"pk": centro.pk}),
        _payload_cdi_scope(
            provincia_propia,
            nombre=centro.nombre,
            provincia=provincia_ajena.pk,
        ),
    )

    assert response.status_code == 302
    centro.refresh_from_db()
    assert centro.provincia_id == provincia_propia.pk


@pytest.mark.django_db
@pytest.mark.parametrize(
    "group_name",
    [UserGroups.SIMEPI_ADMINISTRADOR, UserGroups.SIMEPI_ANALISTA_DATOS],
)
def test_admin_y_analista_crean_cdi_fuera_de_scope_legacy(client, group_name):
    provincia_scope = Provincia.objects.create(nombre=f"Alta scope {group_name}")
    provincia_ajena = Provincia.objects.create(nombre=f"Alta ajena {group_name}")
    user = _crear_usuario(f"nacional-alta-{group_name}", provincia=provincia_scope)
    _asignar_grupo_con_permisos(user, group_name)
    client.force_login(user)

    response = client.post(
        reverse("centrodeinfancia_crear"),
        _payload_cdi_scope(
            provincia_ajena,
            nombre="CDI alta amplia nacional",
            provincia=provincia_ajena.pk,
        ),
    )

    assert response.status_code == 302
    centro = CentroDeInfancia.objects.get(nombre="CDI alta amplia nacional")
    assert centro.provincia_id == provincia_ajena.pk
