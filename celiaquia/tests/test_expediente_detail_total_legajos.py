"""Contador de legajos en el detalle del expediente (tk #1947)."""

import re
from datetime import date

import pytest
from django.contrib.auth.models import Permission, User
from django.urls import reverse

from celiaquia.models import (
    EstadoExpediente,
    EstadoLegajo,
    Expediente,
    ExpedienteCiudadano,
)
from ciudadanos.models import Ciudadano, GrupoFamiliar
from users.models import Profile


def _usuario():
    user = User.objects.create_user(username="prov", password="pass")
    user.user_permissions.add(
        Permission.objects.get(
            content_type__app_label="celiaquia",
            codename="view_expediente",
        )
    )
    Profile.objects.get_or_create(user=user)
    return user


def _expediente(user):
    estado = EstadoExpediente.objects.create(nombre="CREADO")
    return Expediente.objects.create(usuario_provincia=user, estado=estado)


def _legajo(expediente, documento, *, nombre="Ana", fecha_nacimiento=date(2010, 1, 1)):
    estado_legajo, _ = EstadoLegajo.objects.get_or_create(nombre="DOCUMENTO_PENDIENTE")
    ciudadano = Ciudadano.objects.create(
        apellido="Perez",
        nombre=nombre,
        fecha_nacimiento=fecha_nacimiento,
        documento=documento,
    )
    return ExpedienteCiudadano.objects.create(
        expediente=expediente,
        ciudadano=ciudadano,
        estado=estado_legajo,
    )


@pytest.mark.django_db
def test_detalle_expone_el_total_de_legajos(client):
    user = _usuario()
    expediente = _expediente(user)
    for i in range(5):
        _legajo(expediente, 30000000 + i)

    client.force_login(user)
    response = client.get(reverse("expediente_detail", args=[expediente.pk]))

    assert response.status_code == 200
    assert response.context["legajos_total"] == 5


@pytest.mark.django_db
def test_el_total_coincide_con_las_filas_mostradas(client):
    """El contador no puede desincronizarse de la tabla: el armado del árbol
    responsable/hijo reordena y deduplica los legajos, así que se comprueba que
    siga cubriendo a todos."""
    user = _usuario()
    expediente = _expediente(user)

    responsable = _legajo(
        expediente, 40000001, nombre="Madre", fecha_nacimiento=date(1985, 1, 1)
    )
    hijo_a = _legajo(expediente, 40000002, nombre="Hijo A")
    hijo_b = _legajo(expediente, 40000003, nombre="Hijo B")
    suelto = _legajo(expediente, 40000004, nombre="Sin vinculo")

    for hijo in (hijo_a, hijo_b):
        GrupoFamiliar.objects.create(
            ciudadano_1=responsable.ciudadano,
            ciudadano_2=hijo.ciudadano,
            vinculo="Padre/Madre",
        )

    client.force_login(user)
    response = client.get(reverse("expediente_detail", args=[expediente.pk]))

    total = response.context["legajos_total"]
    mostrados = response.context["legajos_enriquecidos"]
    assert total == 4
    assert len(mostrados) == total
    assert {legajo.pk for legajo in mostrados} == {
        responsable.pk,
        hijo_a.pk,
        hijo_b.pk,
        suelto.pk,
    }


@pytest.mark.django_db
def test_los_legajos_eliminados_no_se_cuentan(client):
    """La baja de un legajo es lógica: no debe seguir sumando al total."""
    user = _usuario()
    expediente = _expediente(user)
    _legajo(expediente, 50000001)
    eliminado = _legajo(expediente, 50000002)
    eliminado.delete(user=user)

    client.force_login(user)
    response = client.get(reverse("expediente_detail", args=[expediente.pk]))

    assert response.context["legajos_total"] == 1


@pytest.mark.django_db
def test_expediente_sin_legajos_muestra_cero(client):
    user = _usuario()
    expediente = _expediente(user)

    client.force_login(user)
    response = client.get(reverse("expediente_detail", args=[expediente.pk]))

    assert response.context["legajos_total"] == 0


@pytest.mark.django_db
def test_el_total_se_renderiza_junto_al_titulo(client):
    user = _usuario()
    expediente = _expediente(user)
    for i in range(3):
        _legajo(expediente, 60000000 + i)

    client.force_login(user)
    html = client.get(
        reverse("expediente_detail", args=[expediente.pk])
    ).content.decode()

    titulo = re.search(r"<h5[^>]*>\s*Legajos.*?</h5>", html, re.DOTALL)
    assert titulo is not None, "no se encontró el título de la sección Legajos"
    bloque = titulo.group(0)
    assert "Cantidad total de personas asociadas al expediente" in bloque
    # El badge se explica solo: no alcanza con el número suelto.
    assert "3 personas" in bloque


@pytest.mark.django_db
def test_el_badge_usa_el_singular_con_un_solo_legajo(client):
    user = _usuario()
    expediente = _expediente(user)
    _legajo(expediente, 61000001)

    client.force_login(user)
    html = client.get(
        reverse("expediente_detail", args=[expediente.pk])
    ).content.decode()

    titulo = re.search(r"<h5[^>]*>\s*Legajos.*?</h5>", html, re.DOTALL).group(0)
    assert "1 persona" in titulo
    assert "1 personas" not in titulo
