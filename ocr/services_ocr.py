from __future__ import annotations

import logging
from pathlib import Path

from django.conf import settings
from PIL import Image

logger = logging.getLogger("django")

_NO_TEXT_MESSAGE = "No se pudo extraer texto legible del archivo."


def _get_language() -> str:
    return getattr(settings, "OCR_LANGUAGE", "spa")


def _extract_from_image(file_path: str, language: str) -> dict:
    import pytesseract

    image = Image.open(file_path)
    text = pytesseract.image_to_string(image, lang=language)
    text = text.strip()
    return {
        "text": text,
        "page_count": None,
        "warning": _NO_TEXT_MESSAGE if not text else None,
    }


def _extract_from_pdf(file_path: str, language: str) -> dict:
    import pytesseract
    from pdf2image import convert_from_path

    pages = convert_from_path(file_path)
    page_count = len(pages)
    texts = []
    for page_image in pages:
        page_text = pytesseract.image_to_string(page_image, lang=language).strip()
        if page_text:
            texts.append(page_text)

    text = "\n\n".join(texts)
    return {
        "text": text,
        "page_count": page_count,
        "warning": _NO_TEXT_MESSAGE if not text else None,
    }


def extract_text_from_file(
    file_path: str,
    original_filename: str,
    language: str | None = None,
) -> dict:
    """
    Extrae texto de una imagen o PDF usando Tesseract OCR.

    Retorna dict con:
      - text: str — texto extraído (puede estar vacío)
      - page_count: int | None — páginas si es PDF, None si es imagen
      - warning: str | None — mensaje si no se extrajo texto legible
    """
    if language is None:
        language = _get_language()

    ext = Path(original_filename).suffix.lower()

    if ext == ".pdf":
        return _extract_from_pdf(file_path, language)
    elif ext in (".jpg", ".jpeg", ".png"):
        return _extract_from_image(file_path, language)
    else:
        raise ValueError(f"Tipo de archivo no soportado: '{ext}'")
