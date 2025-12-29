import io
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from importarexpediente.models import ArchivosImportados, ErroresImportacion, ExitoImportacion, RegistroImportado
from comedores.models import Comedor
from expedientespagos.models import ExpedientePago


User = get_user_model()


class ImportarExpedienteViewsTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username="tester", password="pass1234")
		self.client.login(username="tester", password="pass1234")
		# Crear un comedor que pueda resolverse por ID o nombre
		self.comedor = Comedor.objects.create(nombre="ADONAI")

	def _make_csv_file(self, text: str, name: str = "test.csv"):
		data = text.encode("utf-8")
		return SimpleUploadedFile(name, data, content_type="text/csv")

	@patch.object(ExpedientePago, "full_clean")
	def test_upload_view_logs_success_and_errors(self, mock_full_clean):
		# Simular validación: raise para segunda fila
		def side_effect():
			# Usar un contador externo vía attribute
			if not hasattr(mock_full_clean, "_calls"):
				mock_full_clean._calls = 0
			mock_full_clean._calls += 1
			if mock_full_clean._calls == 2:
				raise ValidationError("Fila inválida en prueba")

		mock_full_clean.side_effect = side_effect

		csv_text = (
			"ID;COMEDOR;Expediente de Pago;TOTAL\n"
			f"{self.comedor.id};{self.comedor.nombre};EX-2025-AAA;\"$ 1.000,00\"\n"
			f"99999;NO_EXISTE;EX-2025-BBB;\"$ 2.000,00\"\n"
		)
		uploaded = self._make_csv_file(csv_text)

		resp = self.client.post(
			reverse("upload"),
			{"file": uploaded, "delimiter": ";", "has_header": True},
			follow=True,
		)
		self.assertEqual(resp.status_code, 200)

		# Se crea un maestro y se registran éxito + error
		self.assertEqual(ArchivosImportados.objects.count(), 1)
		master = ArchivosImportados.objects.first()
		self.assertEqual(ExitoImportacion.objects.filter(archivo_importado=master).count(), 1)
		self.assertEqual(ErroresImportacion.objects.filter(archivo_importado=master).count(), 1)
		# Contadores persistidos
		master.refresh_from_db()
		self.assertEqual(master.count_exitos, 1)
		self.assertEqual(master.count_errores, 1)

	def test_list_view_renders(self):
		ArchivosImportados.objects.create(archivo="importados/dummy.csv", usuario=self.user)
		resp = self.client.get(reverse("importarexpedientes_list"))
		self.assertEqual(resp.status_code, 200)

	def test_detail_view_shows_errors_and_success(self):
		# Preparar maestro + registros
		master = ArchivosImportados.objects.create(archivo="importados/dummy.csv", usuario=self.user)
		ExitoImportacion.objects.create(archivo_importado=master, fila=2, mensaje="Fila válida")
		ErroresImportacion.objects.create(archivo_importado=master, fila=3, mensaje="Error de prueba")

		resp = self.client.get(reverse("importarexpediente_detail", args=[master.id]))
		self.assertEqual(resp.status_code, 200)
		# El template debería poder acceder a los registros listados
		self.assertContains(resp, "Error")
		self.assertContains(resp, "Fila válida")

	@patch.object(ExpedientePago, "full_clean")
	def test_import_datos_creates_records_and_logs_ids(self, mock_full_clean):
		mock_full_clean.return_value = None
		# CSV almacenado en el FileField del maestro
		csv_text = (
			"ID;COMEDOR;Expediente de Pago;TOTAL\n"
			f"{self.comedor.id};{self.comedor.nombre};EX-2025-CCC;\"$ 3.000,00\"\n"
		)
		uploaded = self._make_csv_file(csv_text, name="stored.csv")

		master = ArchivosImportados.objects.create(archivo=uploaded, usuario=self.user)

		resp = self.client.post(reverse("importar_datos", args=[master.id]), follow=True)
		self.assertEqual(resp.status_code, 200)

		# Debe haberse creado al menos un ExpedientePago
		self.assertGreater(ExpedientePago.objects.count(), 0)
		exp = ExpedientePago.objects.first()

		# Debe existir un RegistroImportado enlazado a la fila y al éxito creado/ubicado
		self.assertGreater(RegistroImportado.objects.count(), 0)
		reg = RegistroImportado.objects.first()
		self.assertEqual(reg.id_expediente, exp.id)

