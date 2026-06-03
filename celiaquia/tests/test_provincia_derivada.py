"""Tests del fix #1793: la provincia del expediente y los cupos se derivan del
territorio de los ciudadanos (no del perfil del usuario, que puede tener varias
provincias o un municipio especifico y dejar el campo legacy vacio)."""

from datetime import date

import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from ciudadanos.models import Ciudadano
from core.models import Provincia
from users.models import Profile
from celiaquia.models import (
    EstadoCupo,
    EstadoExpediente,
    EstadoLegajo,
    Expediente,
    ExpedienteCiudadano,
    ProvinciaCupo,
    ResultadoSintys,
    RevisionTecnico,
)
from celiaquia.services.cupo_service import CupoService


def _ciudadano(documento, provincia=None):
    return Ciudadano.objects.create(
        apellido="Perez",
        nombre=f"Ciudadano {documento}",
        fecha_nacimiento=date(2000, 1, 1),
        documento=documento,
        tipo_documento=Ciudadano.DOCUMENTO_DNI,
        provincia=provincia,
    )


def _legajo(expediente, ciudadano, estado_legajo, **kwargs):
    return ExpedienteCiudadano.objects.create(
        expediente=expediente,
        ciudadano=ciudadano,
        estado=estado_legajo,
        **kwargs,
    )


def _perfil_provincial(creador, provincia):
    profile, _ = Profile.objects.get_or_create(user=creador)
    profile.es_usuario_provincial = True
    profile.provincia = provincia
    profile.save()
    return profile


@pytest.mark.django_db
def test_provincia_property_deriva_del_ciudadano():
    """Sin provincia en el perfil (usuario multi-provincia), la provincia se toma
    del ciudadano cargado."""
    provincia = Provincia.objects.create(nombre="Cordoba")
    creador = User.objects.create_user(username="prov_multi", password="pass")
    _perfil_provincial(creador, None)  # legacy vacio: maneja varias provincias

    estado = EstadoExpediente.objects.create(nombre="EN_ESPERA")
    estado_legajo, _ = EstadoLegajo.objects.get_or_create(nombre="VALIDO")
    expediente = Expediente.objects.create(usuario_provincia=creador, estado=estado)
    _legajo(expediente, _ciudadano(1001, provincia), estado_legajo)

    expediente = Expediente.objects.get(pk=expediente.pk)
    assert expediente.provincia == provincia


@pytest.mark.django_db
def test_provincia_property_fallback_legacy_sin_ciudadanos():
    """Un expediente sin legajos importados cae al valor legacy del perfil."""
    provincia = Provincia.objects.create(nombre="Salta")
    creador = User.objects.create_user(username="prov_legacy", password="pass")
    _perfil_provincial(creador, provincia)

    estado = EstadoExpediente.objects.create(nombre="CREADO")
    expediente = Expediente.objects.create(usuario_provincia=creador, estado=estado)

    expediente = Expediente.objects.get(pk=expediente.pk)
    assert expediente.provincia == provincia


@pytest.mark.django_db
def test_provincia_property_none_sin_datos():
    """Sin ciudadanos ni provincia legacy, la provincia es None (sin estallar)."""
    creador = User.objects.create_user(username="prov_sin_datos", password="pass")
    _perfil_provincial(creador, None)

    estado = EstadoExpediente.objects.create(nombre="CREADO")
    expediente = Expediente.objects.create(usuario_provincia=creador, estado=estado)

    expediente = Expediente.objects.get(pk=expediente.pk)
    assert expediente.provincia is None


@pytest.mark.django_db
def test_grilla_muestra_provincia_derivada_para_usuario_multi_provincia(client):
    """La grilla muestra la provincia del ciudadano aunque el perfil no la tenga."""
    provincia = Provincia.objects.create(nombre="Mendoza")
    creador = User.objects.create_user(username="prov_grilla", password="pass")
    _perfil_provincial(creador, None)

    estado = EstadoExpediente.objects.create(nombre="EN_ESPERA")
    estado_legajo, _ = EstadoLegajo.objects.get_or_create(nombre="VALIDO")
    expediente = Expediente.objects.create(usuario_provincia=creador, estado=estado)
    _legajo(expediente, _ciudadano(1100, provincia), estado_legajo)

    admin = User.objects.create_superuser(username="admin_grilla", password="pass")
    client.force_login(admin)
    response = client.get(reverse("expediente_list"))

    assert response.status_code == 200
    content = response.content.decode()
    assert str(expediente.pk) in content
    assert provincia.nombre in content


@pytest.mark.django_db
def test_cupo_lista_ocupados_por_provincia_del_ciudadano():
    """Los titulares que ocupan cupo se cuentan por la provincia del ciudadano,
    no por la del perfil del usuario creador."""
    provincia = Provincia.objects.create(nombre="Jujuy")
    ProvinciaCupo.objects.create(provincia=provincia, total_asignado=10)

    creador = User.objects.create_user(username="prov_cupo", password="pass")
    _perfil_provincial(creador, None)  # sin provincia legacy

    estado = EstadoExpediente.objects.create(nombre="CRUCE_FINALIZADO")
    estado_legajo, _ = EstadoLegajo.objects.get_or_create(nombre="VALIDO")
    expediente = Expediente.objects.create(usuario_provincia=creador, estado=estado)
    legajo = _legajo(
        expediente,
        _ciudadano(1200, provincia),
        estado_legajo,
        revision_tecnico=RevisionTecnico.APROBADO,
        resultado_sintys=ResultadoSintys.MATCH,
        estado_cupo=EstadoCupo.DENTRO,
        es_titular_activo=True,
        rol=ExpedienteCiudadano.ROLE_BENEFICIARIO,
    )

    ocupados = list(CupoService.lista_ocupados_por_provincia(provincia))
    assert legajo in ocupados


@pytest.mark.django_db
def test_cupo_metrics_cuenta_fuera_por_provincia_del_ciudadano():
    """La lista de espera (fuera de cupo) se cuenta por provincia del ciudadano."""
    provincia = Provincia.objects.create(nombre="La Rioja")
    ProvinciaCupo.objects.create(provincia=provincia, total_asignado=0)

    creador = User.objects.create_user(username="prov_fuera", password="pass")
    _perfil_provincial(creador, None)

    estado = EstadoExpediente.objects.create(nombre="CRUCE_FINALIZADO")
    estado_legajo, _ = EstadoLegajo.objects.get_or_create(nombre="VALIDO")
    expediente = Expediente.objects.create(usuario_provincia=creador, estado=estado)
    _legajo(
        expediente,
        _ciudadano(1300, provincia),
        estado_legajo,
        revision_tecnico=RevisionTecnico.APROBADO,
        resultado_sintys=ResultadoSintys.MATCH,
        estado_cupo=EstadoCupo.FUERA,
        es_titular_activo=False,
        rol=ExpedienteCiudadano.ROLE_BENEFICIARIO,
    )

    metrics = CupoService.metrics_por_provincia(provincia)
    assert metrics["fuera"] == 1


@pytest.mark.django_db
def test_cruce_sin_provincia_derivable_da_error_claro():
    """Si no se puede determinar la provincia (sin ciudadanos con territorio), el
    cruce SINTYS falla con un mensaje claro, no con 'no hay cupo'."""
    from celiaquia.services.cruce_service import CruceService

    creador = User.objects.create_user(username="prov_cruce", password="pass")
    _perfil_provincial(creador, None)

    estado = EstadoExpediente.objects.create(nombre="ASIGNADO")
    expediente = Expediente.objects.create(usuario_provincia=creador, estado=estado)

    archivo = SimpleUploadedFile("cruce.csv", b"cuit\n20123456789")
    with pytest.raises(ValidationError) as exc:
        CruceService.procesar_cruce_por_cuit(expediente, archivo, creador)

    assert "no se pudo determinar la provincia" in str(exc.value).lower()
