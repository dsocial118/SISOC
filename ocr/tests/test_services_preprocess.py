from unittest.mock import MagicMock, patch

import numpy as np
from django.test import TestCase, override_settings
from PIL import Image


def _build_cv2_mock(array: np.ndarray) -> MagicMock:
    """cv2 mockeado que devuelve arrays reales para que el pipeline complete."""
    mock_cv2 = MagicMock()
    mock_cv2.cvtColor.return_value = array
    mock_cv2.resize.return_value = array
    mock_cv2.adaptiveThreshold.return_value = array
    return mock_cv2


class PreprocessForOcrTest(TestCase):
    def test_returns_pil_image(self):
        from ocr import services_preprocess

        gray = np.zeros((1600, 1600), dtype=np.uint8)
        src = Image.new("RGB", (10, 10))

        with patch.object(services_preprocess, "cv2", _build_cv2_mock(gray)):
            result = services_preprocess.preprocess_for_ocr(src)

        self.assertIsInstance(result, Image.Image)

    def test_calls_pipeline_steps(self):
        from ocr import services_preprocess

        gray = np.zeros((1600, 1600), dtype=np.uint8)
        src = Image.new("RGB", (10, 10))
        mock_cv2 = _build_cv2_mock(gray)

        with patch.object(services_preprocess, "cv2", mock_cv2):
            services_preprocess.preprocess_for_ocr(src)

        mock_cv2.cvtColor.assert_called_once()
        mock_cv2.adaptiveThreshold.assert_called_once()

    def test_no_deskew_or_morphology(self):
        # El deskew y la morfología se removieron tras medir que no mejoraban
        # el OCR (y el deskew lo degradaba). Garantiza que no reaparezcan.
        from ocr import services_preprocess

        gray = np.zeros((1600, 1600), dtype=np.uint8)
        src = Image.new("RGB", (10, 10))
        mock_cv2 = _build_cv2_mock(gray)

        with patch.object(services_preprocess, "cv2", mock_cv2):
            services_preprocess.preprocess_for_ocr(src)

        mock_cv2.morphologyEx.assert_not_called()
        mock_cv2.minAreaRect.assert_not_called()
        mock_cv2.warpAffine.assert_not_called()

    def test_resizes_small_image(self):
        from ocr import services_preprocess

        gray = np.zeros((800, 800), dtype=np.uint8)
        src = Image.new("RGB", (10, 10))
        mock_cv2 = _build_cv2_mock(gray)

        with patch.object(services_preprocess, "cv2", mock_cv2):
            services_preprocess.preprocess_for_ocr(src)

        mock_cv2.resize.assert_called_once()

    def test_skips_resize_for_large_image(self):
        from ocr import services_preprocess

        gray = np.zeros((1600, 1600), dtype=np.uint8)
        src = Image.new("RGB", (10, 10))
        mock_cv2 = _build_cv2_mock(gray)

        with patch.object(services_preprocess, "cv2", mock_cv2):
            services_preprocess.preprocess_for_ocr(src)

        mock_cv2.resize.assert_not_called()

    def test_returns_original_on_error(self):
        from ocr import services_preprocess

        src = Image.new("RGB", (10, 10))
        mock_cv2 = MagicMock()
        mock_cv2.cvtColor.side_effect = RuntimeError("boom")

        with patch.object(services_preprocess, "cv2", mock_cv2):
            result = services_preprocess.preprocess_for_ocr(src)

        self.assertIs(result, src)


class PreprocessIntegrationTest(TestCase):
    """pytesseract y convert_from_path se importan dentro de las funciones,
    por eso se parchean en su módulo de origen."""

    @override_settings(OCR_PREPROCESS=True)
    @patch("ocr.services_preprocess.preprocess_for_ocr")
    @patch("pytesseract.image_to_string")
    @patch("ocr.services_ocr.Image")
    def test_image_pipeline_calls_preprocess_when_enabled(
        self, mock_image, mock_image_to_string, mock_preprocess
    ):
        from ocr.services_ocr import _extract_from_image

        opened = MagicMock()
        mock_image.open.return_value = opened
        mock_preprocess.return_value = "processed"
        mock_image_to_string.return_value = "texto"

        _extract_from_image("/fake/img.png", "spa")

        mock_preprocess.assert_called_once_with(opened)
        mock_image_to_string.assert_called_once()
        args, kwargs = mock_image_to_string.call_args
        self.assertEqual(args[0], "processed")
        self.assertEqual(kwargs["lang"], "spa")

    @override_settings(OCR_PREPROCESS=False)
    @patch("ocr.services_preprocess.preprocess_for_ocr")
    @patch("pytesseract.image_to_string")
    @patch("ocr.services_ocr.Image")
    def test_image_pipeline_skips_preprocess_when_disabled(
        self, mock_image, mock_image_to_string, mock_preprocess
    ):
        from ocr.services_ocr import _extract_from_image

        opened = MagicMock()
        mock_image.open.return_value = opened
        mock_image_to_string.return_value = "texto"

        _extract_from_image("/fake/img.png", "spa")

        mock_preprocess.assert_not_called()
        mock_image_to_string.assert_called_once()
        args, kwargs = mock_image_to_string.call_args
        self.assertEqual(args[0], opened)
        self.assertEqual(kwargs["lang"], "spa")

    @override_settings(OCR_PREPROCESS=True)
    @patch("ocr.services_preprocess.preprocess_for_ocr")
    @patch("pytesseract.image_to_string")
    @patch("pdf2image.convert_from_path")
    def test_pdf_pipeline_preprocesses_each_page(
        self, mock_convert, mock_image_to_string, mock_preprocess
    ):
        from ocr.services_ocr import _extract_from_pdf

        page_a, page_b = MagicMock(), MagicMock()
        mock_convert.return_value = [page_a, page_b]
        mock_preprocess.side_effect = lambda img: img
        mock_image_to_string.return_value = "texto"

        _extract_from_pdf("/fake/doc.pdf", "spa")

        self.assertEqual(mock_preprocess.call_count, 2)
