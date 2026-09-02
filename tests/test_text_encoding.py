import pytest

from core.services.text_encoding import (
    contains_mojibake_marker,
    repair_utf8_mojibake,
    repair_utf8_mojibake_values,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Jos\u00c3\u00a9", "José"),
        ("Mu\u00c3\u00b1oz", "Muñoz"),
        ("Dell \u00c3\u201clio", "Dell Ólio"),
        ("\u00c3\x81ngel", "Ángel"),
        ("O\u00e2\u20ac\u2122Connor", "O’Connor"),
        ("\u00f0\u0178\u02dc\u20ac", "😀"),
        ("Ángel Jos\u00c3\u00a9", "Ángel José"),
        ("Jos\u00c3\u0192\u00c2\u00a9", "José"),
        ("Dariel Lu\u00e3\u0081N", "Dariel Luán"),
    ],
)
def test_repair_utf8_mojibake_repara_secuencias_validas(raw, expected):
    assert repair_utf8_mojibake(raw) == expected


@pytest.mark.parametrize(
    "text",
    [
        "José Muñoz",
        "São Tomé",
        "João",
        "Donatto Simón",
        "Nombre \u00c3",
        "Texto con reemplazo \ufffd",
        "Texto ASCII",
    ],
)
def test_repair_utf8_mojibake_preserva_texto_no_reparable(text):
    assert repair_utf8_mojibake(text) == text


def test_repair_utf8_mojibake_es_idempotente():
    repaired = repair_utf8_mojibake("Ángel Jos\u00c3\u0192\u00c2\u00a9")

    assert repaired == "Ángel José"
    assert repair_utf8_mojibake(repaired) == repaired


def test_repair_utf8_mojibake_values_recorre_payload_sin_cambiar_claves():
    payload = {
        "apellido": "Mu\u00c3\u00b1oz",
        "domicilio": {"calle": "Pe\u00c3\u00b1a"},
        "otros": ["Jos\u00c3\u00a9", 3, None],
    }

    assert repair_utf8_mojibake_values(payload) == {
        "apellido": "Muñoz",
        "domicilio": {"calle": "Peña"},
        "otros": ["José", 3, None],
    }


def test_contains_mojibake_marker_detecta_casos_no_reparables():
    assert contains_mojibake_marker("Texto \ufffd") is True
    assert contains_mojibake_marker("Texto correcto") is False
