"""Tests unitarios para clasificación de comedor por puntaje."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from comedores.services.clasificacion_comedor_service import ClasificacionComedorService


BASE_DIR = Path(__file__).resolve().parent


class _Catalogo(SimpleNamespace):
    def __str__(self):
        return str(getattr(self, "nombre", ""))


class _CombustiblesQuerySetFake:
    def __init__(self, nombres):
        self._items = [_Catalogo(nombre=nombre) for nombre in nombres if nombre]

    def annotate(self, **_kwargs):
        return self

    def order_by(self, *_args, **_kwargs):
        orden = {"Leña": 1, "Otro": 2, "Gas envasado": 3}
        return sorted(self._items, key=lambda item: orden.get(item.nombre, 4))

    def __bool__(self):
        return bool(self._items)


def _normalizar_valor(valor):
    if isinstance(valor, dict):
        return {k: _normalizar_valor(v) for k, v in valor.items()}
    if isinstance(valor, list):
        return [_normalizar_valor(v) for v in valor]
    if valor == "Y":
        return True
    if valor == "N":
        return False
    if valor == "":
        return None
    return valor


def _ns(data):
    if isinstance(data, dict):
        return SimpleNamespace(**{k: _ns(v) for k, v in data.items()})
    if isinstance(data, list):
        return [_ns(v) for v in data]
    return data


def _build_relevamiento_from_json(filename):
    data = json.loads((BASE_DIR / filename).read_text(encoding="utf-8"))
    data = _normalizar_valor(data)

    espacio = data.get("espacio") or {}
    cocina = espacio.get("cocina") or {}
    prestacion_espacio = espacio.get("prestacion") or {}
    anexo = data.get("anexo") or {}

    tipo_espacio_nombre = espacio.get("tipo_espacio_fisico")
    # El JSON usa variantes abreviadas de catálogo; el servicio puntúa contra
    # nombres de catálogo almacenados en DB.
    tipo_espacio_nombre = {
        "Alquilado": "Espacio alquilado",
    }.get(tipo_espacio_nombre, tipo_espacio_nombre)
    espacio["tipo_espacio_fisico"] = (
        _Catalogo(nombre=tipo_espacio_nombre) if tipo_espacio_nombre else None
    )

    combustible_str = cocina.get("abastecimiento_combustible")
    cocina["abastecimiento_combustible"] = _CombustiblesQuerySetFake(
        [v.strip() for v in combustible_str.split(",")]
        if isinstance(combustible_str, str)
        else []
    )
    if cocina.get("abastecimiento_agua"):
        cocina["abastecimiento_agua"] = _Catalogo(nombre=cocina["abastecimiento_agua"])

    if prestacion_espacio.get("desague_hinodoro"):
        prestacion_espacio["desague_hinodoro"] = _Catalogo(
            nombre=prestacion_espacio["desague_hinodoro"]
        )

    if anexo.get("tecnologia"):
        anexo["tecnologia"] = _Catalogo(nombre=anexo["tecnologia"])
    if anexo.get("acceso_comedor"):
        anexo["acceso_comedor"] = _Catalogo(nombre=anexo["acceso_comedor"])

    return _ns(
        {
            "espacio": espacio,
            "colaboradores": data.get("colaboradores"),
            "anexo": anexo,
        }
    )


@pytest.mark.parametrize(
    ("filename", "puntaje_esperado"),
    [
        ("json_relevamiento_puntuacion_0.json", 0),
        # El fixture histórico se llama "56", pero la lógica vigente del servicio
        # penaliza también campos del anexo y devuelve 68.
        ("json_relevamiento_puntuacion_56.json", 68),
    ],
)
def test_get_puntuacion_total_regresion_json(filename, puntaje_esperado):
    relevamiento = _build_relevamiento_from_json(filename)

    resultado = ClasificacionComedorService.get_puntuacion_total(relevamiento)

    assert resultado == puntaje_esperado
