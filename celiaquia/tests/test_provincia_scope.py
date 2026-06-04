"""Tests del seguimiento del issue #1793: aislamiento territorial de expedientes.

Tras derivar la provincia del ciudadano (PR #1814) quedaron expuestos dos huecos
que este cambio cierra:

1. **Listado**: un usuario provincial veia expedientes que el mismo habia cargado
   aunque sus ciudadanos fueran de otra provincia (por ``include_own=True``).
2. **Carga**: un usuario multi-provincia (o sin alcance resoluble a una unica
   provincia) podia importar ciudadanos de cualquier provincia, porque el filtro
   por provincia unica quedaba en ``None``.
"""

from datetime import date

import pytest
from django.contrib.auth.models import Permission, User
from django.core.exceptions import ValidationError
from django.urls import reverse

from ciudadanos.models import Ciudadano
from core.models import Localidad, Municipio, Provincia
from users.models import Profile, ProfileTerritorialScope
from celiaquia.models import (
    Expediente,
    ExpedienteCiudadano,
    EstadoExpediente,
    EstadoLegajo,
)
from celiaquia.services.importacion_service import (
    _obtener_provincias_permitidas_ids,
    _validar_provincia_permitida_importacion,
)


def _grant_view_expediente(user):
    user.user_permissions.add(
        Permission.objects.get(
            content_type__app_label="celiaquia",
            codename="view_expediente",
        )
    )


def _provincial_user(username, *provincias):
    user = User.objects.create_user(username=username, password="pass")
    _grant_view_expediente(user)
    profile, _ = Profile.objects.get_or_create(user=user)
    profile.es_usuario_provincial = True
    profile.save()
    for provincia in provincias:
        ProfileTerritorialScope.objects.create(profile=profile, provincia=provincia)
    return user


def _territorio(nombre):
    provincia = Provincia.objects.create(nombre=f"{nombre} Prov")
    municipio = Municipio.objects.create(nombre=f"{nombre} Mun", provincia=provincia)
    localidad = Localidad.objects.create(nombre=f"{nombre} Loc", municipio=municipio)
    return provincia, municipio, localidad


def _expediente_con_ciudadano(
    owner, estado, documento, provincia, municipio, localidad
):
    expediente = Expediente.objects.create(usuario_provincia=owner, estado=estado)
    ciudadano = Ciudadano.objects.create(
        apellido="Perez",
        nombre=f"Ciudadano {documento}",
        fecha_nacimiento=date(2010, 1, 1),
        documento=documento,
        provincia=provincia,
        municipio=municipio,
        localidad=localidad,
    )
    estado_legajo, _ = EstadoLegajo.objects.get_or_create(nombre="DOCUMENTO_PENDIENTE")
    ExpedienteCiudadano.objects.create(
        expediente=expediente, ciudadano=ciudadano, estado=estado_legajo
    )
    return expediente


# --------------------------------------------------------------------------- #
# Listado (ExpedienteListView -> _apply_provincial_expediente_scope)
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_listado_oculta_expediente_propio_de_otra_provincia(client):
    """El usuario NO ve un expediente que el mismo cargo si sus ciudadanos son de
    una provincia fuera de su alcance (caso del Exped. #367 de Misiones)."""
    prov_propia, mun_propio, loc_propia = _territorio("Buenos Aires")
    prov_ajena, mun_ajeno, loc_ajena = _territorio("Misiones")
    user = _provincial_user("prov-bsas", prov_propia)
    estado = EstadoExpediente.objects.create(nombre="EN_ESPERA")

    propio_en_alcance = _expediente_con_ciudadano(
        user, estado, 501, prov_propia, mun_propio, loc_propia
    )
    propio_fuera_de_alcance = _expediente_con_ciudadano(
        user, estado, 502, prov_ajena, mun_ajeno, loc_ajena
    )
    propio_sin_legajos = Expediente.objects.create(
        usuario_provincia=user, estado=estado
    )

    client.force_login(user)
    response = client.get(reverse("expediente_list"))
    expedientes = list(response.context["expedientes"])

    assert response.status_code == 200
    assert propio_en_alcance in expedientes
    assert propio_sin_legajos in expedientes  # recien creado, todavia sin provincia
    assert propio_fuera_de_alcance not in expedientes


@pytest.mark.django_db
def test_detalle_de_expediente_de_otra_provincia_da_404(client):
    """El detalle de un expediente fuera de alcance no debe ser accesible aunque
    sea propio."""
    prov_ajena, mun_ajeno, loc_ajena = _territorio("Salta")
    prov_propia = Provincia.objects.create(nombre="Cordoba Scope")
    user = _provincial_user("prov-cba", prov_propia)
    estado = EstadoExpediente.objects.create(nombre="EN_ESPERA")
    ajeno = _expediente_con_ciudadano(
        user, estado, 601, prov_ajena, mun_ajeno, loc_ajena
    )

    client.force_login(user)
    response = client.get(reverse("expediente_detail", args=[ajeno.pk]))

    assert response.status_code == 404


# --------------------------------------------------------------------------- #
# Carga (_obtener_provincias_permitidas_ids / _validar_provincia_permitida_importacion)
# --------------------------------------------------------------------------- #


def test_validar_provincia_sin_restriccion_no_lanza():
    # None => admin/coordinador, sin restriccion provincial.
    _validar_provincia_permitida_importacion({"provincia": 99}, None)


def test_validar_provincia_en_alcance_no_lanza():
    _validar_provincia_permitida_importacion({"provincia": 5}, {5, 7})


def test_validar_provincia_fuera_de_alcance_lanza():
    with pytest.raises(ValidationError):
        _validar_provincia_permitida_importacion({"provincia": 9}, {5, 7})


def test_validar_provincia_no_inferida_no_lanza():
    # Sin provincia resuelta no se valida aca (la obligatoriedad de municipio ya
    # produce el error correspondiente).
    _validar_provincia_permitida_importacion({"provincia": None}, {5})
    _validar_provincia_permitida_importacion({}, {5})


@pytest.mark.django_db
def test_provincias_permitidas_superusuario_sin_restriccion():
    admin = User.objects.create_superuser(username="admin-scope", password="pass")
    assert _obtener_provincias_permitidas_ids(admin) is None


@pytest.mark.django_db
def test_provincias_permitidas_no_territorial_sin_restriccion():
    user = User.objects.create_user(username="plain-scope", password="pass")
    assert _obtener_provincias_permitidas_ids(user) is None


@pytest.mark.django_db
def test_provincias_permitidas_multiprovincia_devuelve_conjunto():
    p1 = Provincia.objects.create(nombre="P1 Scope")
    p2 = Provincia.objects.create(nombre="P2 Scope")
    user = _provincial_user("multi-scope", p1, p2)
    assert _obtener_provincias_permitidas_ids(user) == {p1.id, p2.id}
