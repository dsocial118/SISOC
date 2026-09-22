"""Tests de los filtros combinables del listado de Organizaciones (issue #2505)."""

import json

import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from core.models import Localidad, Municipio, Provincia
from organizaciones.filter_config import (
    FIELD_MAP,
    FIELD_TYPES,
    ORGANIZACION_ADVANCED_FILTER,
    get_filters_ui_config,
)
from organizaciones.models import Organizacion, TipoEntidad


def test_config_expone_campos_con_mapeo_y_operadores():
    config = get_filters_ui_config()
    nombres = {field["name"] for field in config["fields"]}

    # Todo campo ofrecido en la UI tiene mapeo ORM y tipo declarado.
    assert nombres <= set(FIELD_MAP)
    assert nombres <= set(FIELD_TYPES)
    assert config["defaultField"] == "nombre"
    for tipo in ("text", "number", "choice", "boolean", "date"):
        assert config["operators"][tipo]


@pytest.mark.django_db
def test_config_toma_los_tipos_de_entidad_de_la_base():
    TipoEntidad.objects.create(nombre="Asociacion civil")
    from django.core.cache import cache

    cache.clear()

    config = get_filters_ui_config()
    tipo_entidad = next(
        field for field in config["fields"] if field["name"] == "tipo_entidad"
    )

    assert {"value": "Asociacion civil", "label": "Asociacion civil"} in tipo_entidad[
        "choices"
    ]


@pytest.mark.django_db
def test_engine_combina_filtros_de_distintos_campos():
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    otra = Provincia.objects.create(nombre="Cordoba")
    tipo = TipoEntidad.objects.create(nombre="Fundacion")
    objetivo = Organizacion.objects.create(
        nombre="Merendero Sur", provincia=provincia, tipo_entidad=tipo
    )
    Organizacion.objects.create(nombre="Merendero Norte", provincia=otra)
    Organizacion.objects.create(nombre="Otra cosa", provincia=provincia)

    payload = {
        "logic": "AND",
        "items": [
            {"field": "nombre", "op": "contains", "value": "Merendero"},
            {"field": "provincia", "op": "contains", "value": "Buenos"},
        ],
    }
    resultado = ORGANIZACION_ADVANCED_FILTER.filter_queryset(
        Organizacion.objects.all(), {"filters": json.dumps(payload)}
    )

    assert list(resultado) == [objetivo]


@pytest.mark.django_db
def test_listado_de_organizaciones_aplica_filters_y_expone_config(client):
    admin = User.objects.create_superuser("admin_org_filtros", "org@test.com", "test")
    provincia = Provincia.objects.create(nombre="Santa Fe")
    municipio = Municipio.objects.create(nombre="Rosario", provincia=provincia)
    Localidad.objects.create(nombre="Centro", municipio=municipio)
    buscada = Organizacion.objects.create(nombre="Comedor Esperanza", cuit=20111111112)
    Organizacion.objects.create(nombre="Otra organizacion", cuit=20222222223)
    client.force_login(admin)

    payload = json.dumps(
        {
            "logic": "AND",
            "items": [{"field": "nombre", "op": "contains", "value": "Esperanza"}],
        }
    )
    response = client.get(reverse("organizaciones"), {"filters": payload})

    assert response.status_code == 200
    assert response.context["filters_mode"] is True
    assert response.context["filters_config"]["fields"]
    ids = [org.pk for org in response.context["organizaciones"]]
    assert ids == [buscada.pk]
