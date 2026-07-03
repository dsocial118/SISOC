import numpy as np
from django.test import TestCase, override_settings

from ocr.services_preprocess import _maybe_remove_color_stamps


class RemoveColorStampsTest(TestCase):
    def _image_with_blue_and_black(self):
        # Imagen RGB: mitad superior azul (sello de color, alta saturación),
        # mitad inferior negra (texto, baja saturación).
        arr = np.zeros((10, 10, 3), dtype=np.uint8)
        arr[0:5, :] = (0, 0, 255)  # azul
        return arr

    @override_settings(OCR_REMOVE_COLOR_STAMPS=True, OCR_COLOR_SAT_THRESHOLD=90)
    def test_whitens_color_preserves_black(self):
        out = _maybe_remove_color_stamps(self._image_with_blue_and_black())
        # El azul (alta saturación) pasa a blanco.
        self.assertTrue((out[0, 0] == (255, 255, 255)).all())
        # El negro (texto) se preserva.
        self.assertTrue((out[9, 9] == (0, 0, 0)).all())

    @override_settings(OCR_REMOVE_COLOR_STAMPS=False)
    def test_disabled_returns_unchanged(self):
        arr = self._image_with_blue_and_black()
        out = _maybe_remove_color_stamps(arr)
        self.assertTrue((out == arr).all())

    @override_settings(OCR_REMOVE_COLOR_STAMPS=True, OCR_COLOR_SAT_THRESHOLD=90)
    def test_red_stamp_also_removed(self):
        arr = np.zeros((4, 4, 3), dtype=np.uint8)
        arr[:, :] = (255, 0, 0)  # rojo, alta saturación
        out = _maybe_remove_color_stamps(arr)
        self.assertTrue((out == 255).all())

    @override_settings(OCR_REMOVE_COLOR_STAMPS=True, OCR_COLOR_SAT_THRESHOLD=90)
    def test_gray_low_saturation_preserved(self):
        # Gris medio: baja saturación -> NO se toca (como el texto/sellos negros).
        arr = np.full((4, 4, 3), 128, dtype=np.uint8)
        out = _maybe_remove_color_stamps(arr)
        self.assertTrue((out == 128).all())
