"""Tests for test favorite filters unit."""

from core.services.favorite_filters import (
    ConfiguracionFiltrosSeccion,
    SeccionesFiltrosFavoritos,
    clave_cache_filtros_favoritos,
    normalizar_carga,
    obtener_configuracion_seccion,
    obtener_items_obsoletos,
)


def test_clave_cache_filtros_favoritos():
    assert (
        clave_cache_filtros_favoritos(7, "comedores") == "filtros_favoritos_7_comedores"
    )


def test_obtener_configuracion_seccion_exists_and_missing():
    assert (
        obtener_configuracion_seccion(SeccionesFiltrosFavoritos.COMEDORES) is not None
    )
    assert obtener_configuracion_seccion("seccion_inexistente") is None


def test_normalizar_carga_none_and_invalid_inputs():
    assert normalizar_carga(None) is None
    assert normalizar_carga('{"invalid_json"') is None
    assert normalizar_carga(123) is None
    assert normalizar_carga({"items": "not-list"}) is None


def test_normalizar_carga_defaults_and_logic_normalization():
    assert normalizar_carga({}) == {"logic": "AND", "items": []}
    assert normalizar_carga({"logic": "or", "items": []}) == {
        "logic": "OR",
        "items": [],
    }
    assert normalizar_carga({"logic": "xor", "items": []}) == {
        "logic": "AND",
        "items": [],
    }
    assert normalizar_carga('{"logic": "and", "items": [{"field": "a"}]}') == {
        "logic": "AND",
        "items": [{"field": "a"}],
    }


def test_obtener_items_obsoletos_with_invalid_element_container():
    config = ConfiguracionFiltrosSeccion(
        tipos_campos={"nombre": "text"},
        operadores_permitidos={"text": ["contains", "empty"]},
    )

    assert obtener_items_obsoletos({"items": "bad"}, config) == [
        {"motivo": "elementos"}
    ]


def test_obtener_items_obsoletos_marks_all_invalid_cases():
    config = ConfiguracionFiltrosSeccion(
        tipos_campos={"nombre": "text", "edad": "number"},
        operadores_permitidos={"text": ["contains", "empty"], "number": ["gte"]},
    )
    payload = {
        "items": [
            "not-a-mapping",
            {"op": "contains", "value": "x"},
            {"field": "invalido", "op": "contains", "value": "x"},
            {"field": "nombre", "value": "x"},
            {"field": "nombre", "op": "gte", "value": "x"},
            {"field": "edad", "op": "gte", "value": ""},
            {"field": "nombre", "op": "empty"},
        ]
    }

    assert obtener_items_obsoletos(payload, config) == [
        {"indice": 0, "motivo": "elemento"},
        {"indice": 1, "motivo": "campo"},
        {"indice": 2, "motivo": "campo"},
        {"indice": 3, "motivo": "operador"},
        {"indice": 4, "motivo": "operador"},
        {"indice": 5, "motivo": "valor"},
    ]


def test_obtener_items_obsoletos_keeps_valid_items():
    config = ConfiguracionFiltrosSeccion(
        tipos_campos={"nombre": "text", "edad": "number"},
        operadores_permitidos={"text": ["contains", "empty"], "number": ["gte"]},
    )
    payload = {
        "items": [
            {"field": "nombre", "op": "contains", "value": "juan"},
            {"field": "nombre", "op": "empty"},
            {"field": "edad", "op": "gte", "value": 18},
        ]
    }

    assert obtener_items_obsoletos(payload, config) == []
