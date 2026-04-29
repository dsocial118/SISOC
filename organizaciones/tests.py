"""Tests for organizaciones."""

import json

from django.contrib.auth.models import User, Permission
from django.test import RequestFactory, TestCase, Client
from django.urls import reverse

from organizaciones.models import Organizacion, TipoEntidad
from organizaciones.views import OrganizacionDetailView
from organizaciones.forms import OrganizacionForm
from core.models import Provincia


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


class CuilDuplicadoFormTests(TestCase):
    """Tests del flujo de CUIL duplicado en OrganizacionForm."""

    CUIL = 20123456789

    def setUp(self):
        self.provincia = Provincia.objects.create(nombre="Buenos Aires")
        self.existente = Organizacion.objects.create(
            nombre="Org Existente", cuit=self.CUIL, provincia=self.provincia
        )

    def _form_data(self, extra=None):
        data = {
            "nombre": "Org Nueva",
            "cuit": str(self.CUIL),
            "fecha_vencimiento": "2030-01-01",
            "provincia": str(self.provincia.pk),
        }
        if extra:
            data.update(extra)
        return data

    def test_cuil_duplicado_sin_confirmacion_es_invalido(self):
        form = OrganizacionForm(data=self._form_data())
        self.assertFalse(form.is_valid())
        self.assertIn("cuit", form.errors)
        self.assertIn(
            "cuil_duplicado_sin_confirmar",
            [e.code for e in form.errors.as_data()["cuit"]],
        )

    def test_cuil_duplicado_con_confirmacion_es_valido(self):
        form = OrganizacionForm(
            data=self._form_data(
                {
                    "cuil_duplicado_confirmado": "true",
                    "cuil_duplicado_confirmado_valor": str(self.CUIL),
                }
            )
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_cuil_duplicado_rechaza_confirmacion_de_otro_cuil(self):
        form = OrganizacionForm(
            data=self._form_data(
                {
                    "cuil_duplicado_confirmado": "true",
                    "cuil_duplicado_confirmado_valor": "20999999990",
                }
            )
        )
        self.assertFalse(form.is_valid())
        self.assertIn("cuit", form.errors)
        self.assertIn(
            "cuil_duplicado_sin_confirmar",
            [e.code for e in form.errors.as_data()["cuit"]],
        )

    def test_cuil_unico_no_requiere_confirmacion(self):
        form = OrganizacionForm(data=self._form_data({"cuit": 20999999990}))
        self.assertTrue(form.is_valid(), form.errors)

    def test_edicion_propio_cuil_no_requiere_confirmacion(self):
        """Al editar una org, su propio CUIL no dispara la advertencia."""
        form = OrganizacionForm(data=self._form_data(), instance=self.existente)
        self.assertTrue(form.is_valid(), form.errors)

    def test_multiples_orgs_mismo_cuil_permitidas(self):
        """Verificar que la DB permite CUILs repetidos sin error de integridad."""
        Organizacion.objects.create(nombre="Org Duplicada", cuit=self.CUIL)
        self.assertEqual(Organizacion.objects.filter(cuit=self.CUIL).count(), 2)


class OrganizacionModelTests(TestCase):
    """Tests del contrato de persistencia de Organizacion."""

    def test_cuit_conserva_indice_no_unico_para_busquedas(self):
        field = Organizacion._meta.get_field("cuit")
        self.assertFalse(field.unique)
        self.assertTrue(field.db_index)


class CuilCheckAjaxTests(TestCase):
    """Tests del endpoint AJAX de verificación de CUIL."""

    CUIL = 20123456780

    def setUp(self):
        self.user = User.objects.create_user(username="tester2", password="secret")
        perm = Permission.objects.get(codename="view_organizacion")
        self.user.user_permissions.add(perm)
        self.client = Client()
        self.client.login(username="tester2", password="secret")
        self.org = Organizacion.objects.create(nombre="Org Ajax", cuit=self.CUIL)
        self.url = reverse("organizacion_cuil_check_ajax")

    def test_retorna_organizaciones_con_cuil_existente(self):
        response = self.client.get(self.url, {"cuil": str(self.CUIL)})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data["organizaciones"]), 1)
        self.assertEqual(data["organizaciones"][0]["nombre"], "Org Ajax")

    def test_retorna_vacio_con_cuil_inexistente(self):
        response = self.client.get(self.url, {"cuil": "20999999990"})
        data = json.loads(response.content)
        self.assertEqual(data["organizaciones"], [])

    def test_exclude_excluye_la_org_en_edicion(self):
        response = self.client.get(
            self.url, {"cuil": str(self.CUIL), "exclude": str(self.org.pk)}
        )
        data = json.loads(response.content)
        self.assertEqual(data["organizaciones"], [])

    def test_cuil_no_numerico_retorna_vacio(self):
        response = self.client.get(self.url, {"cuil": "abc"})
        data = json.loads(response.content)
        self.assertEqual(data["organizaciones"], [])
