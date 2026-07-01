from __future__ import annotations

import logging
import re

from django.conf import settings

logger = logging.getLogger("django")

# Vocabulario del dominio que NO debe "corregirse" (términos legales/registrales
# que suelen faltar en un diccionario de frecuencias genérico).
_DOMAIN_WORDS = [
    "artículo",
    "artículos",
    "comisión",
    "directiva",
    "personería",
    "estatuto",
    "estatutos",
    "asamblea",
    "asociación",
    "asociaciones",
    "asambleístas",
    "tesorero",
    "vicepresidente",
    "revisor",
    "vocal",
    "suplente",
    "titular",
    "constitutiva",
    "semovientes",
    "permutarlos",
    "enajenarlos",
    "hipotecarlos",
    "cartoneros",
    "recuperadores",
]

# Solo se tocan palabras alfabéticas en minúscula de longitud razonable. Las
# capitalizadas (nombres propios) y las de mayúsculas (siglas/encabezados) se
# preservan siempre.
_WORD_RE = re.compile(r"[a-záéíóúüñ]+", re.IGNORECASE)
_MIN_LEN = 4

_spell_cache: dict = {}


def _spell_language(language: str | None) -> str:
    """Mapea el código Tesseract (spa) al de pyspellchecker (es)."""
    lang = (language or getattr(settings, "OCR_LANGUAGE", "spa")).lower()
    return {"spa": "es", "eng": "en", "por": "pt"}.get(lang, lang)


def _get_spell_checker(lang: str):
    if lang in _spell_cache:
        return _spell_cache[lang]
    from spellchecker import SpellChecker

    # distance=1: solo correcciones a un edit de distancia (acentos, typos
    # simples). Reduce drásticamente el riesgo de "corregir" palabras válidas.
    spell = SpellChecker(language=lang, distance=1)
    spell.word_frequency.load_words(_DOMAIN_WORDS)
    _spell_cache[lang] = spell
    return spell


def _is_plural_flip(word: str, candidate: str) -> bool:
    """True si la 'corrección' solo agrega/quita un plural español (s/es).

    Evita destrozar plurales válidos ausentes del diccionario
    (p. ej. 'documentos' -> 'documento').
    """
    longer, shorter = (
        (word, candidate)
        if len(word) >= len(candidate)
        else (
            candidate,
            word,
        )
    )
    return longer in (shorter + "s", shorter + "es")


def _correct_word(word: str, spell) -> str:
    # ``word`` llega en minúscula; la preservación de nombres propios/siglas se
    # hace en _replace sobre la palabra original (antes de bajar a minúscula).
    if len(word) < _MIN_LEN:
        return word
    if word in spell:  # ya es una palabra conocida
        return word

    candidate = spell.correction(word)
    if not candidate or candidate == word:
        return word
    if abs(len(candidate) - len(word)) > 1:
        return word
    if _is_plural_flip(word, candidate):
        return word
    return candidate


def correct_text(text: str, language: str | None = None) -> str:
    """Corrección ortográfica local (offline) y *conservadora* del texto OCR.

    Solo corrige tokens claramente fuera de diccionario, a un edit de distancia,
    preservando mayúsculas/acentos/números, nombres propios y plurales válidos.
    Es best-effort: ante cualquier error devuelve el texto sin modificar.

    No hace nada si ``OCR_SPELLCHECK`` está desactivado (default).
    """
    if not text or not getattr(settings, "OCR_SPELLCHECK", False):
        return text

    try:
        spell = _get_spell_checker(_spell_language(language))
    except Exception:  # noqa: BLE001 — dependencia opcional / carga de diccionario
        logger.warning("Spellcheck no disponible; se devuelve el texto sin corregir")
        return text

    def _replace(match: re.Match) -> str:
        word = match.group(0)
        # Preservar nombres propios (Capitalizados) y siglas/encabezados (MAYÚS):
        # solo se tocan palabras enteramente en minúscula.
        if word != word.lower():
            return word
        try:
            corrected = _correct_word(word, spell)
            return corrected if corrected != word else word
        except Exception:  # noqa: BLE001 — nunca romper por un token
            return word

    try:
        return _WORD_RE.sub(_replace, text)
    except Exception:  # noqa: BLE001
        logger.exception("Fallo la corrección ortográfica; se usa el texto crudo")
        return text
