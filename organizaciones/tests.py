"""Tests for organizaciones."""

import json
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth.models import User, Permission
from django.test import RequestFactory, TestCase, Client
from django.urls import reverse
from django.utils import timezone

from comedores.models import Comedor, Programas, TipoDeComedor
from core.models import Provincia
from organizaciones.models import Organizacion, ProyectoOrganizacion, TipoEntidad
from organizaciones.forms import OrganizacionForm
from organizaciones.views import OrganizacionDetailView
from rendicioncuentasmensual.models import RendicionCuentaMensual


class CuilDuplicadoTemplateTests(TestCase):
    def test_verificacion_inicial_usa_secuencia_para_evitar_respuestas_viejas(self):
        template = Path("organizaciones/templates/organizacion_form.html").read_text(
            encoding="utf-8"
        )

        self.assertIn("var initialSeq = requestSeq;", template)
        self.assertIn("fetchCuilCheck(initialVal, initialSeq);", template)


class ProyectosOrganizacionAjaxTests(TestCase):
    def test_formulario_escucha_cambios_de_select2_con_jquery(self):
        template = Path("comedores/templates/comedor/comedor_form.html").read_text(
            encoding="utf-8"
        )

        self.assertIn(
            '$(organizacionInput).on("change", actualizarProyectos);', template
        )

    def test_usuario_que_puede_crear_comedor_carga_proyectos_en_primer_intento(self):
        user = User.objects.create_user(username="creador-comedor", password="secret")
        user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="comedores",
                codename="add_comedor",
            )
        )
        organizacion = Organizacion.objects.create(nombre="OrganizaciÃ³n con proyectos")
        proyecto = ProyectoOrganizacion.objects.create(
            organizacion=organizacion,
            codigo="P-1961",
        )
        ProyectoOrganizacion.objects.create(
            organizacion=organizacion,
            codigo="INACTIVO",
            activo=False,
        )
        self.client.force_login(user)

        with patch(
            "organizaciones.views._filtrar_organizaciones_por_dupla",
            side_effect=lambda queryset, _user: queryset,
        ):
            response = self.client.get(
                reverse(
                    "organizacion_proyectos_ajax",
                    kwargs={"organizacion_id": organizacion.pk},
                )
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"proyectos": [{"id": proyecto.id, "codigo": "P-1961", "nombre": None}]},
        )


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

    def test_detalle_muestra_programas_de_comedores_y_fallback(self):
        """El tab de comedores muestra el catálogo y conserva los sin programa."""
        user = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="secret"
        )
        organizacion = Organizacion.objects.create(nombre="Organización Programa")
        programas = [
            Programas.objects.create(nombre="Alimentar comunidad"),
            Programas.objects.create(nombre="Abordaje comunitario - Línea Secos"),
            Programas.objects.create(nombre="Abordaje comunitario - Línea Tradicional"),
        ]
        for index, programa in enumerate(programas, start=1):
            Comedor.objects.create(
                nombre=f"Comedor con programa {index}",
                organizacion=organizacion,
                programa=programa,
            )
        tipo_comedor = TipoDeComedor.objects.create(nombre="Comunitario")
        Comedor.objects.create(
            nombre="Comedor histórico sin programa",
            organizacion=organizacion,
            tipocomedor=tipo_comedor,
        )

        self.client.force_login(user)
        response = self.client.get(
            reverse("organizacion_detalle", kwargs={"pk": organizacion.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<th>Programa</th>", html=True)
        for programa in programas:
            self.assertContains(response, programa.nombre)
        self.assertRegex(
            response.content.decode(),
            r"(?s)Comedor histórico sin programa.*?<td>Comunitario</td>\s*<td>-</td>",
        )


class OrganizacionRendicionesPresentadasTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            username="admin-rendiciones",
            email="admin-rendiciones@example.com",
            password="secret",
        )
        self.client.force_login(self.user)
        self.organizacion = Organizacion.objects.create(nombre="Organización PNUD")
        self.comedor_p01 = Comedor.objects.create(
            nombre="Comedor P01",
            organizacion=self.organizacion,
            codigo_de_proyecto="P01",
        )
        self.comedor_p02 = Comedor.objects.create(
            nombre="Comedor P02",
            organizacion=self.organizacion,
            codigo_de_proyecto="P02",
        )
        self.rendicion_p01 = RendicionCuentaMensual.objects.create(
            comedor=self.comedor_p01,
            mes=6,
            anio=2026,
            convenio="CONV-01",
            numero_rendicion=1,
            monto_rendido="3000000.00",
            fecha_validacion_territorial=timezone.now(),
        )
        self.rendicion_p02 = RendicionCuentaMensual.objects.create(
            comedor=self.comedor_p02,
            mes=7,
            anio=2026,
            convenio="CONV-02",
            numero_rendicion=2,
        )

    def test_legajo_muestra_rendiciones_y_proyectos_disponibles(self):
        response = self.client.get(
            reverse("organizacion_detalle", kwargs={"pk": self.organizacion.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Rendiciones Presentadas")
        self.assertContains(response, "CONV-01")
        self.assertContains(response, "CONV-02")
        self.assertEqual(response.context["proyectos_rendiciones"], ["P01", "P02"])

    def test_filtro_por_proyecto_limita_resultados_y_activa_tab(self):
        response = self.client.get(
            reverse("organizacion_detalle", kwargs={"pk": self.organizacion.pk}),
            {"proyecto": "P01"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CONV-01")
        self.assertNotContains(response, "CONV-02")
        self.assertTrue(response.context["rendiciones_tab_activo"])

    def test_detalle_muestra_datos_y_enlace_a_rendicion(self):
        response = self.client.get(
            reverse(
                "organizacion_rendicion_detalle",
                kwargs={
                    "organizacion_id": self.organizacion.pk,
                    "pk": self.rendicion_p01.pk,
                },
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CONV-01")
        self.assertEqual(response.context["rendicion"].monto_rendido, 3000000)
        self.assertContains(response, "Ir a Rendición")

    def test_detalle_no_expone_rendicion_de_otra_organizacion(self):
        otra_organizacion = Organizacion.objects.create(nombre="Otra organización")

        response = self.client.get(
            reverse(
                "organizacion_rendicion_detalle",
                kwargs={
                    "organizacion_id": otra_organizacion.pk,
                    "pk": self.rendicion_p01.pk,
                },
            )
        )

        self.assertEqual(response.status_code, 404)


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

    def test_cuit_valido_para_los_tres_tipos_de_entidad(self):
        tipos = [
            TipoEntidad.objects.create(nombre="Personería jurídica"),
            TipoEntidad.objects.create(nombre="Personería jurídica eclesiástica"),
            TipoEntidad.objects.create(nombre="Asociación de hecho"),
        ]

        for tipo_entidad in tipos:
            with self.subTest(tipo_entidad=tipo_entidad.nombre):
                form = OrganizacionForm(
                    data=self._form_data(
                        {"cuit": "20999999990", "tipo_entidad": tipo_entidad.pk}
                    )
                )
                self.assertTrue(form.is_valid(), form.errors)

    def test_cuit_rechaza_simbolos_espacios_y_longitud_invalida(self):
        casos_invalidos = (
            "20-99999999-0",
            "20 99999999 0",
            "2099999999",
            "209999999900",
        )

        for cuit in casos_invalidos:
            with self.subTest(cuit=cuit):
                form = OrganizacionForm(data=self._form_data({"cuit": cuit}))
                self.assertFalse(form.is_valid())
                self.assertIn("cuit", form.errors)

    def test_cuit_expone_restricciones_en_el_input(self):
        campo = OrganizacionForm().fields["cuit"]

        self.assertEqual(campo.widget.attrs["inputmode"], "numeric")
        self.assertEqual(campo.widget.attrs["maxlength"], "11")
        self.assertEqual(campo.widget.attrs["pattern"], "[0-9]{11}")


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
