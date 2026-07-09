from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings

from ocr.services_ocr import _maybe_auto_orient


class MaybeAutoOrientTest(TestCase):
    def _image(self):
        img = MagicMock(name="pil_image")
        img.rotate.return_value = MagicMock(name="rotated")
        return img

    @override_settings(OCR_AUTO_ORIENT=True)
    def test_rotates_when_osd_reports_rotation(self):
        img = self._image()
        osd = "Orientation in degrees: 90\nRotate: 90\nOrientation confidence: 5.0\n"
        with patch("pytesseract.image_to_osd", return_value=osd):
            result = _maybe_auto_orient(img)
        img.rotate.assert_called_once_with(-90, expand=True)
        self.assertIs(result, img.rotate.return_value)

    @override_settings(OCR_AUTO_ORIENT=True)
    def test_no_rotation_when_upright(self):
        img = self._image()
        with patch("pytesseract.image_to_osd", return_value="Rotate: 0\n"):
            result = _maybe_auto_orient(img)
        img.rotate.assert_not_called()
        self.assertIs(result, img)

    @override_settings(OCR_AUTO_ORIENT=False)
    def test_disabled_skips_osd(self):
        img = self._image()
        with patch("pytesseract.image_to_osd") as mock_osd:
            result = _maybe_auto_orient(img)
        mock_osd.assert_not_called()
        self.assertIs(result, img)

    @override_settings(OCR_AUTO_ORIENT=True)
    def test_best_effort_on_osd_failure(self):
        img = self._image()
        with patch(
            "pytesseract.image_to_osd", side_effect=RuntimeError("Too few characters")
        ):
            result = _maybe_auto_orient(img)
        img.rotate.assert_not_called()
        self.assertIs(result, img)

    @override_settings(OCR_AUTO_ORIENT=True)
    def test_rotates_270(self):
        img = self._image()
        with patch("pytesseract.image_to_osd", return_value="Rotate: 270\n"):
            _maybe_auto_orient(img)
        img.rotate.assert_called_once_with(-270, expand=True)
