"""Pruebas del generador standalone de BAHRA."""

import csv
import importlib.util
import json
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / ("actualizar_territorio_desde_bahra.py")
)
SPEC = importlib.util.spec_from_file_location(
    "actualizar_territorio_bahra", SCRIPT_PATH
)
bahra = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bahra)


def _escribir_csv(path, columnas, filas):
    with path.open("w", encoding="utf-8", newline="") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=columnas)
        writer.writeheader()
        writer.writerows(filas)


def test_generador_deduplica_normaliza_ancla_y_agrega_sin_reescribir_prefijo(tmp_path):
    fixture = [
        {
            "model": "core.provincia",
            "pk": 1,
            "fields": {"nombre": "Córdoba"},
        },
        {
            "model": "core.municipio",
            "pk": 2,
            "fields": {"nombre": "Capital", "provincia": 1},
        },
        {
            "model": "core.localidad",
            "pk": 3,
            "fields": {"nombre": "Existente", "municipio": 2},
        },
    ]
    fixture_path = tmp_path / "territorio.json"
    original = json.dumps(fixture, ensure_ascii=False, indent=2)
    fixture_path.write_text(original, encoding="utf-8")

    asentamientos_path = tmp_path / "asentamientos.csv"
    _escribir_csv(
        asentamientos_path,
        [
            "categoria",
            "id",
            "nombre",
            "provincia_nombre",
            "municipio_nombre",
            "departamento_nombre",
        ],
        [
            {
                "categoria": "Paraje",
                "id": "1",
                "nombre": "Nueva",
                "provincia_nombre": "CORDOBA",
                "municipio_nombre": "capital",
                "departamento_nombre": "Capital",
            },
            {
                "categoria": "Entidad",
                "id": "2",
                "nombre": "NUEVA",
                "provincia_nombre": "Córdoba",
                "municipio_nombre": "Capital",
                "departamento_nombre": "Capital",
            },
            {
                "categoria": "Localidad simple",
                "id": "3",
                "nombre": "Anclada",
                "provincia_nombre": "Córdoba",
                "municipio_nombre": "",
                "departamento_nombre": "Capital",
            },
            {
                "categoria": "Paraje",
                "id": "4",
                "nombre": "Existente",
                "provincia_nombre": "Córdoba",
                "municipio_nombre": "",
                "departamento_nombre": "Departamento Nuevo",
            },
            {
                "categoria": "Localidad simple",
                "id": "5",
                "nombre": "Cruce",
                "provincia_nombre": "Córdoba",
                "municipio_nombre": "Municipio Vecino",
                "departamento_nombre": "Capital",
            },
        ],
    )
    municipios_path = tmp_path / "municipios.csv"
    _escribir_csv(
        municipios_path,
        ["nombre", "provincia_nombre"],
        [{"nombre": "Oficial", "provincia_nombre": "Córdoba"}],
    )

    resumen = bahra.actualizar_fixture(
        fixture_path, asentamientos_path, municipios_path
    )
    resultado = fixture_path.read_text(encoding="utf-8")
    datos = json.loads(resultado)

    assert resultado.startswith(original[:-2])
    assert not resultado.endswith("\n")
    assert resumen["municipios_oficiales_nuevos"] == 1
    assert resumen["pseudo_municipios_nuevos"] == 1
    assert resumen["municipio_cross_provincia_anclado_a_depto"] == 1
    assert resumen["descartes_dedup_interno"] == 1
    assert resumen["descartes_anclaje_anti_duplicado"] == 1
    assert resumen["localidades_Entidad"] == 1
    assert resumen["localidades_Localidad simple"] == 2
    assert all(entry["pk"] >= 100000 for entry in datos[3:])
    assert [entry["model"] for entry in datos[3:]] == [
        "core.municipio",
        "core.municipio",
        "core.localidad",
        "core.localidad",
        "core.localidad",
    ]
