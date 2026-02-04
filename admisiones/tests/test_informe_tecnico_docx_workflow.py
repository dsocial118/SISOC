from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import models
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from admisiones.models.admisiones import Admision, InformeTecnico
from admisiones.services.admisiones_service import AdmisionService
from admisiones.services.informes_service import InformeService
from comedores.models import Comedor
from duplas.models import Dupla


User = get_user_model()


def _fake_value_for_field(field):
    if field.choices:
        return field.choices[0][0]
    if isinstance(field, models.EmailField):
        return "test@example.com"
    if isinstance(field, (models.CharField, models.TextField)):
        return "test"
    if isinstance(field, models.BooleanField):
        return False
    if isinstance(field, models.DecimalField):
        return Decimal("1.0")
    if isinstance(field, models.FloatField):
        return 1.0
    if isinstance(field, models.DateTimeField):
        return timezone.now()
    if isinstance(field, models.DateField):
        return timezone.now().date()
    if isinstance(field, models.IntegerField):
        return 1
    return "test"


def crear_informe_tecnico(admision, **overrides):
    data = {}
    for field in InformeTecnico._meta.fields:
        if field.primary_key or field.auto_created:
            continue
        if getattr(field, "auto_now", False) or getattr(field, "auto_now_add", False):
            continue
        if field.has_default():
            continue
        if isinstance(field, models.ForeignKey):
            continue
        if field.null:
            continue
        data[field.name] = _fake_value_for_field(field)

    data.update(
        {
            "admision": admision,
            "tipo": "base",
            "estado": "Iniciado",
            "estado_formulario": "borrador",
        }
    )
    data.update(overrides)
    return InformeTecnico.objects.create(**data)


class InformeTecnicoDocxWorkflowServiceTest(TestCase):
    def test_subir_docx_editado_actualiza_estado_y_campo(self):
        admision = Admision.objects.create(
            estado_admision="informe_tecnico_finalizado"
        )
        informe = crear_informe_tecnico(
            admision,
            estado="Docx generado",
            estado_formulario="finalizado",
        )
        archivo = SimpleUploadedFile(
            "informe.docx",
            b"contenido",
            content_type=(
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ),
        )

        pdf_obj = InformeService.subir_docx_editado(informe, archivo)

        self.assertIsNotNone(pdf_obj)
        pdf_obj.refresh_from_db()
        informe.refresh_from_db()
        admision.refresh_from_db()

        self.assertTrue(pdf_obj.archivo_docx_editado.name.endswith(".docx"))
        self.assertEqual(pdf_obj.informe_id, informe.id)
        self.assertEqual(informe.estado, "Docx editado")
        self.assertEqual(admision.estado_admision, "informe_tecnico_docx_editado")

    def test_guardar_informe_no_sobrescribe_validado(self):
        admision = Admision.objects.create()
        crear_informe_tecnico(admision, estado="Validado", tipo="base")

        class DummyForm:
            def __init__(self, instance):
                self.instance = instance

            def save(self, commit=False):
                raise AssertionError("No debería guardarse cuando ya está validado.")

        form = DummyForm(InformeTecnico(tipo="base"))
        resultado = InformeService.guardar_informe(
            form, admision, es_creacion=True, action="draft"
        )

        self.assertFalse(resultado.get("success"))
        self.assertIn("validado", resultado.get("error", "").lower())


class AdmisionEstadosGuardTest(TestCase):
    def test_no_retrocede_estado_docx_editado_por_documento(self):
        admision = Admision.objects.create(
            estado_admision="informe_tecnico_docx_editado"
        )

        AdmisionService._actualizar_estados_por_cambio_documento(admision, "Aceptado")

        admision.refresh_from_db()
        self.assertEqual(admision.estado_admision, "informe_tecnico_docx_editado")


class InformeTecnicoDocxViewPermsTest(TestCase):
    def setUp(self):
        self.user_out = User.objects.create_user(username="usuario_fuera", password="x")
        grupo_tecnico = Group.objects.create(name="Tecnico Comedor")
        self.user_out.groups.add(grupo_tecnico)

        abogado = User.objects.create_user(username="abogado", password="x")
        tecnico = User.objects.create_user(username="tecnico", password="x")

        self.dupla = Dupla.objects.create(
            nombre="Dupla Test", estado="Activo", abogado=abogado
        )
        self.dupla.tecnico.add(tecnico)

        self.comedor = Comedor.objects.create(nombre="Comedor Test", dupla=self.dupla)
        self.admision = Admision.objects.create(
            comedor=self.comedor, estado_admision="informe_tecnico_finalizado"
        )
        self.informe = crear_informe_tecnico(
            self.admision,
            estado="Docx generado",
            estado_formulario="finalizado",
        )

    def test_subir_docx_requiere_pertenecer_a_dupla(self):
        self.client.force_login(self.user_out)
        url = reverse("informe_tecnico_ver", args=[self.informe.tipo, self.informe.pk])

        archivo = SimpleUploadedFile(
            "informe.docx",
            b"contenido",
            content_type=(
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ),
        )
        response = self.client.post(url, data={"subir_docx": "1", "docx_editado": archivo})

        self.assertEqual(response.status_code, 403)
