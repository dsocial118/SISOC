"""Politica comun para exportaciones CSV compatibles con Excel."""

from collections.abc import Iterable, Iterator

from django.http import HttpResponse


CSV_CONTENT_TYPE = "text/csv; charset=utf-8"
UTF8_BOM = "\ufeff"
CSV_FORMULA_PREFIXES = ("=", "+", "-", "@")


def build_csv_response(filename: str) -> HttpResponse:
    """Crea una respuesta CSV UTF-8 con BOM y nombre de descarga."""
    response = HttpResponse(content_type=CSV_CONTENT_TYPE)
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.write(UTF8_BOM)
    return response


def neutralize_csv_formula(value):
    """Impide que una planilla interprete texto no confiable como una formula."""
    if isinstance(value, str) and value.startswith(CSV_FORMULA_PREFIXES):
        return f"'{value}"
    return value


def prepend_utf8_bom(rows: Iterable[str]) -> Iterator[str]:
    """Anteponer una sola marca BOM a una secuencia CSV en streaming."""
    yield UTF8_BOM
    yield from rows


def encode_csv_text(content: str) -> bytes:
    """Codifica un CSV de texto como UTF-8 con BOM."""
    return content.encode("utf-8-sig")
