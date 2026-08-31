from datetime import date

import pytest
from django.contrib.auth.models import Permission, User
from django.urls import reverse

from centrodeinfancia.models import (
    AsistenciaNominaCentroInfancia,
    CentroDeInfancia,
    NominaCentroInfancia,
)
from ciudadanos.models import Ciudadano
from core.models import Provincia
from users.models import Profile


def _url(centro):
    return reverse("centrodeinfancia_nomina_asistencia", kwargs={"pk": centro.pk})


def _crear_nomina(centro, *, apellido, nombre, documento, estado):
    ciudadano = Ciudadano.objects.create(
        apellido=apellido,
        nombre=nombre,
        documento=documento,
        fecha_nacimiento=date(2020, 1, 1),
    )
    return NominaCentroInfancia.objects.create(
        centro=centro,
        ciudadano=ciudadano,
        apellido=apellido,
        nombre=nombre,
        dni=documento,
        estado=estado,
    )


@pytest.mark.django_db
def test_asistencia_get_muestra_solo_nomina_activa(client):
    user = User.objects.create_superuser(
        username="super-asistencia-nomina",
        email="asistencia@example.com",
        password="test1234",
    )
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(nombre="CDI Asistencia Nómina")
    _crear_nomina(
        centro,
        apellido="Activa",
        nombre="Ana",
        documento=40111222,
        estado=NominaCentroInfancia.ESTADO_ACTIVO,
    )
    pendiente = _crear_nomina(
        centro,
        apellido="Pendiente",
        nombre="Paz",
        documento=40111223,
        estado=NominaCentroInfancia.ESTADO_PENDIENTE,
    )
    _crear_nomina(
        centro,
        apellido="Baja",
        nombre="Beto",
        documento=40111224,
        estado=NominaCentroInfancia.ESTADO_BAJA,
    )
    fecha = date(2026, 7, 1)
    AsistenciaNominaCentroInfancia.objects.create(
        nomina=pendiente,
        fecha=fecha,
        presente=True,
        registrado_por=user,
    )

    response = client.get(_url(centro), {"fecha": fecha.isoformat()})

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "Activa, Ana" in content
    assert "Pendiente, Paz" not in content
    assert "Baja, Beto" not in content
    assert response.context["total_sin_marcar"] == 1


@pytest.mark.django_db
def test_asistencia_get_incluye_baja_con_asistencia_historica(client):
    user = User.objects.create_superuser(
        username="super-asistencia-historica",
        email="historica@example.com",
        password="test1234",
    )
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(nombre="CDI Histórico")
    baja = _crear_nomina(
        centro,
        apellido="Baja",
        nombre="Beto",
        documento=40111225,
        estado=NominaCentroInfancia.ESTADO_BAJA,
    )
    fecha = date(2026, 7, 1)
    AsistenciaNominaCentroInfancia.objects.create(
        nomina=baja,
        fecha=fecha,
        presente=True,
        registrado_por=user,
    )

    response = client.get(_url(centro), {"fecha": fecha.isoformat()})

    assert response.status_code == 200
    assert "Baja, Beto" in response.content.decode("utf-8")
    assert response.context["filas"][0]["presente"] is True

    response = client.post(
        _url(centro),
        {"fecha": fecha.isoformat(), f"presente_{baja.pk}": "0"},
    )

    assert response.status_code == 302
    asistencia = AsistenciaNominaCentroInfancia.objects.get(nomina=baja, fecha=fecha)
    assert asistencia.presente is False


@pytest.mark.django_db
def test_asistencia_post_crea_actualiza_y_elimina_marcas(client):
    user = User.objects.create_superuser(
        username="super-asistencia-post",
        email="post@example.com",
        password="test1234",
    )
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(nombre="CDI Post")
    primera = _crear_nomina(
        centro,
        apellido="Arias",
        nombre="Ana",
        documento=40111226,
        estado=NominaCentroInfancia.ESTADO_ACTIVO,
    )
    segunda = _crear_nomina(
        centro,
        apellido="Benitez",
        nombre="Beto",
        documento=40111227,
        estado=NominaCentroInfancia.ESTADO_ACTIVO,
    )
    fecha = "2026-07-02"

    response = client.post(
        _url(centro),
        {
            "fecha": fecha,
            f"presente_{primera.pk}": "1",
            f"presente_{segunda.pk}": "0",
            f"obs_{segunda.pk}": "Llegó tarde",
        },
    )

    assert response.status_code == 302
    assert AsistenciaNominaCentroInfancia.objects.filter(
        nomina=primera,
        fecha=fecha,
        presente=True,
    ).exists()
    segunda_asistencia = AsistenciaNominaCentroInfancia.objects.get(
        nomina=segunda,
        fecha=fecha,
    )
    assert segunda_asistencia.presente is False
    assert segunda_asistencia.observaciones == "Llegó tarde"

    response = client.post(
        _url(centro),
        {"fecha": fecha, f"presente_{segunda.pk}": "1"},
    )

    assert response.status_code == 302
    assert not AsistenciaNominaCentroInfancia.objects.filter(
        nomina=primera,
        fecha=fecha,
    ).exists()
    segunda_asistencia.refresh_from_db()
    assert segunda_asistencia.presente is True
    assert segunda_asistencia.observaciones is None


@pytest.mark.django_db
def test_asistencia_post_invalida_no_guarda_ninguna_fila(client):
    user = User.objects.create_superuser(
        username="super-asistencia-invalida",
        email="invalida@example.com",
        password="test1234",
    )
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(nombre="CDI Lote Inválido")
    primera = _crear_nomina(
        centro,
        apellido="Arias",
        nombre="Ana",
        documento=40111230,
        estado=NominaCentroInfancia.ESTADO_ACTIVO,
    )
    segunda = _crear_nomina(
        centro,
        apellido="Benitez",
        nombre="Beto",
        documento=40111231,
        estado=NominaCentroInfancia.ESTADO_ACTIVO,
    )

    response = client.post(
        _url(centro),
        {
            "fecha": "2026-07-03",
            f"presente_{primera.pk}": "1",
            f"presente_{segunda.pk}": "invalida",
        },
    )

    assert response.status_code == 302
    assert not AsistenciaNominaCentroInfancia.objects.exists()


@pytest.mark.django_db
def test_asistencia_post_revierte_lote_si_falla_una_escritura(client, monkeypatch):
    user = User.objects.create_superuser(
        username="super-asistencia-atomica",
        email="atomica@example.com",
        password="test1234",
    )
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(nombre="CDI Lote Atómico")
    primera = _crear_nomina(
        centro,
        apellido="Arias",
        nombre="Ana",
        documento=40111232,
        estado=NominaCentroInfancia.ESTADO_ACTIVO,
    )
    segunda = _crear_nomina(
        centro,
        apellido="Benitez",
        nombre="Beto",
        documento=40111233,
        estado=NominaCentroInfancia.ESTADO_ACTIVO,
    )
    guardar_original = AsistenciaNominaCentroInfancia.save

    def guardar_con_falla(instancia, *args, **kwargs):
        if instancia.nomina_id == segunda.pk:
            raise RuntimeError("falla simulada en segunda escritura")
        return guardar_original(instancia, *args, **kwargs)

    monkeypatch.setattr(AsistenciaNominaCentroInfancia, "save", guardar_con_falla)

    with pytest.raises(RuntimeError, match="falla simulada"):
        client.post(
            _url(centro),
            {
                "fecha": "2026-07-04",
                f"presente_{primera.pk}": "1",
                f"presente_{segunda.pk}": "0",
            },
        )

    assert not AsistenciaNominaCentroInfancia.objects.exists()


@pytest.mark.django_db
def test_calendario_retorna_solo_dias_del_centro_y_mes(client):
    user = User.objects.create_superuser(
        username="super-asistencia-calendario",
        email="calendar@example.com",
        password="test1234",
    )
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(nombre="CDI Calendario")
    otra = CentroDeInfancia.objects.create(nombre="CDI Otro")
    nomina = _crear_nomina(
        centro,
        apellido="Calendario",
        nombre="Cata",
        documento=40111228,
        estado=NominaCentroInfancia.ESTADO_ACTIVO,
    )
    otra_nomina = _crear_nomina(
        otra,
        apellido="Otro",
        nombre="Omar",
        documento=40111229,
        estado=NominaCentroInfancia.ESTADO_ACTIVO,
    )
    AsistenciaNominaCentroInfancia.objects.create(
        nomina=nomina,
        fecha=date(2026, 7, 3),
        presente=True,
        registrado_por=user,
    )
    AsistenciaNominaCentroInfancia.objects.create(
        nomina=nomina,
        fecha=date(2026, 8, 3),
        presente=False,
        registrado_por=user,
    )
    AsistenciaNominaCentroInfancia.objects.create(
        nomina=otra_nomina,
        fecha=date(2026, 7, 4),
        presente=True,
        registrado_por=user,
    )

    response = client.get(
        reverse(
            "centrodeinfancia_nomina_asistencia_calendario",
            kwargs={"pk": centro.pk},
        ),
        {"mes": "2026-07"},
    )

    assert response.status_code == 200
    assert response.json() == {"dias": ["2026-07-03"]}


@pytest.mark.django_db
def test_ruta_historica_redirige_a_asistencia_nomina(client):
    user = User.objects.create_superuser(
        username="super-asistencia-redireccion",
        email="redirect@example.com",
        password="test1234",
    )
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(nombre="CDI Redirección")

    response = client.get(
        reverse("centrodeinfancia_trabajadores_asistencia", kwargs={"pk": centro.pk})
    )

    assert response.status_code == 302
    assert response.url == _url(centro)


@pytest.mark.django_db
def test_asistencia_requiere_permiso_de_edicion(client):
    user = User.objects.create_user(
        username="asistencia-sin-edicion",
        password="test1234",
    )
    user.user_permissions.add(Permission.objects.get(codename="view_centrodeinfancia"))
    Profile.objects.get_or_create(user=user)
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(nombre="CDI Sin edición")

    response = client.get(_url(centro))

    assert response.status_code == 403


@pytest.mark.django_db
def test_asistencia_fuera_del_scope_devuelve_404(client):
    provincia_usuario = Provincia.objects.create(nombre="Mendoza")
    provincia_centro = Provincia.objects.create(nombre="Jujuy")
    user = User.objects.create_user(username="asistencia-scope", password="test1234")
    user.user_permissions.add(
        Permission.objects.get(codename="change_centrodeinfancia")
    )
    profile, _ = Profile.objects.get_or_create(user=user)
    profile.provincia = provincia_usuario
    profile.save()
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(
        nombre="CDI Fuera de scope",
        provincia=provincia_centro,
    )

    response = client.get(_url(centro))

    assert response.status_code == 404
