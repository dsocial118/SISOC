from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
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
    RegistroAsistenciaNominaPWA,
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
        hora_inicio="10:00",
        hora_fin="11:00",
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
    row_lopez = next(
        row for row in response.data["results"] if row["apellido"] == "Lopez"
    )
    assert row_lopez["cantidad_actividades"] == 1
    assert row_lopez["actividades"] == []

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
        hora_inicio="18:00",
        hora_fin="19:00",
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


@pytest.mark.django_db
def test_nomina_list_includes_monthly_attendance_history(comedor, admision, sexo_f):
    representante = _create_representante(comedor=comedor, username="rep_nomina_hist")
    client = _auth_client_for_user(representante)

    ciudadano = Ciudadano.objects.create(
        nombre="Julia",
        apellido="Suarez",
        documento=28765432,
        fecha_nacimiento="1998-04-12",
        sexo=sexo_f,
    )
    nomina = Nomina.objects.create(
        admision=admision,
        ciudadano=ciudadano,
        estado=Nomina.ESTADO_ACTIVO,
    )
    RegistroAsistenciaNominaPWA.objects.create(
        nomina=nomina,
        periodicidad=RegistroAsistenciaNominaPWA.PERIODICIDAD_MENSUAL,
        periodo_referencia=timezone.localdate().replace(day=1),
        tomado_por=representante,
    )
    RegistroAsistenciaNominaPWA.objects.create(
        nomina=nomina,
        periodicidad=RegistroAsistenciaNominaPWA.PERIODICIDAD_MENSUAL,
        periodo_referencia=date(2026, 2, 1),
        tomado_por=representante,
    )

    response = client.get(f"/api/pwa/espacios/{comedor.id}/nomina/")

    assert response.status_code == 200
    assert len(response.data["results"]) == 1
    row = response.data["results"][0]
    assert row["asistencia_mes_actual"]["periodicidad"] == "mensual"
    assert row["asistencia_mes_actual"]["tomado_por"] == representante.username
    assert row["historial_asistencias"] == []


@pytest.mark.django_db
def test_nomina_history_endpoint_returns_attendance_history(comedor, admision, sexo_f):
    representante = _create_representante(
        comedor=comedor, username="rep_nomina_historial_endpoint"
    )
    client = _auth_client_for_user(representante)

    ciudadano = Ciudadano.objects.create(
        nombre="Lucia",
        apellido="Mendez",
        documento=29654321,
        fecha_nacimiento="2000-08-05",
        sexo=sexo_f,
    )
    nomina = Nomina.objects.create(
        admision=admision,
        ciudadano=ciudadano,
        estado=Nomina.ESTADO_ACTIVO,
    )
    RegistroAsistenciaNominaPWA.objects.create(
        nomina=nomina,
        periodicidad=RegistroAsistenciaNominaPWA.PERIODICIDAD_MENSUAL,
        periodo_referencia=timezone.localdate().replace(day=1),
        tomado_por=representante,
    )
    RegistroAsistenciaNominaPWA.objects.create(
        nomina=nomina,
        periodicidad=RegistroAsistenciaNominaPWA.PERIODICIDAD_MENSUAL,
        periodo_referencia=date(2026, 2, 1),
        tomado_por=representante,
    )

    response = client.get(
        f"/api/pwa/espacios/{comedor.id}/nomina/{nomina.id}/historial-asistencia/"
    )

    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]["periodo_referencia"] == str(
        timezone.localdate().replace(day=1)
    )
    assert response.data[0]["tomado_por"] == representante.username


@pytest.mark.django_db
def test_nomina_detail_endpoint_returns_linked_activities(
    comedor, admision, sexo_m, dia
):
    representante = _create_representante(
        comedor=comedor, username="rep_nomina_detalle"
    )
    client = _auth_client_for_user(representante)

    ciudadano = Ciudadano.objects.create(
        nombre="Pedro",
        apellido="Ramos",
        documento=31888777,
        fecha_nacimiento="1993-11-11",
        sexo=sexo_m,
    )
    nomina = Nomina.objects.create(
        admision=admision,
        ciudadano=ciudadano,
        estado=Nomina.ESTADO_ACTIVO,
    )
    NominaEspacioPWA.objects.create(
        nomina=nomina,
        asistencia_alimentaria=False,
        asistencia_actividades=True,
        activo=True,
    )
    catalogo = CatalogoActividadPWA.objects.filter(activo=True).first()
    actividad = ActividadEspacioPWA.objects.create(
        comedor=comedor,
        catalogo_actividad=catalogo,
        dia_actividad=dia,
        horario_actividad="16:00",
        hora_inicio="16:00",
        hora_fin="17:00",
        activo=True,
    )
    InscriptoActividadEspacioPWA.objects.create(
        actividad_espacio=actividad,
        nomina=nomina,
        activo=True,
    )

    response = client.get(f"/api/pwa/espacios/{comedor.id}/nomina/{nomina.id}/")

    assert response.status_code == 200
    assert response.data["cantidad_actividades"] == 1
    assert len(response.data["actividades"]) == 1
    assert response.data["actividades"][0]["horario"] == "16:00 a 17:00"


@pytest.mark.django_db
def test_nomina_register_attendance_current_month_is_idempotent(
    comedor, admision, sexo_m
):
    representante = _create_representante(comedor=comedor, username="rep_nomina_asis")
    client = _auth_client_for_user(representante)

    ciudadano = Ciudadano.objects.create(
        nombre="Mario",
        apellido="Benitez",
        documento=30111222,
        fecha_nacimiento="1991-07-20",
        sexo=sexo_m,
    )
    nomina = Nomina.objects.create(
        admision=admision,
        ciudadano=ciudadano,
        estado=Nomina.ESTADO_ACTIVO,
    )

    url = f"/api/pwa/espacios/{comedor.id}/nomina/{nomina.id}/registrar-asistencia/"

    first_response = client.post(url, {}, format="json")
    second_response = client.post(url, {}, format="json")

    assert first_response.status_code == 201
    assert first_response.data["created"] is True
    assert second_response.status_code == 200
    assert second_response.data["created"] is False
    assert (
        RegistroAsistenciaNominaPWA.objects.filter(
            nomina=nomina,
            periodicidad=RegistroAsistenciaNominaPWA.PERIODICIDAD_MENSUAL,
            periodo_referencia=timezone.localdate().replace(day=1),
        ).count()
        == 1
    )
    assert AuditoriaOperacionPWA.objects.filter(
        entidad="nomina_asistencia",
        accion="create",
        entidad_id=first_response.data["registro"]["id"],
    ).exists()


@pytest.mark.django_db
def test_nomina_bulk_attendance_alimentaria_syncs_current_period(
    comedor, admision, sexo_f, sexo_m
):
    representante = _create_representante(
        comedor=comedor, username="rep_nomina_bulk_alimentaria"
    )
    client = _auth_client_for_user(representante)

    ciudadano_1 = Ciudadano.objects.create(
        nombre="Alicia",
        apellido="Rojas",
        documento=25111222,
        fecha_nacimiento="1988-03-01",
        sexo=sexo_f,
    )
    ciudadano_2 = Ciudadano.objects.create(
        nombre="Bruno",
        apellido="Silva",
        documento=27111222,
        fecha_nacimiento="1986-04-01",
        sexo=sexo_m,
    )
    ciudadano_3 = Ciudadano.objects.create(
        nombre="Carla",
        apellido="Molina",
        documento=29111222,
        fecha_nacimiento="1992-05-01",
        sexo=sexo_f,
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
    nomina_3 = Nomina.objects.create(
        admision=admision,
        ciudadano=ciudadano_3,
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
        asistencia_alimentaria=True,
        asistencia_actividades=False,
        activo=True,
    )
    NominaEspacioPWA.objects.create(
        nomina=nomina_3,
        asistencia_alimentaria=False,
        asistencia_actividades=True,
        activo=True,
    )

    periodo_actual = timezone.localdate().replace(day=1)
    registro_existente = RegistroAsistenciaNominaPWA.objects.create(
        nomina=nomina_2,
        periodicidad=RegistroAsistenciaNominaPWA.PERIODICIDAD_MENSUAL,
        periodo_referencia=periodo_actual,
        tomado_por=representante,
    )

    response = client.post(
        f"/api/pwa/espacios/{comedor.id}/nomina/asistencia-alimentaria/",
        {"nomina_ids": [nomina_1.id]},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["periodo_label"] == periodo_actual.strftime("%m/%Y")
    assert response.data["selected_nomina_ids"] == [nomina_1.id]
    assert response.data["created_count"] == 1
    assert response.data["deleted_count"] == 1
    assert (
        RegistroAsistenciaNominaPWA.objects.filter(
            nomina=nomina_1,
            periodicidad=RegistroAsistenciaNominaPWA.PERIODICIDAD_MENSUAL,
            periodo_referencia=periodo_actual,
        ).count()
        == 1
    )
    assert not RegistroAsistenciaNominaPWA.objects.filter(
        pk=registro_existente.id
    ).exists()
    assert AuditoriaOperacionPWA.objects.filter(
        entidad="nomina_asistencia",
        accion="create",
        metadata__origen="bulk_alimentaria",
    ).exists()
    assert AuditoriaOperacionPWA.objects.filter(
        entidad="nomina_asistencia",
        accion="delete",
        entidad_id=registro_existente.id,
        metadata__origen="bulk_alimentaria",
    ).exists()


@pytest.mark.django_db
def test_nomina_bulk_attendance_alimentaria_rejects_non_alimentaria_rows(
    comedor, admision, sexo_f
):
    representante = _create_representante(
        comedor=comedor, username="rep_nomina_bulk_invalid"
    )
    client = _auth_client_for_user(representante)

    ciudadano = Ciudadano.objects.create(
        nombre="Paula",
        apellido="Acosta",
        documento=30123456,
        fecha_nacimiento="1990-06-15",
        sexo=sexo_f,
    )
    nomina = Nomina.objects.create(
        admision=admision,
        ciudadano=ciudadano,
        estado=Nomina.ESTADO_ACTIVO,
    )
    NominaEspacioPWA.objects.create(
        nomina=nomina,
        asistencia_alimentaria=False,
        asistencia_actividades=True,
        activo=True,
    )

    response = client.post(
        f"/api/pwa/espacios/{comedor.id}/nomina/asistencia-alimentaria/",
        {"nomina_ids": [nomina.id]},
        format="json",
    )

    assert response.status_code == 400
    assert "nomina_ids" in response.data["detail"]
