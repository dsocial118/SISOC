"""Filtros combinables del listado de expedientes de Celiaquía (tk #2320)."""

import json
from datetime import date

import pytest
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from ciudadanos.models import Ciudadano
from core.models import Localidad, Municipio, Provincia
from celiaquia.models import (
    AsignacionTecnico,
    EstadoExpediente,
    EstadoLegajo,
    Expediente,
    ExpedienteCiudadano,
)
from celiaquia.services.expediente_filter_config import (  # pylint: disable=no-name-in-module
    FIELD_MAP,
    FIELD_TYPES,
    get_filters_ui_config,
)
from users.models import Profile


def _permiso(app_label, codename):
    """Los permisos de rol (``auth.role_*``) los crea una data migration que no
    corre en la base de tests, así que se siembran acá."""
    try:
        return Permission.objects.get(
            content_type__app_label=app_label,
            codename=codename,
        )
    except Permission.DoesNotExist:
        content_type = ContentType.objects.get(app_label="auth", model="user")
        return Permission.objects.create(
            content_type=content_type,
            codename=codename,
            name=codename,
        )


def _crear_coordinador():
    user = User.objects.create_user(username="coord", password="pass")
    user.user_permissions.add(_permiso("celiaquia", "view_expediente"))
    user.user_permissions.add(_permiso("auth", "role_coordinadorceliaquia"))
    Profile.objects.get_or_create(user=user)
    return user


def _crear_expediente(*, owner, estado, provincia, documento, numero=None):
    """Crea un expediente con un legajo, para que derive provincia."""
    expediente = Expediente.objects.create(
        usuario_provincia=owner,
        estado=estado,
        numero_expediente=numero,
    )
    municipio = Municipio.objects.create(
        nombre=f"Municipio {documento}", provincia=provincia
    )
    localidad = Localidad.objects.create(
        nombre=f"Localidad {documento}", municipio=municipio
    )
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
        expediente=expediente,
        ciudadano=ciudadano,
        estado=estado_legajo,
    )
    return expediente


def _filtros(*items, logic="AND"):
    return {"filters": json.dumps({"logic": logic, "items": list(items)})}


def _ids_listados(response):
    return {exp.pk for exp in response.context["expedientes"]}


@pytest.mark.django_db
def test_filtros_combinados_aplican_en_conjunto(client):
    """Dos filtros distintos se combinan con AND, no se pisan entre sí."""
    buenos_aires = Provincia.objects.create(nombre="Buenos Aires")
    cordoba = Provincia.objects.create(nombre="Cordoba")
    creado = EstadoExpediente.objects.create(nombre="CREADO")
    en_espera = EstadoExpediente.objects.create(nombre="EN_ESPERA")
    user = _crear_coordinador()

    esperado = _crear_expediente(
        owner=user, estado=creado, provincia=buenos_aires, documento="10000001"
    )
    # Coincide con la provincia pero no con el estado.
    _crear_expediente(
        owner=user, estado=en_espera, provincia=buenos_aires, documento="10000002"
    )
    # Coincide con el estado pero no con la provincia.
    _crear_expediente(
        owner=user, estado=creado, provincia=cordoba, documento="10000003"
    )

    client.force_login(user)
    response = client.get(
        reverse("expediente_list"),
        _filtros(
            {"field": "provincia", "op": "eq", "value": "Buenos Aires"},
            {"field": "estado", "op": "eq", "value": "CREADO"},
        ),
    )

    assert response.status_code == 200
    assert _ids_listados(response) == {esperado.pk}


@pytest.mark.django_db
def test_filtro_por_numero_de_expediente(client):
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    estado = EstadoExpediente.objects.create(nombre="CREADO")
    user = _crear_coordinador()

    esperado = _crear_expediente(
        owner=user,
        estado=estado,
        provincia=provincia,
        documento="20000001",
        numero="EX-2026-777",
    )
    _crear_expediente(
        owner=user,
        estado=estado,
        provincia=provincia,
        documento="20000002",
        numero="EX-2026-888",
    )

    client.force_login(user)
    response = client.get(
        reverse("expediente_list"),
        _filtros({"field": "numero_expediente", "op": "contains", "value": "777"}),
    )

    assert _ids_listados(response) == {esperado.pk}


@pytest.mark.django_db
def test_filtro_por_tecnico_no_duplica_expedientes(client):
    """Dos filtros sobre el mismo campo se combinan con OR sobre un único join.
    Como ``asignaciones_tecnicos`` es multivalor, un expediente asignado a ambos
    técnicos se repetiría una vez por asignación si faltara el ``distinct()``."""
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    estado = EstadoExpediente.objects.create(nombre="ASIGNADO")
    user = _crear_coordinador()

    tecnico = User.objects.create_user(username="tecnico1", password="pass")
    tecnico.user_permissions.add(_permiso("auth", "role_tecnicoceliaquia"))
    otro_tecnico = User.objects.create_user(username="tecnico2", password="pass")
    otro_tecnico.user_permissions.add(_permiso("auth", "role_tecnicoceliaquia"))

    expediente = _crear_expediente(
        owner=user, estado=estado, provincia=provincia, documento="30000001"
    )
    AsignacionTecnico.objects.create(expediente=expediente, tecnico=tecnico)
    AsignacionTecnico.objects.create(expediente=expediente, tecnico=otro_tecnico)

    sin_tecnico = _crear_expediente(
        owner=user, estado=estado, provincia=provincia, documento="30000002"
    )

    client.force_login(user)
    response = client.get(
        reverse("expediente_list"),
        _filtros(
            {"field": "tecnico", "op": "eq", "value": "tecnico1"},
            {"field": "tecnico", "op": "eq", "value": "tecnico2"},
        ),
    )

    listados = list(response.context["expedientes"])
    assert [exp.pk for exp in listados] == [expediente.pk]
    assert sin_tecnico.pk not in {exp.pk for exp in listados}


@pytest.mark.django_db
def test_filtros_no_amplian_el_alcance_territorial(client):
    """Un usuario provincial no puede alcanzar expedientes de otra provincia
    filtrando por ella: los filtros se aplican sobre el queryset ya acotado."""
    propia = Provincia.objects.create(nombre="Buenos Aires")
    ajena = Provincia.objects.create(nombre="Cordoba")
    estado = EstadoExpediente.objects.create(nombre="CREADO")

    provincial = User.objects.create_user(username="prov", password="pass")
    provincial.user_permissions.add(_permiso("celiaquia", "view_expediente"))
    profile, _ = Profile.objects.get_or_create(user=provincial)
    profile.es_usuario_provincial = True
    profile.provincia = propia
    profile.save()

    otro = User.objects.create_user(username="otro", password="pass")
    Profile.objects.get_or_create(user=otro)
    ajeno = _crear_expediente(
        owner=otro, estado=estado, provincia=ajena, documento="40000001"
    )

    client.force_login(provincial)
    response = client.get(
        reverse("expediente_list"),
        _filtros({"field": "provincia", "op": "eq", "value": "Cordoba"}),
    )

    assert response.status_code == 200
    assert ajeno.pk not in _ids_listados(response)


@pytest.mark.django_db
def test_filtro_invalido_no_rompe_el_listado(client):
    """Un campo desconocido se ignora y el listado responde normalmente."""
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    estado = EstadoExpediente.objects.create(nombre="CREADO")
    user = _crear_coordinador()
    expediente = _crear_expediente(
        owner=user, estado=estado, provincia=provincia, documento="50000001"
    )

    client.force_login(user)
    response = client.get(
        reverse("expediente_list"),
        _filtros({"field": "campo_inexistente", "op": "eq", "value": "x"}),
    )

    assert response.status_code == 200
    assert expediente.pk in _ids_listados(response)


@pytest.mark.django_db
def test_config_oculta_el_campo_tecnico_para_usuarios_provinciales(client):
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    EstadoExpediente.objects.create(nombre="CREADO")

    provincial = User.objects.create_user(username="prov", password="pass")
    provincial.user_permissions.add(_permiso("celiaquia", "view_expediente"))
    profile, _ = Profile.objects.get_or_create(user=provincial)
    profile.es_usuario_provincial = True
    profile.provincia = provincia
    profile.save()

    client.force_login(provincial)
    response = client.get(reverse("expediente_list"))

    campos = {campo["name"] for campo in response.context["filters_config"]["fields"]}
    assert "tecnico" not in campos
    assert {"id", "numero_expediente", "estado", "provincia"} <= campos


@pytest.mark.django_db
def test_usuario_provincial_no_puede_filtrar_por_tecnico_mediante_la_url(client):
    """El campo oculto en la UI tampoco debe aceptarse en el backend."""
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    estado = EstadoExpediente.objects.create(nombre="CREADO")

    provincial = User.objects.create_user(username="prov", password="pass")
    provincial.user_permissions.add(_permiso("celiaquia", "view_expediente"))
    profile, _ = Profile.objects.get_or_create(user=provincial)
    profile.es_usuario_provincial = True
    profile.provincia = provincia
    profile.save()

    tecnico = User.objects.create_user(username="tecnico1", password="pass")
    tecnico.user_permissions.add(_permiso("auth", "role_tecnicoceliaquia"))
    asignado = _crear_expediente(
        owner=provincial, estado=estado, provincia=provincia, documento="51000001"
    )
    sin_asignar = _crear_expediente(
        owner=provincial, estado=estado, provincia=provincia, documento="51000002"
    )
    AsignacionTecnico.objects.create(expediente=asignado, tecnico=tecnico)

    client.force_login(provincial)
    response = client.get(
        reverse("expediente_list"),
        _filtros({"field": "tecnico", "op": "eq", "value": "tecnico1"}),
    )

    assert _ids_listados(response) == {asignado.pk, sin_asignar.pk}


@pytest.mark.django_db
def test_config_expone_el_campo_tecnico_al_coordinador(client):
    Provincia.objects.create(nombre="Buenos Aires")
    EstadoExpediente.objects.create(nombre="CREADO")
    user = _crear_coordinador()
    tecnico = User.objects.create_user(
        username="tecnico1", password="pass", first_name="Ana", last_name="Diaz"
    )
    tecnico.user_permissions.add(_permiso("auth", "role_tecnicoceliaquia"))

    client.force_login(user)
    response = client.get(reverse("expediente_list"))

    campos = {
        campo["name"]: campo for campo in response.context["filters_config"]["fields"]
    }
    assert "tecnico" in campos
    assert {"value": "tecnico1", "label": "Ana Diaz"} in campos["tecnico"]["choices"]


@pytest.mark.django_db
def test_config_usa_los_estados_reales_como_opciones():
    EstadoExpediente.objects.create(nombre="CRUCE_FINALIZADO")
    config = get_filters_ui_config()

    estado = next(c for c in config["fields"] if c["name"] == "estado")
    assert {"value": "CRUCE_FINALIZADO", "label": "Cruce finalizado"} in estado[
        "choices"
    ]


@pytest.mark.django_db
def test_listado_renderiza_la_barra_de_filtros_combinables(client):
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    EstadoExpediente.objects.create(nombre="CREADO")
    user = User.objects.create_user(username="prov", password="pass")
    user.user_permissions.add(_permiso("celiaquia", "view_expediente"))
    profile, _ = Profile.objects.get_or_create(user=user)
    profile.es_usuario_provincial = True
    profile.provincia = provincia
    profile.save()

    client.force_login(user)
    html = client.get(reverse("expediente_list")).content.decode()

    assert 'id="filters-form"' in html
    assert 'id="filters-config-json"' in html
    assert 'id="poncho-filters-rows"' in html
    assert "advanced_filters.js" in html


def test_todos_los_campos_tipados_tienen_lookup():
    """Contrato del AdvancedFilterEngine: field_types no puede tener claves que
    falten en field_map."""
    assert set(FIELD_TYPES) <= set(FIELD_MAP)
