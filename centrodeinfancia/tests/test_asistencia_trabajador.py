import datetime

import pytest
from django.contrib.auth.models import Permission, User
from django.urls import reverse

from centrodeinfancia.models import (
    AsistenciaTrabajador,
    CentroDeInfancia,
    Trabajador,
)
from core.models import Provincia
from users.models import Profile


def _crear_usuario(username, provincia=None, *, superuser=False, permisos=None):
    permisos = permisos or []
    if superuser:
        user = User.objects.create_superuser(
            username=username,
            email=f"{username}@example.com",
            password="test1234",
        )
    else:
        user = User.objects.create_user(username=username, password="test1234")
        if permisos:
            user.user_permissions.add(*Permission.objects.filter(codename__in=permisos))

    profile, _ = Profile.objects.get_or_create(user=user)
    profile.provincia = provincia
    profile.save()
    return user


def _url(centro):
    return reverse("centrodeinfancia_trabajadores_asistencia", kwargs={"pk": centro.pk})


@pytest.mark.django_db
def test_asistencia_get_renderiza_personal(client):
    user = _crear_usuario("super-asis-get", superuser=True)
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(nombre="CDI Asistencia")
    Trabajador.objects.create(centro=centro, nombre="Ana", apellido="Lopez")
    Trabajador.objects.create(centro=centro, nombre="Beto", apellido="Diaz")

    response = client.get(_url(centro))

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "Lopez, Ana" in content
    assert "Diaz, Beto" in content
    assert "Registro de asistencia" in content
    assert response.context["total_sin_marcar"] == 2
    assert response.context["total_presentes"] == 0


@pytest.mark.django_db
def test_asistencia_get_carga_estado_guardado(client):
    user = _crear_usuario("super-asis-load", superuser=True)
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(nombre="CDI Historial")
    trabajador = Trabajador.objects.create(
        centro=centro, nombre="Ana", apellido="Lopez"
    )
    fecha = datetime.date(2026, 6, 1)
    AsistenciaTrabajador.objects.create(
        trabajador=trabajador,
        fecha=fecha,
        presente=True,
        observaciones="Llegó temprano",
        registrado_por=user,
    )

    response = client.get(_url(centro), {"fecha": "2026-06-01"})

    assert response.status_code == 200
    assert response.context["fecha"] == fecha
    assert response.context["total_presentes"] == 1
    assert response.context["filas"][0]["presente"] is True
    content = response.content.decode("utf-8")
    assert f'name="obs_{trabajador.pk}"' in content
    assert 'type="text"' in content
    assert 'value="Llegó temprano"' in content


@pytest.mark.django_db
def test_asistencia_fuera_de_scope_devuelve_404(client):
    provincia_a = Provincia.objects.create(nombre="Mendoza")
    provincia_b = Provincia.objects.create(nombre="Jujuy")
    user = _crear_usuario(
        "user-asis-scope",
        provincia=provincia_a,
        permisos=["change_centrodeinfancia"],
    )
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(nombre="CDI Jujuy", provincia=provincia_b)

    response = client.get(_url(centro))

    assert response.status_code == 404


@pytest.mark.django_db
def test_asistencia_post_crea_registros(client):
    user = _crear_usuario("super-asis-post", superuser=True)
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(nombre="CDI Post")
    t1 = Trabajador.objects.create(centro=centro, nombre="Ana", apellido="Lopez")
    t2 = Trabajador.objects.create(centro=centro, nombre="Beto", apellido="Diaz")

    response = client.post(
        _url(centro),
        {
            "fecha": "2026-06-10",
            f"presente_{t1.pk}": "1",
            f"obs_{t1.pk}": "",
            f"presente_{t2.pk}": "0",
            f"obs_{t2.pk}": "llegó tarde",
        },
    )

    assert response.status_code == 302
    fecha = datetime.date(2026, 6, 10)
    a1 = AsistenciaTrabajador.objects.get(trabajador=t1, fecha=fecha)
    a2 = AsistenciaTrabajador.objects.get(trabajador=t2, fecha=fecha)
    assert a1.presente is True
    assert a1.registrado_por == user
    assert a2.presente is False
    assert a2.observaciones == "llegó tarde"


@pytest.mark.django_db
def test_asistencia_post_actualiza_sin_duplicar(client):
    user = _crear_usuario("super-asis-update", superuser=True)
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(nombre="CDI Update")
    trabajador = Trabajador.objects.create(
        centro=centro, nombre="Ana", apellido="Lopez"
    )
    fecha = datetime.date(2026, 6, 15)
    AsistenciaTrabajador.objects.create(
        trabajador=trabajador,
        fecha=fecha,
        presente=True,
        registrado_por=user,
    )

    response = client.post(
        _url(centro),
        {
            "fecha": "2026-06-15",
            f"presente_{trabajador.pk}": "0",
            f"obs_{trabajador.pk}": "",
        },
    )

    assert response.status_code == 302
    registros = AsistenciaTrabajador.objects.filter(trabajador=trabajador, fecha=fecha)
    assert registros.count() == 1
    assert registros.first().presente is False


@pytest.mark.django_db
def test_asistencia_trabajador_sin_marcar_no_genera_registro(client):
    user = _crear_usuario("super-asis-skip", superuser=True)
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(nombre="CDI Skip")
    marcado = Trabajador.objects.create(centro=centro, nombre="Ana", apellido="Lopez")
    sin_marcar = Trabajador.objects.create(
        centro=centro, nombre="Beto", apellido="Diaz"
    )

    response = client.post(
        _url(centro),
        {"fecha": "2026-06-20", f"presente_{marcado.pk}": "1"},
    )

    assert response.status_code == 302
    assert AsistenciaTrabajador.objects.filter(trabajador=marcado).exists()
    assert not AsistenciaTrabajador.objects.filter(trabajador=sin_marcar).exists()


@pytest.mark.django_db
def test_asistencia_post_rechaza_fecha_invalida_sin_guardar(client):
    user = _crear_usuario("super-asis-invalid-date", superuser=True)
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(nombre="CDI Fecha inválida")
    trabajador = Trabajador.objects.create(
        centro=centro,
        nombre="Ana",
        apellido="Lopez",
    )

    response = client.post(
        _url(centro),
        {
            "fecha": "fecha-invalida",
            f"presente_{trabajador.pk}": "1",
        },
    )

    assert response.status_code == 302
    assert not AsistenciaTrabajador.objects.exists()


@pytest.mark.django_db
def test_asistencia_post_valida_todas_las_marcas_antes_de_guardar(client):
    user = _crear_usuario("super-asis-invalid-mark", superuser=True)
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(nombre="CDI Marca inválida")
    primero = Trabajador.objects.create(
        centro=centro,
        nombre="Ana",
        apellido="Arias",
    )
    segundo = Trabajador.objects.create(
        centro=centro,
        nombre="Beto",
        apellido="Benitez",
    )

    response = client.post(
        _url(centro),
        {
            "fecha": "2026-06-21",
            f"presente_{primero.pk}": "1",
            f"presente_{segundo.pk}": "desconocido",
        },
    )

    assert response.status_code == 302
    assert not AsistenciaTrabajador.objects.exists()


@pytest.mark.django_db
def test_asistencia_post_revierte_el_lote_si_falla_una_escritura(
    client,
    monkeypatch,
):
    user = _crear_usuario("super-asis-atomic", superuser=True)
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(nombre="CDI Lote atómico")
    primero = Trabajador.objects.create(
        centro=centro,
        nombre="Ana",
        apellido="Arias",
    )
    segundo = Trabajador.objects.create(
        centro=centro,
        nombre="Beto",
        apellido="Benitez",
    )
    guardar_original = AsistenciaTrabajador.save

    def guardar_con_falla(instancia, *args, **kwargs):
        if instancia.trabajador_id == segundo.pk:
            raise RuntimeError("falla simulada en segunda escritura")
        return guardar_original(instancia, *args, **kwargs)

    monkeypatch.setattr(AsistenciaTrabajador, "save", guardar_con_falla)

    with pytest.raises(RuntimeError, match="falla simulada"):
        client.post(
            _url(centro),
            {
                "fecha": "2026-06-22",
                f"presente_{primero.pk}": "1",
                f"presente_{segundo.pk}": "0",
            },
        )

    assert not AsistenciaTrabajador.objects.exists()


@pytest.mark.django_db
def test_asistencia_requiere_permiso_de_edicion(client):
    user = _crear_usuario("user-asis-denied", permisos=["view_centrodeinfancia"])
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(nombre="CDI Denegado")

    response = client.get(_url(centro))

    assert response.status_code == 403
