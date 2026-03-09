import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from ciudadanos.models import Ciudadano
from comedores.models import Comedor, Nomina
from core.models import Dia, Provincia, Sexo
from pwa.models import (
    ActividadEspacioPWA,
    AuditoriaOperacionPWA,
    CatalogoActividadPWA,
    InscriptoActividadEspacioPWA,
)
from users.models import AccesoComedorPWA


@pytest.fixture
def comedor(db):
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    return Comedor.objects.create(nombre="Comedor Actividades API", provincia=provincia)


@pytest.fixture
def dia():
    return Dia.objects.create(nombre="Lunes")


def _create_representante(*, comedor, username="rep_act", password="testpass123"):
    user_model = get_user_model()
    user = user_model.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password=password,
    )
    AccesoComedorPWA.objects.create(
        user=user,
        comedor=comedor,
        rol=AccesoComedorPWA.ROL_REPRESENTANTE,
        activo=True,
    )
    return user


def _auth_client_for_user(user):
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


@pytest.mark.django_db
def test_catalogo_actividades_list_ok(comedor):
    representante = _create_representante(comedor=comedor)
    client = _auth_client_for_user(representante)

    response = client.get(f"/api/pwa/espacios/{comedor.id}/actividades/catalogo/")

    assert response.status_code == 200
    assert isinstance(response.data, list)
    assert len(response.data) > 0
    assert {"id", "categoria", "actividad"}.issubset(set(response.data[0].keys()))


@pytest.mark.django_db
def test_create_update_delete_actividad_ok(comedor, dia):
    representante = _create_representante(comedor=comedor)
    client = _auth_client_for_user(representante)
    catalogo = CatalogoActividadPWA.objects.filter(activo=True).first()
    assert catalogo is not None

    create_response = client.post(
        f"/api/pwa/espacios/{comedor.id}/actividades/",
        {
            "catalogo_actividad": catalogo.id,
            "dia_actividad": dia.id,
            "horario_actividad": "18:00 a 19:00",
        },
        format="json",
    )

    assert create_response.status_code == 201
    actividad_id = create_response.data["id"]

    patch_response = client.patch(
        f"/api/pwa/espacios/{comedor.id}/actividades/{actividad_id}/",
        {
            "horario_actividad": "19:00 a 20:00",
        },
        format="json",
    )

    assert patch_response.status_code == 200
    assert patch_response.data["horario_actividad"] == "19:00 a 20:00"

    delete_response = client.delete(
        f"/api/pwa/espacios/{comedor.id}/actividades/{actividad_id}/"
    )
    assert delete_response.status_code == 204
    actividad = ActividadEspacioPWA.objects.get(pk=actividad_id)
    assert actividad.activo is False
    assert actividad.fecha_baja is not None
    eventos = list(
        AuditoriaOperacionPWA.objects.filter(
            entidad="actividad",
            entidad_id=actividad_id,
        )
        .order_by("id")
        .values_list("accion", flat=True)
    )
    assert eventos == ["create", "update", "delete"]


@pytest.mark.django_db
def test_delete_actividad_impacta_inscriptos(comedor, dia):
    representante = _create_representante(comedor=comedor, username="rep_act_2")
    client = _auth_client_for_user(representante)
    catalogo = CatalogoActividadPWA.objects.filter(activo=True).first()
    actividad = ActividadEspacioPWA.objects.create(
        comedor=comedor,
        catalogo_actividad=catalogo,
        dia_actividad=dia,
        horario_actividad="16:00 a 17:00",
        creado_por=representante,
        actualizado_por=representante,
    )

    sexo = Sexo.objects.create(sexo="Femenino")
    ciudadano = Ciudadano.objects.create(
        nombre="Ana",
        apellido="Perez",
        fecha_nacimiento=timezone.datetime(2010, 1, 1).date(),
        documento=12345678,
        sexo=sexo,
    )
    nomina = Nomina.objects.create(
        comedor=comedor,
        ciudadano=ciudadano,
        estado=Nomina.ESTADO_ACTIVO,
    )
    inscripto = InscriptoActividadEspacioPWA.objects.create(
        actividad_espacio=actividad,
        nomina=nomina,
        activo=True,
        creado_por=representante,
        actualizado_por=representante,
    )

    response = client.delete(
        f"/api/pwa/espacios/{comedor.id}/actividades/{actividad.id}/"
    )

    assert response.status_code == 204
    inscripto.refresh_from_db()
    assert inscripto.activo is False
    assert inscripto.fecha_baja is not None
    assert AuditoriaOperacionPWA.objects.filter(
        entidad="inscripcion_actividad",
        entidad_id=inscripto.id,
        accion="deactivate",
    ).exists()


@pytest.mark.django_db
def test_list_actividades_e_inscriptos_ok(comedor, dia):
    representante = _create_representante(comedor=comedor, username="rep_act_3")
    client = _auth_client_for_user(representante)
    catalogo = CatalogoActividadPWA.objects.filter(activo=True).first()
    actividad = ActividadEspacioPWA.objects.create(
        comedor=comedor,
        catalogo_actividad=catalogo,
        dia_actividad=dia,
        horario_actividad="10:00 a 11:00",
        creado_por=representante,
        actualizado_por=representante,
    )
    sexo = Sexo.objects.create(sexo="Masculino")
    ciudadano = Ciudadano.objects.create(
        nombre="Juan",
        apellido="Lopez",
        fecha_nacimiento=timezone.datetime(2011, 2, 2).date(),
        documento=33444555,
        sexo=sexo,
    )
    nomina = Nomina.objects.create(
        comedor=comedor,
        ciudadano=ciudadano,
        estado=Nomina.ESTADO_ACTIVO,
    )
    InscriptoActividadEspacioPWA.objects.create(
        actividad_espacio=actividad,
        nomina=nomina,
        activo=True,
        creado_por=representante,
        actualizado_por=representante,
    )

    list_response = client.get(f"/api/pwa/espacios/{comedor.id}/actividades/")
    assert list_response.status_code == 200
    assert list_response.data[0]["cantidad_inscriptos"] == 1

    inscriptos_response = client.get(
        f"/api/pwa/espacios/{comedor.id}/actividades/{actividad.id}/inscriptos/"
    )
    assert inscriptos_response.status_code == 200
    assert len(inscriptos_response.data) == 1
    assert inscriptos_response.data[0]["nombre"] == "Juan"
    assert inscriptos_response.data[0]["apellido"] == "Lopez"
    assert inscriptos_response.data[0]["dni"] == "33444555"
    assert inscriptos_response.data[0]["genero"] == "Masculino"


@pytest.mark.django_db
def test_actividades_requiere_representante_del_espacio(comedor):
    user_model = get_user_model()
    other_user = user_model.objects.create_user(
        username="sin_permiso_act",
        email="sin_permiso_act@example.com",
        password="testpass123",
    )
    client = _auth_client_for_user(other_user)

    response = client.get(f"/api/pwa/espacios/{comedor.id}/actividades/")

    assert response.status_code == 403
