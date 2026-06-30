from unittest.mock import patch

from django.test import TestCase, override_settings

from ocr.services_postprocess import correct_text


class FakeSpell:
    """Spell-checker determinista para tests (sin depender del diccionario real)."""

    def __init__(self, known=None, corrections=None):
        self.known = set(known or [])
        self.corrections = corrections or {}

    def __contains__(self, word):
        return word in self.known

    def correction(self, word):
        return self.corrections.get(word)


class CorrectTextTest(TestCase):
    def _patch_spell(self, **kw):
        return patch(
            "ocr.services_postprocess._get_spell_checker",
            return_value=FakeSpell(**kw),
        )

    @override_settings(OCR_SPELLCHECK=False)
    def test_disabled_returns_text_unchanged(self):
        self.assertEqual(correct_text("texto presrnte"), "texto presrnte")

    @override_settings(OCR_SPELLCHECK=True)
    def test_corrects_clear_typo(self):
        with self._patch_spell(corrections={"presrnte": "presente"}):
            self.assertEqual(correct_text("el presrnte acta"), "el presente acta")

    @override_settings(OCR_SPELLCHECK=True)
    def test_preserves_proper_nouns(self):
        # 'Fiorito' está capitalizada -> nombre propio, no se toca aunque haya
        # una "corrección" disponible.
        with self._patch_spell(corrections={"fiorito": "favorito"}):
            self.assertEqual(correct_text("en Fiorito vive"), "en Fiorito vive")

    @override_settings(OCR_SPELLCHECK=True)
    def test_preserves_valid_plural(self):
        # 'documentos' ausente del diccionario no debe degradarse a 'documento'.
        with self._patch_spell(corrections={"documentos": "documento"}):
            self.assertEqual(correct_text("los documentos"), "los documentos")

    @override_settings(OCR_SPELLCHECK=True)
    def test_preserves_known_word(self):
        with self._patch_spell(
            known={"asociacion"}, corrections={"asociacion": "otra"}
        ):
            self.assertEqual(correct_text("una asociacion"), "una asociacion")

    @override_settings(OCR_SPELLCHECK=True)
    def test_preserves_short_words(self):
        with self._patch_spell(corrections={"los": "las"}):
            self.assertEqual(correct_text("los"), "los")

    @override_settings(OCR_SPELLCHECK=True)
    def test_preserves_numbers_and_punctuation(self):
        with self._patch_spell():
            self.assertEqual(correct_text("DNI 18.352.181"), "DNI 18.352.181")

    @override_settings(OCR_SPELLCHECK=True)
    def test_rejects_large_edits(self):
        # Diferencia de longitud > 1 -> no se aplica (probable mala corrección).
        with self._patch_spell(corrections={"acto": "actividad"}):
            self.assertEqual(correct_text("un acto"), "un acto")

    @override_settings(OCR_SPELLCHECK=True)
    def test_best_effort_on_checker_failure(self):
        with patch(
            "ocr.services_postprocess._get_spell_checker",
            side_effect=RuntimeError("no dict"),
        ):
            self.assertEqual(correct_text("texto presrnte"), "texto presrnte")
