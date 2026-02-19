"""Tests for tests."""

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase

from organizaciones.models import Organizacion, TipoEntidad
from organizaciones.views import OrganizacionDetailView


class OrganizacionDetailViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="tester", password="secret")

    def _get_context(self, organizacion: Organizacion):
        request = self.factory.get("/")
        request.user = self.user

        view = OrganizacionDetailView()
        view.setup(request)
        view.object = organizacion

        return view.get_context_data()

    def test_avales_flag_true_for_asociacion_de_hecho(self):
        tipo_entidad = TipoEntidad.objects.create(nombre="Asociación de hecho")
        organizacion = Organizacion.objects.create(
            nombre="Organizacion A", tipo_entidad=tipo_entidad
        )

        context = self._get_context(organizacion)

        self.assertTrue(context["avales"])
        self.assertEqual(context["tipo_entidad"], tipo_entidad)

    def test_avales_flag_false_without_tipo_entidad(self):
        organizacion = Organizacion.objects.create(nombre="Organizacion B")

        context = self._get_context(organizacion)

        self.assertFalse(context["avales"])
        self.assertIsNone(context["tipo_entidad"])

    def test_avales_flag_false_for_other_tipo_entidad(self):
        tipo_entidad = TipoEntidad.objects.create(nombre="Fundación")
        organizacion = Organizacion.objects.create(
            nombre="Organizacion C", tipo_entidad=tipo_entidad
        )

        context = self._get_context(organizacion)

        self.assertFalse(context["avales"])
        self.assertEqual(context["tipo_entidad"], tipo_entidad)
