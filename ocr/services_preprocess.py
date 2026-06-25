from __future__ import annotations

import logging

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger("django")

# Lado mayor mínimo (px) por debajo del cual se reescala la imagen para
# acercarla a ~300 DPI efectivos y darle más detalle a Tesseract.
_MIN_LONG_SIDE = 1500

# Binarización adaptativa: tamaño de bloque (impar) y constante C. Un bloque
# grande (31) tolera mejor fondos grises y sellos que uno chico, sin fragmentar
# los caracteres. Valores elegidos empíricamente sobre documentos reales.
_ADAPTIVE_BLOCK_SIZE = 31
_ADAPTIVE_C = 10


def preprocess_for_ocr(pil_image: Image.Image) -> Image.Image:
    """
    Limpia una imagen PIL antes del OCR para mejorar la precisión en
    documentos "sucios" (fondos grises, sellos, ruido de digitalización).

    Pipeline (en orden):
      a. Conversión a escala de grises.
      b. Redimensionado si el lado mayor < 1500px (~300 DPI efectivos).
      c. Binarización adaptativa (Gaussian, bloque 31, C=10).

    Devuelve una nueva imagen PIL en modo "L". Ante cualquier error, registra
    el problema y devuelve la imagen original sin modificar.

    Nota: no se aplica corrección de inclinación (deskew). Se evaluó con
    `cv2.minAreaRect` sobre documentos reales y no mejoró el reconocimiento
    (incluso lo empeoró levemente), además de ser propenso a rotaciones
    catastróficas. Ver docs/ocr.md.
    """
    try:
        gray = cv2.cvtColor(np.array(pil_image.convert("RGB")), cv2.COLOR_RGB2GRAY)

        gray = _resize_if_small(gray)

        binary = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            _ADAPTIVE_BLOCK_SIZE,
            _ADAPTIVE_C,
        )

        return Image.fromarray(binary)
    except Exception:  # noqa: BLE001 — preprocesado best-effort, no debe romper el OCR
        logger.exception("Fallo el preprocesamiento OCR; se usa la imagen original")
        return pil_image


def _resize_if_small(gray: np.ndarray) -> np.ndarray:
    height, width = gray.shape[:2]
    long_side = max(height, width)
    if long_side >= _MIN_LONG_SIDE or long_side == 0:
        return gray

    scale = _MIN_LONG_SIDE / long_side
    new_size = (int(round(width * scale)), int(round(height * scale)))
    return cv2.resize(gray, new_size, interpolation=cv2.INTER_CUBIC)
