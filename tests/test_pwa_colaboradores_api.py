import pytest
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from ciudadanos.models import Ciudadano
from comedores.models import (
    ActividadColaboradorEspacio,
    AuditColaboradorEspacio,
    ColaboradorEspacio,
    Comedor,
)
from core.models import Provincia, Sexo
from users.models import AccesoComedorPWA


@pytest.fixture
def comedor(db):
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    return Comedor.objects.create(nombre="Comedor Colaboradores", provincia=provincia)


@pytest.fixture
def sexo(db):
    return Sexo.objects.create(sexo="Femenino")


@pytest.fixture
def actividad(db):
    return ActividadColaboradorEspacio.objects.create(
        alias="COM",
        nombre="Compras",
        orden=1,
    )


def _create_representante(*, comedor, username="rep_colab", password="testpass123"):
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


def _create_ciudadano(*, sexo, documento=12345678):
    return Ciudadano.objects.create(
        tipo_documento=Ciudadano.DOCUMENTO_DNI,
        documento=documento,
        apellido="Gomez",
        nombre="Ana",
        sexo=sexo,
        fecha_nacimiento="1990-01-15",
        cuil_cuit="27123456789",
    )


@pytest.mark.django_db
def test_preview_dni_devuelve_ciudadano_existente(comedor, sexo):
    representante = _create_representante(comedor=comedor)
    client = _auth_client_for_user(representante)
    ciudadano = _create_ciudadano(sexo=sexo)

    response = client.post(
        f"/api/pwa/espacios/{comedor.id}/colaboradores/preview-dni/",
        {"dni": str(ciudadano.documento)},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["source"] == "sisoc"
    assert response.data["ciudadano_id"] == ciudadano.id
    assert response.data["apellido"] == "Gomez"
    assert response.data["nombre"] == "Ana"
    assert str(response.data["dni"]) == "12345678"


@pytest.mark.django_db
def test_create_colaborador_ok_desde_ciudadano_existente(comedor, sexo, actividad):
    representante = _create_representante(comedor=comedor)
    client = _auth_client_for_user(representante)
    ciudadano = _create_ciudadano(sexo=sexo)

    response = client.post(
        f"/api/pwa/espacios/{comedor.id}/colaboradores/",
        {
            "ciudadano_id": ciudadano.id,
            "genero": "M",
            "codigo_telefono": "11",
            "numero_telefono": "12345678",
            "fecha_alta": "2026-03-26",
            "actividad_ids": [actividad.id],
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.data["ciudadano_id"] == ciudadano.id
    assert response.data["genero"] == "M"
    assert response.data["codigo_telefono"] == "11"
    assert response.data["numero_telefono"] == "12345678"
    assert response.data["activo"] is True
    assert response.data["actividades"] == [
        {"id": actividad.id, "alias": "COM", "nombre": "Compras"}
    ]
    colaborador = ColaboradorEspacio.objects.get(pk=response.data["id"])
    assert colaborador.comedor == comedor
    assert colaborador.ciudadano == ciudadano
    assert colaborador.actividades.filter(pk=actividad.id).exists()
    assert AuditColaboradorEspacio.objects.filter(
        colaborador=colaborador,
        accion=AuditColaboradorEspacio.ACCION_CREATE,
    ).exists()


@pytest.mark.django_db
def test_create_colaborador_desde_renaper_crea_ciudadano(
    comedor, sexo, actividad, mocker
):
    representante = _create_representante(comedor=comedor)
    client = _auth_client_for_user(representante)
    ciudadano = _create_ciudadano(sexo=sexo, documento=22333444)
    mocker.patch(
        "comedores.services.comedor_service.impl.ComedorService.crear_ciudadano_desde_renaper",
        return_value={
            "success": True,
            "message": "Ciudadano obtenido desde RENAPER.",
            "ciudadano": ciudadano,
        },
    )

    response = client.post(
        f"/api/pwa/espacios/{comedor.id}/colaboradores/",
        {
            "dni": "22333444",
            "genero": "ND",
            "codigo_telefono": "221",
            "numero_telefono": "9876543",
            "fecha_alta": "2026-03-26",
            "actividad_ids": [actividad.id],
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.data["ciudadano_id"] == ciudadano.id
    assert str(response.data["dni"]) == "22333444"


@pytest.mark.django_db
def test_create_colaborador_rechaza_duplicado_activo(comedor, sexo, actividad):
    representante = _create_representante(comedor=comedor)
    client = _auth_client_for_user(representante)
    ciudadano = _create_ciudadano(sexo=sexo)
    ColaboradorEspacio.objects.create(
        comedor=comedor,
        ciudadano=ciudadano,
        genero="M",
        codigo_telefono="11",
        numero_telefono="12345678",
        fecha_alta="2026-03-20",
        creado_por=representante,
        modificado_por=representante,
    ).actividades.set([actividad])

    response = client.post(
        f"/api/pwa/espacios/{comedor.id}/colaboradores/",
        {
            "ciudadano_id": ciudadano.id,
            "genero": "M",
            "codigo_telefono": "11",
            "numero_telefono": "87654321",
            "fecha_alta": "2026-03-26",
            "actividad_ids": [actividad.id],
        },
        format="json",
    )

    assert response.status_code == 400
    assert "ya se encuentra registrada" in response.data["detail"].lower()


@pytest.mark.django_db
def test_update_colaborador_ok(comedor, sexo, actividad):
    representante = _create_representante(comedor=comedor)
    client = _auth_client_for_user(representante)
    ciudadano = _create_ciudadano(sexo=sexo)
    colaborador = ColaboradorEspacio.objects.create(
        comedor=comedor,
        ciudadano=ciudadano,
        genero="ND",
        codigo_telefono="11",
        numero_telefono="12345678",
        fecha_alta="2026-03-20",
        creado_por=representante,
        modificado_por=representante,
    )
    colaborador.actividades.set([actividad])
    otra_actividad = ActividadColaboradorEspacio.objects.create(
        alias="LIM",
        nombre="Limpieza",
        orden=2,
    )

    response = client.patch(
        f"/api/pwa/espacios/{comedor.id}/colaboradores/{colaborador.id}/",
        {
            "genero": "M",
            "numero_telefono": "99999999",
            "fecha_baja": "2026-03-28",
            "actividad_ids": [otra_actividad.id],
        },
        format="json",
    )

    assert response.status_code == 200
    colaborador.refresh_from_db()
    assert colaborador.genero == "M"
    assert colaborador.numero_telefono == "99999999"
    assert str(colaborador.fecha_baja) == "2026-03-28"
    assert list(colaborador.actividades.values_list("nombre", flat=True)) == ["Limpieza"]
    assert AuditColaboradorEspacio.objects.filter(
        colaborador=colaborador,
        accion=AuditColaboradorEspacio.ACCION_UPDATE,
    ).exists()


@pytest.mark.django_db
def test_update_colaborador_preserva_actividades_si_no_se_envia_actividad_ids(
    comedor, sexo, actividad
):
    representante = _create_representante(comedor=comedor)
    client = _auth_client_for_user(representante)
    ciudadano = _create_ciudadano(sexo=sexo)
    colaborador = ColaboradorEspacio.objects.create(
        comedor=comedor,
        ciudadano=ciudadano,
        genero="ND",
        codigo_telefono="11",
        numero_telefono="12345678",
        fecha_alta="2026-03-20",
        creado_por=representante,
        modificado_por=representante,
    )
    colaborador.actividades.set([actividad])

    response = client.patch(
        f"/api/pwa/espacios/{comedor.id}/colaboradores/{colaborador.id}/",
        {
            "numero_telefono": "55555555",
        },
        format="json",
    )

    assert response.status_code == 200
    colaborador.refresh_from_db()
    assert colaborador.numero_telefono == "55555555"
    assert list(colaborador.actividades.values_list("nombre", flat=True)) == [
        "Compras"
    ]


@pytest.mark.django_db
def test_delete_colaborador_es_baja_logica_y_permanece_en_listado(
    comedor, sexo, actividad
):
    representante = _create_representante(comedor=comedor)
    client = _auth_client_for_user(representante)
    ciudadano = _create_ciudadano(sexo=sexo)
    colaborador = ColaboradorEspacio.objects.create(
        comedor=comedor,
        ciudadano=ciudadano,
        genero="ND",
        codigo_telefono="11",
        numero_telefono="12345678",
        fecha_alta="2026-03-20",
        creado_por=representante,
        modificado_por=representante,
    )
    colaborador.actividades.set([actividad])

    response = client.delete(
        f"/api/pwa/espacios/{comedor.id}/colaboradores/{colaborador.id}/",
    )

    assert response.status_code == 204
    colaborador.refresh_from_db()
    assert colaborador.fecha_baja is not None
    list_response = client.get(f"/api/pwa/espacios/{comedor.id}/colaboradores/")
    assert list_response.status_code == 200
    assert list_response.data[0]["id"] == colaborador.id
    assert list_response.data[0]["activo"] is False
    assert list_response.data[0]["fecha_baja"] is not None
    assert AuditColaboradorEspacio.objects.filter(
        colaborador=colaborador,
        accion=AuditColaboradorEspacio.ACCION_DELETE,
    ).exists()


@pytest.mark.django_db
def test_colaboradores_requiere_representante_del_espacio(comedor):
    user_model = get_user_model()
    other_user = user_model.objects.create_user(
        username="sin_permiso_colab",
        email="sin_permiso_colab@example.com",
        password="testpass123",
    )
    client = _auth_client_for_user(other_user)

    response = client.get(f"/api/pwa/espacios/{comedor.id}/colaboradores/")

    assert response.status_code == 403
