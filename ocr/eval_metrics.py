"""
Métricas para evaluar la calidad del OCR contra un texto de referencia.

La métrica principal es el *recall de palabras*: qué proporción de las palabras
del ground-truth aparecen en el texto extraído. Es robusta frente a diferencias
de orden, espaciado y puntuación, que no importan para juzgar si el OCR
"recuperó el contenido".

Solo usa la librería estándar para que sea testeable sin Tesseract.
"""
from __future__ import annotations

import re
import unicodedata
from collections import Counter

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def normalize_tokens(text: str, min_len: int = 3) -> list[str]:
    """Normaliza a tokens comparables: sin acentos, minúsculas, len >= min_len.

    Se descartan tokens muy cortos (artículos, preposiciones, ruido OCR) que
    aportan poco a la comparación de contenido.
    """
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return [t for t in _TOKEN_RE.findall(text.lower()) if len(t) >= min_len]


def word_recall(extracted: str, ground_truth: str, min_len: int = 3) -> dict:
    """Compara texto extraído vs ground-truth y devuelve métricas de cobertura.

    Retorna dict con:
      - recall: palabras del GT cubiertas por el OCR (lo más importante)
      - precision: palabras del OCR que están en el GT
      - f1: media armónica de ambas
      - matched / gt_total / extracted_total: conteos crudos (multiset)
    """
    gt = Counter(normalize_tokens(ground_truth, min_len))
    oc = Counter(normalize_tokens(extracted, min_len))

    gt_total = sum(gt.values())
    extracted_total = sum(oc.values())
    matched = sum((gt & oc).values())

    recall = matched / gt_total if gt_total else 0.0
    precision = matched / extracted_total if extracted_total else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    return {
        "recall": recall,
        "precision": precision,
        "f1": f1,
        "matched": matched,
        "gt_total": gt_total,
        "extracted_total": extracted_total,
    }
