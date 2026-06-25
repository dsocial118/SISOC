from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone

from ocr.models import OCRJob, OCRJobDocument
from ocr.services_ocr_jobs import (
    claim_next_ocr_job,
    create_ocr_job,
    get_recent_ocr_jobs,
    mark_stale_ocr_jobs_as_failed,
    process_ocr_job,
)

User = get_user_model()


def _make_file(name="test.png", content=b"fakedata", content_type="image/png"):
    return SimpleUploadedFile(name, content, content_type=content_type)


class CreateOCRJobTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="creator", password="pass")

    def test_creates_job_and_documents(self):
        files = [
            _make_file("a.png"),
            _make_file("b.pdf", content_type="application/pdf"),
        ]
        job = create_ocr_job(requested_by=self.user, files=files)
        self.assertEqual(job.requested_by, self.user)
        self.assertEqual(job.status, OCRJob.Status.PENDING)
        self.assertEqual(job.total_documents, 2)
        self.assertEqual(job.documents.count(), 2)

    def test_document_original_filename_preserved(self):
        files = [_make_file("factura_2024.jpg")]
        job = create_ocr_job(requested_by=self.user, files=files)
        doc = job.documents.first()
        self.assertEqual(doc.original_filename, "factura_2024.jpg")

    def test_document_file_size_recorded(self):
        content = b"x" * 500
        files = [_make_file("test.png", content=content)]
        job = create_ocr_job(requested_by=self.user, files=files)
        doc = job.documents.first()
        self.assertEqual(doc.file_size, 500)

    def test_empty_files_creates_job_with_zero_docs(self):
        job = create_ocr_job(requested_by=self.user, files=[])
        self.assertEqual(job.total_documents, 0)
        self.assertEqual(job.documents.count(), 0)


class ClaimNextOCRJobTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="worker", password="pass")

    def test_returns_none_when_no_pending_jobs(self):
        result = claim_next_ocr_job()
        self.assertIsNone(result)

    def test_claims_pending_job(self):
        job = OCRJob.objects.create(
            requested_by=self.user, status=OCRJob.Status.PENDING
        )
        claimed = claim_next_ocr_job()
        self.assertIsNotNone(claimed)
        self.assertEqual(claimed.pk, job.pk)
        claimed.refresh_from_db()
        self.assertEqual(claimed.status, OCRJob.Status.PROCESSING)

    def test_does_not_claim_already_processing_job(self):
        OCRJob.objects.create(
            requested_by=self.user,
            status=OCRJob.Status.PROCESSING,
            last_activity_at=timezone.now(),
        )
        result = claim_next_ocr_job()
        self.assertIsNone(result)

    def test_does_not_claim_completed_job(self):
        OCRJob.objects.create(requested_by=self.user, status=OCRJob.Status.COMPLETED)
        result = claim_next_ocr_job()
        self.assertIsNone(result)


class MarkStaleJobsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="stale", password="pass")

    def test_marks_stale_processing_job_as_failed(self):
        job = OCRJob.objects.create(
            requested_by=self.user,
            status=OCRJob.Status.PROCESSING,
            last_activity_at=timezone.now() - timedelta(seconds=700),
        )
        count = mark_stale_ocr_jobs_as_failed()
        self.assertEqual(count, 1)
        job.refresh_from_db()
        self.assertEqual(job.status, OCRJob.Status.FAILED)

    def test_does_not_mark_recent_job_as_failed(self):
        OCRJob.objects.create(
            requested_by=self.user,
            status=OCRJob.Status.PROCESSING,
            last_activity_at=timezone.now() - timedelta(seconds=10),
        )
        count = mark_stale_ocr_jobs_as_failed()
        self.assertEqual(count, 0)

    def test_does_not_mark_pending_job_as_failed(self):
        OCRJob.objects.create(
            requested_by=self.user,
            status=OCRJob.Status.PENDING,
        )
        count = mark_stale_ocr_jobs_as_failed()
        self.assertEqual(count, 0)


class ProcessOCRJobTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="processor", password="pass")

    @patch("ocr.services_ocr_jobs.extract_text_from_file")
    @patch("ocr.services_ocr_jobs._delete_file")
    def test_successful_processing_marks_completed(self, mock_delete, mock_extract):
        mock_extract.return_value = {
            "text": "Texto extraído",
            "page_count": None,
            "warning": None,
        }
        job = OCRJob.objects.create(
            requested_by=self.user,
            status=OCRJob.Status.PROCESSING,
            total_documents=1,
        )
        doc = OCRJobDocument.objects.create(
            job=job,
            original_filename="test.png",
        )
        process_ocr_job(job)
        job.refresh_from_db()
        doc.refresh_from_db()
        self.assertEqual(job.status, OCRJob.Status.COMPLETED)
        self.assertEqual(job.processed_documents, 1)
        self.assertEqual(job.failed_documents, 0)
        self.assertEqual(doc.status, OCRJobDocument.Status.COMPLETED)
        self.assertEqual(doc.extracted_text, "Texto extraído")

    @patch("ocr.services_ocr_jobs.extract_text_from_file")
    @patch("ocr.services_ocr_jobs._delete_file")
    def test_no_text_marks_doc_as_no_text(self, mock_delete, mock_extract):
        mock_extract.return_value = {
            "text": "",
            "page_count": None,
            "warning": "No se pudo extraer texto legible del archivo.",
        }
        job = OCRJob.objects.create(
            requested_by=self.user,
            status=OCRJob.Status.PROCESSING,
            total_documents=1,
        )
        OCRJobDocument.objects.create(job=job, original_filename="blank.png")
        process_ocr_job(job)
        job.refresh_from_db()
        doc = job.documents.first()
        self.assertEqual(job.status, OCRJob.Status.COMPLETED)
        self.assertEqual(doc.status, OCRJobDocument.Status.NO_TEXT)

    @patch("ocr.services_ocr_jobs.extract_text_from_file")
    @patch("ocr.services_ocr_jobs._delete_file")
    def test_failed_doc_marks_job_completed_with_errors(
        self, mock_delete, mock_extract
    ):
        mock_extract.side_effect = Exception("OCR crash")
        job = OCRJob.objects.create(
            requested_by=self.user,
            status=OCRJob.Status.PROCESSING,
            total_documents=1,
        )
        OCRJobDocument.objects.create(job=job, original_filename="bad.jpg")
        process_ocr_job(job)
        job.refresh_from_db()
        doc = job.documents.first()
        self.assertEqual(job.status, OCRJob.Status.COMPLETED_WITH_ERRORS)
        self.assertEqual(job.failed_documents, 1)
        self.assertEqual(doc.status, OCRJobDocument.Status.FAILED)
        self.assertIn("OCR crash", doc.error_message)

    @patch("ocr.services_ocr_jobs.extract_text_from_file")
    @patch("ocr.services_ocr_jobs._delete_file")
    def test_partial_failure_continues_processing(self, mock_delete, mock_extract):
        mock_extract.side_effect = [
            Exception("Error en doc 1"),
            {"text": "Texto doc 2", "page_count": None, "warning": None},
        ]
        job = OCRJob.objects.create(
            requested_by=self.user,
            status=OCRJob.Status.PROCESSING,
            total_documents=2,
        )
        OCRJobDocument.objects.create(job=job, original_filename="bad.jpg")
        OCRJobDocument.objects.create(job=job, original_filename="good.png")
        process_ocr_job(job)
        job.refresh_from_db()
        docs = list(job.documents.order_by("id"))
        self.assertEqual(job.status, OCRJob.Status.COMPLETED_WITH_ERRORS)
        self.assertEqual(job.processed_documents, 2)
        self.assertEqual(job.failed_documents, 1)
        self.assertEqual(docs[0].status, OCRJobDocument.Status.FAILED)
        self.assertEqual(docs[1].status, OCRJobDocument.Status.COMPLETED)

    @patch("ocr.services_ocr_jobs.extract_text_from_file")
    @patch("ocr.services_ocr_jobs._delete_file")
    def test_pdf_page_count_stored(self, mock_delete, mock_extract):
        mock_extract.return_value = {
            "text": "Página 1\nPágina 2",
            "page_count": 2,
            "warning": None,
        }
        job = OCRJob.objects.create(
            requested_by=self.user,
            status=OCRJob.Status.PROCESSING,
            total_documents=1,
        )
        OCRJobDocument.objects.create(job=job, original_filename="multi.pdf")
        process_ocr_job(job)
        doc = job.documents.first()
        self.assertEqual(doc.page_count, 2)


class GetRecentOCRJobsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="recent", password="pass")

    def test_returns_jobs_for_user(self):
        OCRJob.objects.create(requested_by=self.user)
        OCRJob.objects.create(requested_by=self.user)
        jobs = get_recent_ocr_jobs(requested_by=self.user)
        self.assertEqual(len(jobs), 2)

    def test_respects_limit(self):
        for _ in range(15):
            OCRJob.objects.create(requested_by=self.user)
        jobs = get_recent_ocr_jobs(limit=5, requested_by=self.user)
        self.assertEqual(len(jobs), 5)
