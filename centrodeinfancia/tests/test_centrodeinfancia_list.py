from datetime import date

import pytest
from django.contrib.auth.models import Permission, User
from django.urls import reverse

from ciudadanos.models import Ciudadano
from centrodeinfancia.models import CentroDeInfancia, NominaCentroInfancia
from core.models import Provincia


@pytest.mark.django_db
def test_listado_cdi_muestra_si_tiene_nomina(client):
    user = User.objects.create_user(username="listado-cdi", password="test1234")
    user.user_permissions.add(
        Permission.objects.get(codename="view_centrodeinfancia")
    )
    client.force_login(user)

    provincia = Provincia.objects.create(nombre="Buenos Aires")
    centro_con_nomina = CentroDeInfancia.objects.create(
        nombre="CDI con nomina",
        provincia=provincia,
    )
    centro_sin_nomina = CentroDeInfancia.objects.create(
        nombre="CDI sin nomina",
        provincia=provincia,
    )
    ciudadano = Ciudadano.objects.create(
        apellido="Gomez",
        nombre="Luz",
        fecha_nacimiento=date(2018, 6, 1),
        documento=44444444,
    )
    NominaCentroInfancia.objects.create(
        centro=centro_con_nomina,
        ciudadano=ciudadano,
        estado=NominaCentroInfancia.ESTADO_ACTIVO,
    )

    response = client.get(reverse("centrodeinfancia"))
    content = response.content.decode("utf-8")

    assert response.status_code == 200
    assert "tiene_nomina" in response.context["active_columns"]
    assert response.context["centros"][0].tiene_nomina is True
    assert response.context["centros"][1].tiene_nomina is False

    tiene_nomina_column = next(
        col
        for col in response.context["column_config"]["available"]
        if col["key"] == "tiene_nomina"
    )
    assert tiene_nomina_column["default"] is True
    assert tiene_nomina_column["required"] is False

    assert "Tiene nómina" in content
    assert 'data-tiene-nomina="Si"' in content
    assert 'data-tiene-nomina="No"' in content
