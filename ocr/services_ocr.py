from __future__ import annotations

import logging
import os
import re
from pathlib import Path

from django.conf import settings
from PIL import Image

logger = logging.getLogger("django")

_NO_TEXT_MESSAGE = "No se pudo extraer texto legible del archivo."


def _get_language() -> str:
    return getattr(settings, "OCR_LANGUAGE", "spa")


def _tesseract_config(language: str) -> str:
    """Arma el string de configuracion (flags) para pytesseract.

    Incluye ``--tessdata-dir`` solo si ``OCR_TESSDATA_DIR`` apunta a un
    directorio que realmente contiene el modelo del idioma pedido; de lo
    contrario se omite y Tesseract usa el tessdata del sistema (fallback
    seguro, sin romper si el modelo no esta presente).
    """
    parts: list[str] = []

    tessdata_dir = getattr(settings, "OCR_TESSDATA_DIR", "") or ""
    if tessdata_dir:
        first_lang = language.split("+")[0]
        model = os.path.join(tessdata_dir, f"{first_lang}.traineddata")
        if os.path.isfile(model):
            parts.append(f'--tessdata-dir "{tessdata_dir}"')
        else:
            logger.warning(
                "OCR_TESSDATA_DIR=%s no tiene %s.traineddata; uso tessdata del sistema",
                tessdata_dir,
                first_lang,
            )

    # --oem / --psm: valores < 0 omiten la flag (se usa el default de Tesseract).
    oem = getattr(settings, "OCR_TESSERACT_OEM", -1)
    if isinstance(oem, int) and oem >= 0:
        parts.append(f"--oem {oem}")

    psm = getattr(settings, "OCR_TESSERACT_PSM", -1)
    if isinstance(psm, int) and psm >= 0:
        parts.append(f"--psm {psm}")

    return " ".join(parts)


#: Opciones de calidad ajustables por lote (toggles de la UI). Cada una puede
#: sobreescribir el setting global; si no se pasa, se usa el setting.
_OPTION_SETTINGS = {
    "preprocess": ("OCR_PREPROCESS", True),
    "pdf_text_layer": ("OCR_PDF_TEXT_LAYER", True),
    "auto_orient": ("OCR_AUTO_ORIENT", True),
}


def _resolve_options(options: dict | None) -> dict:
    """Combina overrides por-lote con los settings globales (override gana)."""
    options = options or {}
    resolved = {}
    for key, (setting_name, default) in _OPTION_SETTINGS.items():
        if key in options and options[key] is not None:
            resolved[key] = options[key]
        else:
            resolved[key] = getattr(settings, setting_name, default)
    return resolved


def _maybe_preprocess(image: Image.Image, enabled: bool | None = None) -> Image.Image:
    if enabled is None:
        enabled = getattr(settings, "OCR_PREPROCESS", True)
    if not enabled:
        return image
    from ocr.services_preprocess import preprocess_for_ocr

    return preprocess_for_ocr(image)


def _maybe_auto_orient(image: Image.Image, enabled: bool | None = None) -> Image.Image:
    """Corrige la orientación de la imagen usando el OSD de Tesseract.

    Detecta rotaciones de 90/180/270° y rota la imagen para dejarla derecha.
    Best-effort: si el OSD falla (poco texto, sin confianza, error), se devuelve
    la imagen sin rotar. Se ejecuta sobre la imagen original (no binarizada),
    que es donde el OSD funciona mejor.
    """
    if enabled is None:
        enabled = getattr(settings, "OCR_AUTO_ORIENT", True)
    if not enabled:
        return image

    import pytesseract

    try:
        osd = pytesseract.image_to_osd(image)
        match = re.search(r"Rotate:\s*(\d+)", osd)
        rotate = int(match.group(1)) if match else 0
        if rotate % 360:
            # OSD informa los grados a rotar en sentido horario; PIL rota en
            # sentido antihorario, de ahí el signo negativo.
            return image.rotate(-rotate, expand=True)
    except Exception:  # noqa: BLE001 — OSD best-effort, no debe romper el OCR
        logger.warning("OSD no pudo determinar la orientación; se usa sin rotar")
    return image


def _extract_from_image(
    file_path: str, language: str, opts: dict | None = None
) -> dict:
    import pytesseract

    opts = opts or _resolve_options(None)
    image = Image.open(file_path)
    image = _maybe_auto_orient(image, opts["auto_orient"])
    image = _maybe_preprocess(image, opts["preprocess"])
    text = pytesseract.image_to_string(
        image, lang=language, config=_tesseract_config(language)
    )
    text = text.strip()
    return {
        "text": text,
        "page_count": None,
        "warning": _NO_TEXT_MESSAGE if not text else None,
    }


def _page_has_big_image(page) -> bool:
    """True si la pagina tiene un raster de tamano-pagina (indicio de escaneo).

    Lee las dimensiones del XObject de imagen sin decodificarlo (barato). Ante
    cualquier duda devuelve True: preferimos OCR antes que descartar contenido.
    """
    max_side = getattr(settings, "OCR_PDF_TEXT_LAYER_IMG_MAXSIDE", 1000)
    try:
        resources = page.get("/Resources")
        xobjects = resources.get("/XObject") if resources else None
        if not xobjects:
            return False
        for name in xobjects:
            obj = xobjects[name].get_object()
            if obj.get("/Subtype") == "/Image":
                if (
                    max(int(obj.get("/Width", 0)), int(obj.get("/Height", 0)))
                    >= max_side
                ):
                    return True
    except Exception:  # noqa: BLE001 — deteccion best-effort
        return True
    return False


def _read_text_layer(file_path: str) -> list[dict] | None:
    """Lee la capa de texto embebida por pagina (best-effort, con pypdf).

    Devuelve una lista (una entrada por pagina) con ``text`` y ``has_big_image``.
    Ante cualquier error devuelve None y el caller cae a OCR puro.
    """
    try:
        from pypdf import PdfReader

        reader = PdfReader(file_path)
        layer = []
        for page in reader.pages:
            text = (page.extract_text() or "").strip()
            layer.append({"text": text, "has_big_image": _page_has_big_image(page)})
        return layer
    except Exception:  # noqa: BLE001 — capa de texto best-effort, no debe romper el OCR
        logger.exception("No se pudo leer la capa de texto del PDF; se usa OCR puro")
        return None


def _choose_page_text(ocr_text: str, layer_entry: dict | None) -> tuple[str, str]:
    """Decide, para una pagina, entre texto embebido y OCR.

    Usa la capa embebida SOLO si la pagina es born-digital (texto sustancial y
    sin raster de tamano-pagina) y ademas no tiene menos palabras que el OCR
    (guardrail anti-perdida: una capa parcial perderia el cuerpo escaneado).

    Retorna (texto_elegido, fuente) donde fuente es "text_layer" u "ocr".
    """
    if not layer_entry:
        return ocr_text, "ocr"

    min_words = getattr(settings, "OCR_PDF_TEXT_LAYER_MIN_WORDS", 8)
    emb = layer_entry["text"]
    emb_words = len(emb.split())
    ocr_words = len(ocr_text.split())

    born_digital = emb_words >= min_words and not layer_entry["has_big_image"]
    if born_digital and emb_words >= ocr_words:
        return emb, "text_layer"
    return ocr_text, "ocr"


def _ocr_pdf_pages(pages: list, language: str, opts: dict, layer: list | None):
    """Procesa cada pagina del PDF y acumula texto y metricas de palabras.

    Devuelve ``(texts, hybrid_words, ocr_only_words, layer_pages)``:
      - texts: lista de textos por pagina (solo las no vacias)
      - hybrid_words: palabras del resultado hibrido (capa de texto + OCR)
      - ocr_only_words: palabras si solo se usara OCR (para el guardrail)
      - layer_pages: cantidad de paginas resueltas por capa de texto
    """
    import pytesseract

    texts = []
    hybrid_words = 0  # palabras del resultado hibrido
    ocr_only_words = 0  # palabras si solo se usara OCR
    layer_pages = 0
    for i, page_image in enumerate(pages):
        page_image = _maybe_auto_orient(page_image, opts["auto_orient"])
        page_image = _maybe_preprocess(page_image, opts["preprocess"])
        ocr_text = pytesseract.image_to_string(
            page_image, lang=language, config=_tesseract_config(language)
        ).strip()
        layer_entry = layer[i] if layer and i < len(layer) else None
        page_text, source = _choose_page_text(ocr_text, layer_entry)

        ocr_only_words += len(ocr_text.split())
        hybrid_words += len(page_text.split())
        if source == "text_layer":
            layer_pages += 1
        if page_text:
            texts.append(page_text)

    return texts, hybrid_words, ocr_only_words, layer_pages


def _extract_from_pdf(file_path: str, language: str, opts: dict | None = None) -> dict:
    from pdf2image import convert_from_path

    opts = opts or _resolve_options(None)
    pages = convert_from_path(file_path, dpi=300)
    page_count = len(pages)

    layer = _read_text_layer(file_path) if opts["pdf_text_layer"] else None

    texts, hybrid_words, ocr_only_words, layer_pages = _ocr_pdf_pages(
        pages, language, opts, layer
    )

    if layer is not None:
        # Guardrail medible: el hibrido nunca debe perder palabras frente al OCR
        # solo. Se loguea para auditar el comportamiento sobre datos reales.
        logger.info(
            "OCR PDF hibrido: %d/%d paginas por capa de texto; "
            "palabras hibrido=%d ocr_only=%d",
            layer_pages,
            page_count,
            hybrid_words,
            ocr_only_words,
        )
        if hybrid_words < ocr_only_words:
            logger.warning(
                "OCR PDF hibrido perdio palabras (%d < %d); revisar heuristica",
                hybrid_words,
                ocr_only_words,
            )

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
    options: dict | None = None,
) -> dict:
    """
    Extrae texto de una imagen o PDF usando Tesseract OCR.

    ``options`` (opcional) permite sobreescribir por lote las opciones de
    calidad ``preprocess``, ``pdf_text_layer`` y ``auto_orient``; si no se pasa
    (o una clave falta), se usa el setting global correspondiente.

    Retorna dict con:
      - text: str — texto extraído (puede estar vacío)
      - page_count: int | None — páginas si es PDF, None si es imagen
      - warning: str | None — mensaje si no se extrajo texto legible
    """
    if language is None:
        language = _get_language()

    opts = _resolve_options(options)
    ext = Path(original_filename).suffix.lower()

    if ext == ".pdf":
        result = _extract_from_pdf(file_path, language, opts)
    elif ext in (".jpg", ".jpeg", ".png"):
        result = _extract_from_image(file_path, language, opts)
    else:
        raise ValueError(f"Tipo de archivo no soportado: '{ext}'")

    return _maybe_spellcheck(result, language)


def _maybe_spellcheck(result: dict, language: str) -> dict:
    """Aplica corrección ortográfica al texto si OCR_SPELLCHECK está activo.

    Conserva el texto crudo en ``raw_text``. Best-effort: ante error devuelve el
    resultado sin tocar.
    """
    if not getattr(settings, "OCR_SPELLCHECK", False) or not result.get("text"):
        return result
    from ocr.services_postprocess import correct_text

    raw = result["text"]
    corrected = correct_text(raw, language)
    if corrected != raw:
        result["raw_text"] = raw
        result["text"] = corrected
    return result
