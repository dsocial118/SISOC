from datetime import date, timedelta

import pytest
from django.contrib.auth.models import Group, Permission, User
from django.urls import reverse
from django.utils import timezone

from ciudadanos.models import Ciudadano
from core.constants import UserGroups
from core.models import Provincia
from centrodefamilia.models import (
    AccesoCDF,
    Actividad,
    ActividadCentro,
    AsistenciaActividad,
    Categoria,
    Centro,
    ParticipanteActividad,
)
from centrodefamilia.services.asistencia import AsistenciaActividadService


@pytest.fixture(autouse=True)
def _grupo_cdf_referente(db):
    Group.objects.get_or_create(name=UserGroups.CDF_REFERENTE_CENTRO)


def _centro(nombre, provincia):
    return Centro.objects.create(
        nombre=nombre,
        provincia=provincia,
        tipo="faro",
        codigo=nombre[:20],
        domicilio_actividad="Dirección de prueba",
        telefono="123",
        celular="456",
        correo="centro@test.com",
        nombre_referente="Ref",
        apellido_referente="Ente",
        telefono_referente="789",
        correo_referente="ref@test.com",
    )


def _actividad(centro):
    categoria = Categoria.objects.create(nombre="Deportes")
    actividad = Actividad.objects.create(nombre="Fútbol", categoria=categoria)
    return ActividadCentro.objects.create(
        centro=centro,
        actividad=actividad,
        cantidad_personas=20,
        horariosdesde="10:00",
        horarioshasta="12:00",
    )


def _participante(actividad_centro, documento, estado="inscrito"):
    ciudadano = Ciudadano.objects.create(
        apellido=f"Apellido{documento}",
        nombre=f"Nombre{documento}",
        fecha_nacimiento=date(2000, 1, 1),
        documento=documento,
    )
    return ParticipanteActividad.objects.create(
        actividad_centro=actividad_centro,
        ciudadano=ciudadano,
        estado=estado,
    )


def _referente_con_acceso(centro):
    user = User.objects.create_user(username="ref-cdf", password="test1234")
    user.user_permissions.add(
        Permission.objects.get(
            content_type__app_label="centrodefamilia", codename="view_centro"
        )
    )
    AccesoCDF.objects.create(user=user, centro=centro, creado_por=user)
    return user


@pytest.fixture
def escenario(db):
    provincia = Provincia.objects.create(nombre="Buenos Aires Asist")
    centro = _centro("CDF Asistencia", provincia)
    actividad = _actividad(centro)
    return centro, actividad


# --------------------------- Service ---------------------------------------


@pytest.mark.django_db
def test_planilla_solo_incluye_inscritos(escenario):
    _, actividad = escenario
    inscrito = _participante(actividad, 30000001)
    _participante(actividad, 30000002, estado="lista_espera")
    _participante(actividad, 30000003, estado="dado_baja")

    filas = AsistenciaActividadService.obtener_planilla(actividad, timezone.localdate())

    assert [fila["participante"].pk for fila in filas] == [inscrito.pk]
    assert filas[0]["presente"] is None


@pytest.mark.django_db
def test_registrar_crea_y_actualiza_asistencia(escenario):
    _, actividad = escenario
    p1 = _participante(actividad, 30000011)
    p2 = _participante(actividad, 30000012)
    usuario = User.objects.create_user(username="registrador", password="x")
    hoy = timezone.localdate()

    AsistenciaActividadService.registrar(
        actividad, hoy, {p1.pk: "1", p2.pk: "0"}, usuario
    )

    assert AsistenciaActividad.objects.get(participante=p1, fecha=hoy).presente is True
    assert AsistenciaActividad.objects.get(participante=p2, fecha=hoy).presente is False

    # Re-toma: actualiza sin duplicar
    AsistenciaActividadService.registrar(
        actividad, hoy, {p1.pk: "0", p2.pk: "1"}, usuario
    )

    assert AsistenciaActividad.objects.filter(fecha=hoy).count() == 2
    assert AsistenciaActividad.objects.get(participante=p1, fecha=hoy).presente is False
    assert AsistenciaActividad.objects.get(participante=p2, fecha=hoy).presente is True


@pytest.mark.django_db
def test_parse_fecha_rechaza_futuras_e_invalidas():
    from django.core.exceptions import ValidationError

    manana = timezone.localdate() + timedelta(days=1)
    with pytest.raises(ValidationError):
        AsistenciaActividadService.parse_fecha(manana.strftime("%Y-%m-%d"))
    with pytest.raises(ValidationError):
        AsistenciaActividadService.parse_fecha("no-es-fecha")
    assert AsistenciaActividadService.parse_fecha(None) == timezone.localdate()


# --------------------------- Vista ------------------------------------------


@pytest.mark.django_db
def test_get_planilla_como_referente(client, escenario):
    centro, actividad = escenario
    _participante(actividad, 30000021)
    user = _referente_con_acceso(centro)
    client.force_login(user)

    response = client.get(
        reverse("actividadcentro_asistencia", kwargs={"pk": actividad.pk})
    )

    assert response.status_code == 200
    assert "Apellido30000021" in response.content.decode()


@pytest.mark.django_db
def test_post_guarda_asistencia_y_redirige(client, escenario):
    centro, actividad = escenario
    p1 = _participante(actividad, 30000031)
    p2 = _participante(actividad, 30000032)
    user = _referente_con_acceso(centro)
    client.force_login(user)
    hoy = timezone.localdate()

    response = client.post(
        reverse("actividadcentro_asistencia", kwargs={"pk": actividad.pk}),
        {
            "fecha": hoy.strftime("%Y-%m-%d"),
            f"presente_{p1.pk}": "1",
            f"presente_{p2.pk}": "0",
        },
    )

    assert response.status_code == 302
    asistencia_p1 = AsistenciaActividad.objects.get(participante=p1, fecha=hoy)
    assert asistencia_p1.presente is True
    assert asistencia_p1.registrado_por == user
    assert AsistenciaActividad.objects.get(participante=p2, fecha=hoy).presente is False


@pytest.mark.django_db
def test_post_fecha_futura_no_registra(client, escenario):
    centro, actividad = escenario
    p1 = _participante(actividad, 30000041)
    user = _referente_con_acceso(centro)
    client.force_login(user)
    manana = timezone.localdate() + timedelta(days=1)

    response = client.post(
        reverse("actividadcentro_asistencia", kwargs={"pk": actividad.pk}),
        {
            "fecha": manana.strftime("%Y-%m-%d"),
            f"presente_{p1.pk}": "1",
        },
    )

    assert response.status_code == 302
    assert not AsistenciaActividad.objects.exists()


@pytest.mark.django_db
def test_usuario_sin_vinculo_recibe_403(client, escenario):
    _, actividad = escenario
    user = User.objects.create_user(username="ajeno", password="x")
    user.user_permissions.add(
        Permission.objects.get(
            content_type__app_label="centrodefamilia", codename="view_centro"
        )
    )
    client.force_login(user)

    response = client.get(
        reverse("actividadcentro_asistencia", kwargs={"pk": actividad.pk})
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_superusuario_puede_tomar_asistencia(client, escenario):
    _, actividad = escenario
    _participante(actividad, 30000051)
    admin = User.objects.create_superuser(username="admin-asist", password="x")
    client.force_login(admin)

    response = client.get(
        reverse("actividadcentro_asistencia", kwargs={"pk": actividad.pk})
    )

    assert response.status_code == 200
