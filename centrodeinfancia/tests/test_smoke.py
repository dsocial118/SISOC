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
        self.assertEqual(
            reverse("centrodeinfancia_trabajador_crear", kwargs={"pk": 1}),
            "/centrodeinfancia/1/trabajadores/crear/",
        )
        self.assertEqual(
            reverse(
                "centrodeinfancia_trabajador_editar",
                kwargs={"pk": 1, "trabajador_id": 2},
            ),
            "/centrodeinfancia/1/trabajadores/2/editar/",
        )
        self.assertEqual(
            reverse(
                "centrodeinfancia_trabajador_eliminar",
                kwargs={"pk": 1, "trabajador_id": 2},
            ),
            "/centrodeinfancia/1/trabajadores/2/eliminar/",
        )
        self.assertEqual(
            reverse("centrodeinfancia_formulario_listado", kwargs={"pk": 1}),
            "/centrodeinfancia/1/formularios/",
        )
        self.assertEqual(
            reverse("centrodeinfancia_formulario_crear", kwargs={"pk": 1}),
            "/centrodeinfancia/1/formularios/crear/",
        )
        self.assertEqual(
            reverse(
                "centrodeinfancia_formulario_detalle",
                kwargs={"pk": 1, "form_pk": 2},
            ),
            "/centrodeinfancia/1/formularios/2/",
        )
