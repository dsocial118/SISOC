from __future__ import annotations

from pathlib import Path

from django.contrib import messages
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View

from users.views import AdminRequiredMixin
from ocr.forms import OCRUploadForm
from ocr.models import OCRJob, OCRJobDocument
from ocr.services_ocr_jobs import create_ocr_job, get_recent_ocr_jobs

OCR_PERMISSION = "ocr.use_ocr"


class OCRUploadView(AdminRequiredMixin, View):
    required_permissions = (OCR_PERMISSION,)
    template_name = "ocr/ocr_upload.html"

    def _context(self, form):
        from django.conf import settings as django_settings

        return {
            "form": form,
            "recent_jobs": get_recent_ocr_jobs(requested_by=self.request.user),
            "max_file_size_mb": getattr(django_settings, "OCR_MAX_FILE_SIZE_MB", 20),
        }

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self._context(OCRUploadForm()))

    def post(self, request, *args, **kwargs):
        form = OCRUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, self.template_name, self._context(form))

        files = form.cleaned_data["archivos"]
        job = create_ocr_job(
            requested_by=request.user, files=files, options=form.get_options()
        )
        messages.success(
            request,
            f"Lote OCR #{job.id} creado con {job.total_documents} archivo(s). "
            "El procesamiento se ejecuta en segundo plano.",
        )
        return redirect(reverse("ocr_job_detail", kwargs={"pk": job.pk}))


class OCRJobDetailView(AdminRequiredMixin, View):
    required_permissions = (OCR_PERMISSION,)
    template_name = "ocr/ocr_job_detail.html"

    def get(self, request, *args, **kwargs):
        filters = {"pk": kwargs["pk"]}
        if not request.user.is_superuser:
            filters["requested_by"] = request.user
        job = get_object_or_404(OCRJob, **filters)
        documents = job.documents.order_by("id")
        return render(
            request,
            self.template_name,
            {
                "job": job,
                "documents": documents,
                "upload_url": reverse("ocr_upload"),
            },
        )


class OCRDocumentDownloadView(AdminRequiredMixin, View):
    required_permissions = (OCR_PERMISSION,)

    def get(self, request, *args, **kwargs):
        doc = get_object_or_404(OCRJobDocument, pk=kwargs["doc_pk"])
        if not request.user.is_superuser and doc.job.requested_by != request.user:
            raise Http404

        stem = Path(doc.original_filename).stem
        filename = f"{stem}.txt"
        response = HttpResponse(
            doc.extracted_text or "",
            content_type="text/plain; charset=utf-8",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
