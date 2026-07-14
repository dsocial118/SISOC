from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from ocr.models import OCRJob, OCRJobDocument
from ocr.services_ocr import _resolve_options, extract_text_from_file
from ocr.services_ocr_jobs import create_ocr_job, process_ocr_job

User = get_user_model()


class ResolveOptionsTest(TestCase):
    @override_settings(
        OCR_PREPROCESS=True, OCR_PDF_TEXT_LAYER=True, OCR_AUTO_ORIENT=True
    )
    def test_defaults_from_settings_when_no_options(self):
        opts = _resolve_options(None)
        self.assertEqual(
            opts,
            {"preprocess": True, "pdf_text_layer": True, "auto_orient": True},
        )

    @override_settings(OCR_PREPROCESS=True, OCR_AUTO_ORIENT=True)
    def test_override_wins_over_setting(self):
        opts = _resolve_options({"preprocess": False})
        self.assertFalse(opts["preprocess"])
        self.assertTrue(opts["auto_orient"])  # no override -> setting


class ExtractPassesOptionsTest(TestCase):
    @patch("ocr.services_ocr._extract_from_pdf")
    def test_options_threaded_to_pdf_extractor(self, mock_pdf):
        mock_pdf.return_value = {"text": "x", "page_count": 1, "warning": None}
        extract_text_from_file(
            "/fake/doc.pdf",
            "doc.pdf",
            options={
                "preprocess": False,
                "pdf_text_layer": False,
                "auto_orient": False,
            },
        )
        passed_opts = mock_pdf.call_args[0][2]
        self.assertEqual(
            passed_opts,
            {"preprocess": False, "pdf_text_layer": False, "auto_orient": False},
        )


class CreateOCRJobOptionsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="opts", password="pass")

    def test_stores_options_on_job(self):
        job = create_ocr_job(
            requested_by=self.user,
            files=[],
            options={"preprocess": False, "pdf_text_layer": True, "auto_orient": False},
        )
        self.assertFalse(job.opt_preprocess)
        self.assertTrue(job.opt_pdf_text_layer)
        self.assertFalse(job.opt_auto_orient)

    def test_defaults_all_true_without_options(self):
        job = create_ocr_job(requested_by=self.user, files=[])
        self.assertTrue(job.opt_preprocess)
        self.assertTrue(job.opt_pdf_text_layer)
        self.assertTrue(job.opt_auto_orient)


class ProcessJobPassesOptionsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="procopts", password="pass")

    @patch("ocr.services_ocr_jobs._delete_file")
    @patch("ocr.services_ocr_jobs.extract_text_from_file")
    def test_job_options_reach_extractor(self, mock_extract, _mock_delete):
        mock_extract.return_value = {"text": "ok", "page_count": None, "warning": None}
        job = OCRJob.objects.create(
            requested_by=self.user,
            status=OCRJob.Status.PROCESSING,
            total_documents=1,
            opt_preprocess=False,
            opt_pdf_text_layer=False,
            opt_auto_orient=True,
        )
        OCRJobDocument.objects.create(
            job=job, original_filename="x.png", archivo="ocr/x.png"
        )
        process_ocr_job(job)
        options = mock_extract.call_args.kwargs["options"]
        self.assertEqual(
            options,
            {"preprocess": False, "pdf_text_layer": False, "auto_orient": True},
        )
