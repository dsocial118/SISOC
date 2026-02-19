from django.test import SimpleTestCase
from django.urls import reverse

class CentroDeInfanciaUrlsSmokeTests(SimpleTestCase):
    def test_reverse_main_routes(self):
        self.assertEqual(reverse("centrodeinfancia"), "/centrodeinfancia/listar")
        self.assertEqual(reverse("centrodeinfancia_crear"), "/centrodeinfancia/crear")
        self.assertEqual(
            reverse("centrodeinfancia_detalle", kwargs={"pk": 1}),
            "/centrodeinfancia/detalle/1",
        )
