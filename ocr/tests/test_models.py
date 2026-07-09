from django.contrib.auth import get_user_model
from django.test import TestCase

from ocr.models import OCRJob, OCRJobDocument

User = get_user_model()


class OCRJobModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="pass")

    def test_create_job_defaults(self):
        job = OCRJob.objects.create(requested_by=self.user)
        self.assertEqual(job.status, OCRJob.Status.PENDING)
        self.assertEqual(job.total_documents, 0)
        self.assertEqual(job.processed_documents, 0)
        self.assertEqual(job.failed_documents, 0)
        self.assertEqual(job.last_error_message, "")
        self.assertIsNone(job.started_at)
        self.assertIsNone(job.finished_at)
        self.assertIsNone(job.last_activity_at)

    def test_str(self):
        job = OCRJob.objects.create(requested_by=self.user)
        self.assertIn(str(job.id), str(job))
        self.assertIn("Pendiente", str(job))

    def test_status_choices(self):
        statuses = [c[0] for c in OCRJob.Status.choices]
        self.assertIn("pending", statuses)
        self.assertIn("processing", statuses)
        self.assertIn("completed", statuses)
        self.assertIn("completed_with_errors", statuses)
        self.assertIn("failed", statuses)


class OCRJobDocumentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser2", password="pass")
        self.job = OCRJob.objects.create(requested_by=self.user, total_documents=1)

    def test_create_document_defaults(self):
        doc = OCRJobDocument.objects.create(
            job=self.job,
            original_filename="test.png",
            file_size=1024,
        )
        self.assertEqual(doc.status, OCRJobDocument.Status.PENDING)
        self.assertEqual(doc.extracted_text, "")
        self.assertEqual(doc.error_message, "")
        self.assertIsNone(doc.page_count)
        self.assertIsNone(doc.processed_at)

    def test_str(self):
        doc = OCRJobDocument.objects.create(
            job=self.job,
            original_filename="factura.pdf",
        )
        self.assertIn("factura.pdf", str(doc))
        self.assertIn("Pendiente", str(doc))

    def test_document_belongs_to_job(self):
        doc = OCRJobDocument.objects.create(
            job=self.job,
            original_filename="img.jpg",
        )
        self.assertEqual(self.job.documents.count(), 1)
        self.assertEqual(self.job.documents.first().pk, doc.pk)
