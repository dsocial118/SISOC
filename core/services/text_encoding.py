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


def _title_affected_tokens(text: str, positions: list[int]) -> str:
    result = text
    for position in positions:
        start = position
        while start > 0 and not result[start - 1].isspace():
            start -= 1

        end = position
        while end < len(result) and not result[end].isspace():
            end += 1

        result = f"{result[:start]}{result[start:end].title()}{result[end:]}"
    return result


def _repair_title_cased_once(text: str) -> tuple[str, bool]:
    """Invierte mojibake cuando hay evidencia del límite creado por title()."""

    repaired: list[str] = []
    affected_positions: list[int] = []
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
                category = unicodedata.category(decoded) if decoded else ""
                is_uppercase = category == "Lu"
                is_lowercase_with_title_boundary = (
                    category == "Ll"
                    and index > 0
                    and text[index - 1].isalpha()
                    and index + 2 < len(text)
                    and text[index + 2].isupper()
                )
                if is_uppercase or is_lowercase_with_title_boundary:
                    affected_positions.append(len(repaired))
                    repaired.append(decoded)
                    index += 2
                    changed = True
                    continue

        repaired.append(text[index])
        index += 1

    result = "".join(repaired)
    return _title_affected_tokens(result, affected_positions), changed


def _repair_stranded_title_boundary_once(text: str) -> tuple[str, bool]:
    """Corrige un segundo inicio de palabra dejado tras reparar el mojibake."""

    affected_positions = []
    for index, character in enumerate(text[:-2]):
        is_token_start = index == 0 or text[index - 1].isspace()
        is_latin1_uppercase = (
            0x00C0 <= ord(character) <= 0x00DE
            and unicodedata.category(character) == "Lu"
        )
        if (
            is_token_start
            and is_latin1_uppercase
            and text[index + 1].isupper()
            and text[index + 2].islower()
        ):
            affected_positions.append(index)

    return _title_affected_tokens(text, affected_positions), bool(affected_positions)


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
        current, stranded_title_changed = _repair_stranded_title_boundary_once(current)
        if not title_cased_changed and not changed and not stranded_title_changed:
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
