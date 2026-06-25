from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ocr.models import OCRJob, OCRJobDocument

User = get_user_model()


def _make_png(name="test.png"):
    return SimpleUploadedFile(name, b"fakeimgdata", content_type="image/png")


def _give_ocr_permission(user):
    perm = Permission.objects.get(codename="use_ocr")
    user.user_permissions.add(perm)


class OCRUploadViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="uploader", password="pass")
        _give_ocr_permission(self.user)
        self.url = reverse("ocr_upload")

    def _login(self):
        self.client.force_login(self.user)

    def test_get_requires_login(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f"/login/?next={self.url}")

    def test_get_renders_form(self):
        self._login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "ocr/ocr_upload.html")
        self.assertIn("form", response.context)

    def test_get_shows_max_file_size(self):
        self._login()
        response = self.client.get(self.url)
        self.assertIn("max_file_size_mb", response.context)

    def test_post_no_files_shows_error(self):
        self._login()
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertFormError(form, "archivos", "Debe seleccionar al menos un archivo.")

    def test_post_invalid_extension_shows_error(self):
        self._login()
        bad_file = SimpleUploadedFile(
            "file.xls", b"data", content_type="application/vnd.ms-excel"
        )
        response = self.client.post(self.url, {"archivos": bad_file})
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertFalse(form.is_valid())

    @patch("ocr.views.create_ocr_job")
    def test_post_valid_files_creates_job_and_redirects(self, mock_create):
        self._login()
        fake_job = OCRJob.objects.create(
            requested_by=self.user,
            total_documents=1,
        )
        mock_create.return_value = fake_job
        response = self.client.post(self.url, {"archivos": _make_png()})
        self.assertRedirects(
            response,
            reverse("ocr_job_detail", kwargs={"pk": fake_job.pk}),
            fetch_redirect_response=False,
        )
        mock_create.assert_called_once()

    def test_superuser_can_access_without_permission(self):
        superuser = User.objects.create_superuser(username="super", password="pass")
        self.client.force_login(superuser)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)


class OCRJobDetailViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="detailer", password="pass")
        _give_ocr_permission(self.user)
        self.job = OCRJob.objects.create(requested_by=self.user, total_documents=1)
        OCRJobDocument.objects.create(
            job=self.job,
            original_filename="test.png",
            status=OCRJobDocument.Status.COMPLETED,
            extracted_text="Texto extraído de prueba.",
        )

    def _login(self):
        self.client.force_login(self.user)

    def test_get_requires_login(self):
        url = reverse("ocr_job_detail", kwargs={"pk": self.job.pk})
        response = self.client.get(url)
        self.assertRedirects(response, f"/login/?next={url}")

    def test_get_shows_job_detail(self):
        self._login()
        response = self.client.get(
            reverse("ocr_job_detail", kwargs={"pk": self.job.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "ocr/ocr_job_detail.html")
        self.assertIn("job", response.context)
        self.assertEqual(response.context["job"].pk, self.job.pk)

    def test_get_other_users_job_returns_404(self):
        other = User.objects.create_user(username="other", password="pass")
        _give_ocr_permission(other)
        self.client.force_login(other)
        response = self.client.get(
            reverse("ocr_job_detail", kwargs={"pk": self.job.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_superuser_can_see_any_job(self):
        superuser = User.objects.create_superuser(username="super", password="pass")
        self.client.force_login(superuser)
        response = self.client.get(
            reverse("ocr_job_detail", kwargs={"pk": self.job.pk})
        )
        self.assertEqual(response.status_code, 200)


class OCRDocumentDownloadViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="downloader", password="pass")
        _give_ocr_permission(self.user)
        self.job = OCRJob.objects.create(requested_by=self.user, total_documents=1)
        self.doc = OCRJobDocument.objects.create(
            job=self.job,
            original_filename="factura.pdf",
            status=OCRJobDocument.Status.COMPLETED,
            extracted_text="Contenido de la factura.",
        )

    def _login(self):
        self.client.force_login(self.user)

    def test_download_returns_txt(self):
        self._login()
        response = self.client.get(
            reverse("ocr_document_download", kwargs={"doc_pk": self.doc.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/plain", response.get("Content-Type", ""))
        self.assertIn("factura.txt", response.get("Content-Disposition", ""))
        self.assertEqual(response.content.decode("utf-8"), "Contenido de la factura.")

    def test_download_other_users_doc_returns_404(self):
        other = User.objects.create_user(username="other2", password="pass")
        _give_ocr_permission(other)
        self.client.force_login(other)
        response = self.client.get(
            reverse("ocr_document_download", kwargs={"doc_pk": self.doc.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_download_empty_text_returns_empty_txt(self):
        self._login()
        self.doc.extracted_text = ""
        self.doc.save(update_fields=["extracted_text"])
        response = self.client.get(
            reverse("ocr_document_download", kwargs={"doc_pk": self.doc.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"")
