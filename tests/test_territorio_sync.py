"""Pruebas de la sincronización create-only del fixture territorial."""

import json

import pytest

from core.models import Localidad, Municipio, Provincia
from core.services.territorio_sync import sync_territorio_desde_fixture


pytestmark = pytest.mark.django_db


def _fixture(path):
    path.write_text(
        json.dumps(
            [
                {
                    "model": "core.provincia",
                    "pk": 101,
                    "fields": {"nombre": "Córdoba"},
                },
                {
                    "model": "core.municipio",
                    "pk": 102,
                    "fields": {"nombre": "Capital", "provincia": 101},
                },
                {
                    "model": "core.municipio",
                    "pk": 103,
                    "fields": {"nombre": "Interior", "provincia": 101},
                },
                {
                    "model": "core.localidad",
                    "pk": 104,
                    "fields": {"nombre": "VILLA", "municipio": 102},
                },
                {
                    "model": "core.localidad",
                    "pk": 105,
                    "fields": {"nombre": "Villa", "municipio": 103},
                },
                {
                    "model": "core.localidad",
                    "pk": 106,
                    "fields": {"nombre": "Nueva", "municipio": 102},
                },
            ],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def test_sync_crea_solo_faltantes_normaliza_y_es_idempotente(tmp_path):
    provincia = Provincia.objects.create(pk=10, nombre="CÓRDOBA")
    capital = Municipio.objects.create(pk=11, nombre="cApItAl", provincia=provincia)
    Municipio.objects.create(pk=12, nombre="INTERIOR", provincia=provincia)
    localidad_existente = Localidad.objects.create(
        pk=13, nombre="vÍlla", municipio=capital
    )
    Localidad.objects.create(pk=14, nombre="Intacta", municipio=capital)
    fixture_path = tmp_path / "territorio.json"
    _fixture(fixture_path)

    primer_resultado = sync_territorio_desde_fixture(fixture_path)

    provincia.refresh_from_db()
    capital.refresh_from_db()
    localidad_existente.refresh_from_db()
    assert provincia.pk == 10 and provincia.nombre == "CÓRDOBA"
    assert capital.pk == 11 and capital.nombre == "cApItAl"
    assert localidad_existente.pk == 13 and localidad_existente.nombre == "vÍlla"
    assert primer_resultado == {
        "provincias_creadas": 0,
        "municipios_creadas": 0,
        "localidades_creadas": 2,
        "saltadas_por_integridad": 0,
    }
    assert Localidad.objects.filter(municipio=capital).count() == 3
    assert (
        Localidad.objects.filter(nombre="Villa", municipio__nombre="INTERIOR").count()
        == 1
    )

    segundo_resultado = sync_territorio_desde_fixture(fixture_path)

    assert segundo_resultado == {
        "provincias_creadas": 0,
        "municipios_creadas": 0,
        "localidades_creadas": 0,
        "saltadas_por_integridad": 0,
    }
    assert Localidad.objects.count() == 4
