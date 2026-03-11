import pytest
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from admisiones.models.admisiones import Admision
from ciudadanos.models import Ciudadano
from comedores.models import Comedor, Nomina
from core.models import Dia, Provincia, Sexo
from pwa.models import (
    ActividadEspacioPWA,
    AuditoriaOperacionPWA,
    CatalogoActividadPWA,
    InscriptoActividadEspacioPWA,
    NominaEspacioPWA,
)
from users.models import AccesoComedorPWA


@pytest.fixture
def comedor(db):
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    return Comedor.objects.create(nombre="Comedor Nómina API", provincia=provincia)


@pytest.fixture
def admision(comedor):
    return Admision.objects.create(comedor=comedor, activa=True)


@pytest.fixture
def sexo_f(db):
    return Sexo.objects.create(sexo="Femenino")


@pytest.fixture
def sexo_m(db):
    return Sexo.objects.create(sexo="Masculino")


@pytest.fixture
def dia(db):
    return Dia.objects.create(nombre="Lunes")


def _create_representante(*, comedor, username="rep_nomina", password="testpass123"):
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
def test_nomina_list_stats_and_tabs(comedor, admision, sexo_f, sexo_m, dia):
    representante = _create_representante(comedor=comedor, username="rep_nomina_tabs")
    client = _auth_client_for_user(representante)

    ciudadano_1 = Ciudadano.objects.create(
        nombre="Ana",
        apellido="Perez",
        documento=12345678,
        fecha_nacimiento="2014-01-10",
        sexo=sexo_f,
    )
    ciudadano_2 = Ciudadano.objects.create(
        nombre="Juan",
        apellido="Lopez",
        documento=33444555,
        fecha_nacimiento="1990-02-15",
        sexo=sexo_m,
    )
    nomina_1 = Nomina.objects.create(
        admision=admision,
        ciudadano=ciudadano_1,
        estado=Nomina.ESTADO_ACTIVO,
    )
    nomina_2 = Nomina.objects.create(
        admision=admision,
        ciudadano=ciudadano_2,
        estado=Nomina.ESTADO_ACTIVO,
    )
    NominaEspacioPWA.objects.create(
        nomina=nomina_1,
        asistencia_alimentaria=True,
        asistencia_actividades=False,
        activo=True,
    )
    NominaEspacioPWA.objects.create(
        nomina=nomina_2,
        asistencia_alimentaria=False,
        asistencia_actividades=True,
        activo=True,
    )
    catalogo = CatalogoActividadPWA.objects.filter(activo=True).first()
    actividad = ActividadEspacioPWA.objects.create(
        comedor=comedor,
        catalogo_actividad=catalogo,
        dia_actividad=dia,
        horario_actividad="10:00",
        activo=True,
    )
    InscriptoActividadEspacioPWA.objects.create(
        actividad_espacio=actividad,
        nomina=nomina_2,
        activo=True,
    )

    response = client.get(f"/api/pwa/espacios/{comedor.id}/nomina/")
    assert response.status_code == 200
    assert response.data["stats"]["total_nomina"] == 2
    assert response.data["stats"]["genero"]["F"] == 1
    assert response.data["stats"]["genero"]["M"] == 1
    assert response.data["stats"]["menores_edad"] == 1
    assert response.data["stats"]["mayores_edad"] == 1
    assert len(response.data["results"]) == 2

    response_alim = client.get(
        f"/api/pwa/espacios/{comedor.id}/nomina/?tab=alimentaria"
    )
    assert response_alim.status_code == 200
    assert len(response_alim.data["results"]) == 1
    assert response_alim.data["results"][0]["apellido"] == "Perez"

    response_formacion = client.get(
        f"/api/pwa/espacios/{comedor.id}/nomina/?tab=formacion"
    )
    assert response_formacion.status_code == 200
    assert len(response_formacion.data["results"]) == 1
    assert response_formacion.data["results"][0]["apellido"] == "Lopez"


@pytest.mark.django_db
def test_nomina_create_indocumentado_ok(comedor, sexo_f):
    representante = _create_representante(comedor=comedor, username="rep_nomina_indoc")
    client = _auth_client_for_user(representante)

    response = client.post(
        f"/api/pwa/espacios/{comedor.id}/nomina/",
        {
            "nombre": "Nora",
            "apellido": "SinDoc",
            "fecha_nacimiento": "2011-05-10",
            "sexo_id": sexo_f.id,
            "es_indocumentado": True,
            "identificador_interno": "IND-001",
            "asistencia_alimentaria": True,
            "asistencia_actividades": False,
            "actividad_ids": [],
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.data["es_indocumentado"] is True
    assert response.data["identificador_interno"] == "IND-001"
    assert response.data["dni"] == ""


@pytest.mark.django_db
def test_nomina_create_rejects_duplicate_dni_in_same_space(
    comedor, admision, sexo_f, mocker
):
    representante = _create_representante(comedor=comedor, username="rep_nomina_dup")
    client = _auth_client_for_user(representante)

    ciudadano = Ciudadano.objects.create(
        nombre="Laura",
        apellido="Diaz",
        documento=22333444,
        fecha_nacimiento="2005-01-01",
        sexo=sexo_f,
    )
    Nomina.objects.create(
        admision=admision,
        ciudadano=ciudadano,
        estado=Nomina.ESTADO_ACTIVO,
    )
    mocker.patch(
        "pwa.services.nomina_service.ComedorService.crear_ciudadano_desde_renaper",
        return_value={"success": True, "data": {"id": ciudadano.id}},
    )

    response = client.post(
        f"/api/pwa/espacios/{comedor.id}/nomina/",
        {
            "dni": "22333444",
            "asistencia_alimentaria": True,
            "asistencia_actividades": False,
            "actividad_ids": [],
        },
        format="json",
    )

    assert response.status_code == 400
    assert "dni" in response.data["detail"]


@pytest.mark.django_db
def test_nomina_delete_is_logical(comedor, admision, sexo_m, dia):
    representante = _create_representante(comedor=comedor, username="rep_nomina_delete")
    client = _auth_client_for_user(representante)

    ciudadano = Ciudadano.objects.create(
        nombre="Carlos",
        apellido="Soto",
        documento=40999888,
        fecha_nacimiento="1994-09-01",
        sexo=sexo_m,
    )
    nomina = Nomina.objects.create(
        admision=admision,
        ciudadano=ciudadano,
        estado=Nomina.ESTADO_ACTIVO,
    )
    NominaEspacioPWA.objects.create(
        nomina=nomina,
        asistencia_alimentaria=True,
        asistencia_actividades=True,
        activo=True,
    )
    catalogo = CatalogoActividadPWA.objects.filter(activo=True).first()
    actividad = ActividadEspacioPWA.objects.create(
        comedor=comedor,
        catalogo_actividad=catalogo,
        dia_actividad=dia,
        horario_actividad="18:00",
        activo=True,
    )
    inscripto = InscriptoActividadEspacioPWA.objects.create(
        actividad_espacio=actividad,
        nomina=nomina,
        activo=True,
    )

    response = client.delete(f"/api/pwa/espacios/{comedor.id}/nomina/{nomina.id}/")
    assert response.status_code == 204

    nomina.refresh_from_db()
    inscripto.refresh_from_db()
    assert nomina.estado == Nomina.ESTADO_BAJA
    assert inscripto.activo is False
    assert AuditoriaOperacionPWA.objects.filter(
        entidad="nomina",
        entidad_id=nomina.id,
        accion="delete",
    ).exists()
    assert AuditoriaOperacionPWA.objects.filter(
        entidad="inscripcion_actividad",
        entidad_id=inscripto.id,
        accion="deactivate",
    ).exists()
