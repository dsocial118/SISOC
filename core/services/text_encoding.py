"""Reparación conservadora de texto UTF-8 interpretado como una página ANSI."""

from __future__ import annotations

import unicodedata
from typing import Any


MOJIBAKE_MARKERS = ("Ã", "Â", "â", "ð", "ï", "�")
DEFAULT_MAX_REPAIR_PASSES = 3
TITLE_CASED_UTF8_LEAD_BYTES = {"ã": 0xC3}


def _single_legacy_byte(character: str) -> int | None:
    """Devuelve el byte Windows-1252/Latin-1 representado por un carácter."""

    for encoding in ("cp1252", "latin-1"):
        try:
            encoded = character.encode(encoding)
        except UnicodeEncodeError:
            continue
        if len(encoded) == 1:
            return encoded[0]
    return None


def _utf8_sequence_length(first_byte: int) -> int | None:
    if 0xC2 <= first_byte <= 0xDF:
        return 2
    if 0xE0 <= first_byte <= 0xEF:
        return 3
    if 0xF0 <= first_byte <= 0xF4:
        return 4
    return None


def _repair_once(text: str) -> tuple[str, bool]:
    repaired: list[str] = []
    changed = False
    index = 0

    while index < len(text):
        first_byte = _single_legacy_byte(text[index])
        sequence_length = (
            _utf8_sequence_length(first_byte) if first_byte is not None else None
        )
        if sequence_length and index + sequence_length <= len(text):
            byte_values = [first_byte]
            for character in text[index + 1 : index + sequence_length]:
                byte_value = _single_legacy_byte(character)
                if byte_value is None:
                    break
                byte_values.append(byte_value)

            if len(byte_values) == sequence_length and all(
                0x80 <= byte_value <= 0xBF for byte_value in byte_values[1:]
            ):
                try:
                    decoded = bytes(byte_values).decode("utf-8", errors="strict")
                except UnicodeDecodeError:
                    decoded = ""
                if decoded:
                    repaired.append(decoded)
                    index += sequence_length
                    changed = True
                    continue

        repaired.append(text[index])
        index += 1

    return "".join(repaired), changed


def _repair_title_cased_once(text: str) -> tuple[str, bool]:
    """Invierte mojibake capitalizado sólo cuando reconstruye una letra mayúscula."""

    repaired: list[str] = []
    changed = False
    index = 0

    while index < len(text):
        first_byte = TITLE_CASED_UTF8_LEAD_BYTES.get(text[index])
        if first_byte is not None and index + 1 < len(text):
            continuation_byte = _single_legacy_byte(text[index + 1])
            if continuation_byte is not None and 0x80 <= continuation_byte <= 0xBF:
                try:
                    decoded = bytes((first_byte, continuation_byte)).decode(
                        "utf-8", errors="strict"
                    )
                except UnicodeDecodeError:
                    decoded = ""
                if decoded and unicodedata.category(decoded) == "Lu":
                    repaired.append(decoded)
                    index += 2
                    changed = True
                    continue

        repaired.append(text[index])
        index += 1

    result = "".join(repaired)
    return (result.title() if changed else result), changed


def repair_utf8_mojibake(
    text: str, *, max_passes: int = DEFAULT_MAX_REPAIR_PASSES
) -> str:
    """Repara sólo secuencias que reconstruyen bytes UTF-8 estrictamente válidos.

    El recorrido por secuencias evita recodificar la cadena completa, porque un
    mismo campo puede mezclar caracteres correctos y mojibake. Varias pasadas
    acotadas permiten reparar texto que fue recodificado más de una vez.
    """

    current = text
    for _ in range(max(0, max_passes)):
        current, title_cased_changed = _repair_title_cased_once(current)
        current, changed = _repair_once(current)
        if not title_cased_changed and not changed:
            break
    return current


def contains_mojibake_marker(text: str) -> bool:
    """Indica si quedan marcadores frecuentes, incluso si no son reparables."""

    return any(marker in text for marker in MOJIBAKE_MARKERS)


def repair_utf8_mojibake_values(value: Any) -> Any:
    """Repara recursivamente strings de un payload sin modificar sus claves."""

    if isinstance(value, str):
        return repair_utf8_mojibake(value)
    if isinstance(value, dict):
        return {
            key: repair_utf8_mojibake_values(item_value)
            for key, item_value in value.items()
        }
    if isinstance(value, list):
        return [repair_utf8_mojibake_values(item) for item in value]
    if isinstance(value, tuple):
        return tuple(repair_utf8_mojibake_values(item) for item in value)
    return value
