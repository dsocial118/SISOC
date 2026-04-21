"""Tests for test localidades lookup."""

import pytest
from django.urls import reverse
from django.db import connection
from django.contrib.auth.models import Group, User
from django.test.utils import CaptureQueriesContext

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


@pytest.mark.django_db
def test_localidades_lookup_uses_single_localidad_query_for_provincia_filter(client):
    grupo = Group.objects.create(name="ProvinciaCeliaquia")

    prov = Provincia.objects.create(nombre="Buenos Aires")
    other_prov = Provincia.objects.create(nombre="Cordoba")

    muni_a = Municipio.objects.create(nombre="La Plata", provincia=prov)
    muni_b = Municipio.objects.create(nombre="Berisso", provincia=prov)
    other_muni = Municipio.objects.create(nombre="Capital", provincia=other_prov)

    Localidad.objects.create(nombre="Centro", municipio=muni_a)
    Localidad.objects.create(nombre="Tolosa", municipio=muni_a)
    Localidad.objects.create(nombre="Villa Arguello", municipio=muni_b)
    Localidad.objects.create(nombre="Cba Centro", municipio=other_muni)

    user = User.objects.create_user(username="prov_perf", password="pass")
    profile, _ = Profile.objects.get_or_create(user=user)
    profile.es_usuario_provincial = True
    profile.provincia = prov
    profile.save()
    user.groups.add(grupo)
    client.force_login(user)

    url = reverse("expediente_localidades_lookup")

    with CaptureQueriesContext(connection) as ctx:
        response = client.get(url, {"provincia": prov.id})

    assert response.status_code == 200
    data = response.json()
    assert {item["localidad_nombre"] for item in data} == {
        "Centro",
        "Tolosa",
        "Villa Arguello",
    }

    localidad_queries = [
        query["sql"]
        for query in ctx.captured_queries
        if "core_localidad" in query["sql"].lower()
    ]
    assert len(localidad_queries) == 1
