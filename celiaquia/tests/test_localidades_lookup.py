"""Tests for test localidades lookup."""

import pytest
from django.urls import reverse
from django.contrib.auth.models import Group, User

from core.models import Provincia, Municipio, Localidad
from users.models import Profile


@pytest.mark.django_db
def test_localidades_lookup_filters(client):
    grupo = Group.objects.create(name="ProvinciaCeliaquia")

    prov1 = Provincia.objects.create(nombre="Buenos Aires")
    muni1 = Municipio.objects.create(nombre="La Plata", provincia=prov1)
    loc1 = Localidad.objects.create(nombre="Centro", municipio=muni1)

    prov2 = Provincia.objects.create(nombre="Cordoba")
    muni2 = Municipio.objects.create(nombre="Capital", provincia=prov2)
    Localidad.objects.create(nombre="Cba Centro", municipio=muni2)

    user = User.objects.create_user(username="prov", password="pass")
    profile, _ = Profile.objects.get_or_create(user=user)
    profile.es_usuario_provincial = True
    profile.provincia = prov1
    profile.save()
    user.groups.add(grupo)
    client.force_login(user)

    url = reverse("expediente_localidades_lookup")

    resp = client.get(url)
    data = resp.json()
    assert any(item["localidad_id"] == loc1.id for item in data)

    resp = client.get(url, {"provincia": prov1.id})
    data = resp.json()
    assert len(data) == 1
    assert data[0]["localidad_id"] == loc1.id
    assert data[0]["provincia_id"] == prov1.id
    assert data[0]["municipio_id"] == muni1.id
    assert data[0]["provincia_nombre"] == prov1.nombre
    assert data[0]["municipio_nombre"] == muni1.nombre

    resp = client.get(url, {"provincia": prov1.id, "municipio": muni1.id})
    data = resp.json()
    assert len(data) == 1
    assert data[0]["localidad_id"] == loc1.id
