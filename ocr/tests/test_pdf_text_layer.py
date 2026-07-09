from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings

from ocr.services_ocr import _choose_page_text, _extract_from_pdf


class ChoosePageTextTest(TestCase):
    """Decision por pagina entre capa de texto embebida y OCR."""

    def _entry(self, text, big_image=False):
        return {"text": text, "has_big_image": big_image}

    @override_settings(OCR_PDF_TEXT_LAYER_MIN_WORDS=8)
    def test_born_digital_complete_uses_text_layer(self):
        emb = " ".join(f"palabra{i}" for i in range(20))
        ocr = "ruido ocr parcial"
        text, source = _choose_page_text(ocr, self._entry(emb))
        self.assertEqual(source, "text_layer")
        self.assertEqual(text, emb)

    @override_settings(OCR_PDF_TEXT_LAYER_MIN_WORDS=8)
    def test_partial_layer_falls_back_to_ocr(self):
        # Capa parcial (encabezado digital) sobre cuerpo escaneado: el OCR tiene
        # mas palabras -> guardrail anti-perdida usa OCR para no perder el cuerpo.
        emb = " ".join(f"encabezado{i}" for i in range(10))
        ocr = " ".join(f"cuerpo{i}" for i in range(40))
        text, source = _choose_page_text(ocr, self._entry(emb))
        self.assertEqual(source, "ocr")
        self.assertEqual(text, ocr)

    @override_settings(OCR_PDF_TEXT_LAYER_MIN_WORDS=8)
    def test_scanned_page_without_embedded_text_uses_ocr(self):
        ocr = " ".join(f"escaneo{i}" for i in range(30))
        text, source = _choose_page_text(ocr, self._entry(""))
        self.assertEqual(source, "ocr")
        self.assertEqual(text, ocr)

    @override_settings(OCR_PDF_TEXT_LAYER_MIN_WORDS=8)
    def test_big_image_forces_ocr_even_with_text(self):
        emb = " ".join(f"palabra{i}" for i in range(20))
        ocr = "ocr corto"
        text, source = _choose_page_text(ocr, self._entry(emb, big_image=True))
        self.assertEqual(source, "ocr")

    def test_no_layer_entry_uses_ocr(self):
        text, source = _choose_page_text("solo ocr", None)
        self.assertEqual(source, "ocr")
        self.assertEqual(text, "solo ocr")


class ExtractFromPdfHybridTest(TestCase):
    """_extract_from_pdf con el híbrido de capa de texto."""

    def _run(self, ocr_per_page, layer):
        with (
            patch("pdf2image.convert_from_path") as mock_convert,
            patch("pytesseract.image_to_string") as mock_ocr,
            patch(
                "ocr.services_ocr._maybe_preprocess", side_effect=lambda img, *a: img
            ),
            patch("ocr.services_ocr._read_text_layer", return_value=layer),
        ):
            mock_convert.return_value = [MagicMock() for _ in ocr_per_page]
            mock_ocr.side_effect = ocr_per_page
            return _extract_from_pdf("/fake/doc.pdf", "spa")

    @override_settings(OCR_PDF_TEXT_LAYER=True, OCR_PDF_TEXT_LAYER_MIN_WORDS=8)
    def test_guardrail_hybrid_never_fewer_words_than_ocr_only(self):
        # Caso construido: pagina A born-digital (capa mas rica que su OCR) +
        # pagina B escaneada (sin capa, OCR rico). El total hibrido nunca debe
        # tener menos palabras que el OCR-only.
        page_a_emb = " ".join(f"digital{i}" for i in range(20))
        page_a_ocr = "ocr pobre de pagina digital"  # 5 palabras
        page_b_ocr = " ".join(f"escaneo{i}" for i in range(30))
        layer = [
            {"text": page_a_emb, "has_big_image": False},
            {"text": "", "has_big_image": True},
        ]
        result = self._run([page_a_ocr, page_b_ocr], layer)

        hybrid_words = len(result["text"].split())
        ocr_only_words = len(page_a_ocr.split()) + len(page_b_ocr.split())
        self.assertGreaterEqual(hybrid_words, ocr_only_words)
        # La pagina A debe haber usado la capa digital (mas completa).
        self.assertIn("digital0", result["text"])
        # La pagina B (escaneo) debe venir del OCR.
        self.assertIn("escaneo0", result["text"])

    @override_settings(OCR_PDF_TEXT_LAYER=False)
    def test_disabled_skips_text_layer(self):
        with (
            patch("ocr.services_ocr._read_text_layer") as mock_layer,
            patch("pdf2image.convert_from_path") as mock_convert,
            patch("pytesseract.image_to_string") as mock_ocr,
            patch(
                "ocr.services_ocr._maybe_preprocess", side_effect=lambda img, *a: img
            ),
        ):
            mock_convert.return_value = [MagicMock()]
            mock_ocr.return_value = "texto ocr"
            result = _extract_from_pdf("/fake/doc.pdf", "spa")

        mock_layer.assert_not_called()
        self.assertEqual(result["text"], "texto ocr")
