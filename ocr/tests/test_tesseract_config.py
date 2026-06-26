from unittest.mock import patch

from django.test import TestCase, override_settings

from ocr.services_ocr import _tesseract_config


class TesseractConfigTest(TestCase):
    @override_settings(OCR_TESSDATA_DIR="")
    def test_empty_when_no_tessdata_dir(self):
        self.assertEqual(_tesseract_config("spa"), "")

    @override_settings(OCR_TESSDATA_DIR="/opt/tessdata-best")
    def test_adds_tessdata_dir_when_model_present(self):
        with patch("ocr.services_ocr.os.path.isfile", return_value=True):
            config = _tesseract_config("spa")
        self.assertIn("--tessdata-dir", config)
        self.assertIn("/opt/tessdata-best", config)

    @override_settings(OCR_TESSDATA_DIR="/opt/tessdata-best")
    def test_falls_back_when_model_missing(self):
        # Dir configurado pero sin el modelo del idioma -> se omite la flag y
        # Tesseract usa el tessdata del sistema (fallback seguro).
        with patch("ocr.services_ocr.os.path.isfile", return_value=False):
            config = _tesseract_config("spa")
        self.assertEqual(config, "")

    @override_settings(OCR_TESSDATA_DIR="/opt/tessdata-best")
    def test_checks_first_language_of_combo(self):
        with patch("ocr.services_ocr.os.path.isfile", return_value=True) as isfile:
            _tesseract_config("spa+eng")
        called_path = isfile.call_args[0][0]
        self.assertTrue(called_path.endswith("spa.traineddata"))

    @override_settings(OCR_TESSDATA_DIR="", OCR_TESSERACT_PSM=-1, OCR_TESSERACT_OEM=-1)
    def test_no_psm_oem_flags_by_default(self):
        config = _tesseract_config("spa")
        self.assertNotIn("--psm", config)
        self.assertNotIn("--oem", config)

    @override_settings(OCR_TESSDATA_DIR="", OCR_TESSERACT_PSM=6)
    def test_adds_psm_flag(self):
        self.assertIn("--psm 6", _tesseract_config("spa"))

    @override_settings(OCR_TESSDATA_DIR="", OCR_TESSERACT_OEM=1)
    def test_adds_oem_flag(self):
        self.assertIn("--oem 1", _tesseract_config("spa"))
