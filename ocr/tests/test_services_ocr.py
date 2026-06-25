from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings

from ocr.services_ocr import extract_text_from_file


class ExtractTextFromFileTest(TestCase):
    @patch("ocr.services_ocr._extract_from_image")
    def test_routes_png_to_image_extractor(self, mock_img):
        mock_img.return_value = {
            "text": "Texto PNG",
            "page_count": None,
            "warning": None,
        }
        result = extract_text_from_file("/fake/img.png", "img.png")
        mock_img.assert_called_once()
        self.assertEqual(result["text"], "Texto PNG")
        self.assertIsNone(result["page_count"])

    @patch("ocr.services_ocr._extract_from_image")
    def test_routes_jpg_to_image_extractor(self, mock_img):
        mock_img.return_value = {
            "text": "Texto JPG",
            "page_count": None,
            "warning": None,
        }
        result = extract_text_from_file("/fake/scan.jpg", "scan.jpg")
        mock_img.assert_called_once()
        self.assertEqual(result["text"], "Texto JPG")

    @patch("ocr.services_ocr._extract_from_image")
    def test_routes_jpeg_to_image_extractor(self, mock_img):
        mock_img.return_value = {
            "text": "Texto JPEG",
            "page_count": None,
            "warning": None,
        }
        result = extract_text_from_file("/fake/scan.jpeg", "scan.jpeg")
        mock_img.assert_called_once()

    @patch("ocr.services_ocr._extract_from_pdf")
    def test_routes_pdf_to_pdf_extractor(self, mock_pdf):
        mock_pdf.return_value = {"text": "Texto PDF", "page_count": 3, "warning": None}
        result = extract_text_from_file("/fake/doc.pdf", "doc.pdf")
        mock_pdf.assert_called_once()
        self.assertEqual(result["text"], "Texto PDF")
        self.assertEqual(result["page_count"], 3)

    @patch("ocr.services_ocr._extract_from_image")
    def test_no_text_returns_warning(self, mock_img):
        mock_img.return_value = {
            "text": "",
            "page_count": None,
            "warning": "No se pudo extraer texto legible del archivo.",
        }
        result = extract_text_from_file("/fake/blank.png", "blank.png")
        self.assertEqual(result["text"], "")
        self.assertIsNotNone(result["warning"])
        self.assertIn("No se pudo extraer", result["warning"])

    def test_unsupported_extension_raises(self):
        with self.assertRaises(ValueError):
            extract_text_from_file("/fake/file.docx", "file.docx")

    def test_unsupported_extension_xls_raises(self):
        with self.assertRaises(ValueError):
            extract_text_from_file("/fake/file.xls", "file.xls")

    @patch("ocr.services_ocr._extract_from_pdf")
    def test_pdf_no_text_returns_warning(self, mock_pdf):
        mock_pdf.return_value = {
            "text": "",
            "page_count": 2,
            "warning": "No se pudo extraer texto legible del archivo.",
        }
        result = extract_text_from_file("/fake/scan.pdf", "scan.pdf")
        self.assertEqual(result["text"], "")
        self.assertEqual(result["page_count"], 2)
        self.assertIsNotNone(result["warning"])

    @patch("ocr.services_ocr._extract_from_image")
    @override_settings(OCR_LANGUAGE="eng")
    def test_uses_configured_language(self, mock_img):
        mock_img.return_value = {
            "text": "English text",
            "page_count": None,
            "warning": None,
        }
        extract_text_from_file("/fake/img.png", "img.png")
        _, kwargs = mock_img.call_args
        self.assertEqual(kwargs.get("language") or mock_img.call_args[0][1], "eng")

    @patch("ocr.services_ocr._extract_from_image")
    def test_explicit_language_overrides_settings(self, mock_img):
        mock_img.return_value = {"text": "text", "page_count": None, "warning": None}
        extract_text_from_file("/fake/img.png", "img.png", language="por")
        args, _ = mock_img.call_args
        self.assertEqual(args[1], "por")
