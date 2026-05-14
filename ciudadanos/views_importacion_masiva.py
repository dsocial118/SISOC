from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic import FormView, TemplateView

from ciudadanos.forms import CiudadanosImportUploadForm
from ciudadanos.services_importacion_masiva import (
    generate_ciudadanos_import_template,
    get_ciudadanos_import_template_filename,
)
from ciudadanos.services_importacion_masiva_jobs import (
    can_resume_ciudadanos_import_job,
    create_ciudadanos_import_job,
    get_ciudadanos_import_job_or_404,
    get_recent_ciudadanos_import_jobs,
    request_resume_ciudadanos_import_job,
)


class CiudadanosImportPermissionMixin(LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = "ciudadanos.add_ciudadano"
    raise_exception = True


class CiudadanosImportTemplateView(CiudadanosImportPermissionMixin, View):
    def get(self, request, *args, **kwargs):
        response = HttpResponse(
            generate_ciudadanos_import_template(),
            content_type=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
        )
        filename = get_ciudadanos_import_template_filename()
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class CiudadanosImportUploadView(CiudadanosImportPermissionMixin, FormView):
    form_class = CiudadanosImportUploadForm
    template_name = "ciudadanos/importacion_masiva_form.html"

    def get_success_url(self):
        return reverse("ciudadanos_importacion_masiva_lote", kwargs={"pk": self.job.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["recent_jobs"] = get_recent_ciudadanos_import_jobs()
        context["template_download_url"] = reverse(
            "ciudadanos_importacion_masiva_plantilla"
        )
        return context

    def form_valid(self, form):
        self.job = create_ciudadanos_import_job(
            uploaded_file=form.cleaned_data["archivo"],
            requested_by=self.request.user,
        )
        messages.success(
            self.request,
            "Lote creado. El worker lo procesara de forma asincronica.",
        )
        return super().form_valid(form)


class CiudadanosImportJobDetailView(CiudadanosImportPermissionMixin, TemplateView):
    template_name = "ciudadanos/importacion_masiva_job_detail.html"
    paginate_by = 50

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        job = get_ciudadanos_import_job_or_404(job_id=self.kwargs["pk"])
        rows = job.rows.select_related("ciudadano").order_by("fila", "id")
        paginator = Paginator(rows, self.paginate_by)
        rows_page = paginator.get_page(self.request.GET.get("page"))
        context.update(
            {
                "job": job,
                "rows_page": rows_page,
                "can_resume": can_resume_ciudadanos_import_job(job),
            }
        )
        return context


class CiudadanosImportJobResumeView(CiudadanosImportPermissionMixin, View):
    def post(self, request, *args, **kwargs):
        job = get_ciudadanos_import_job_or_404(job_id=kwargs["pk"])
        try:
            request_resume_ciudadanos_import_job(job=job)
            messages.success(request, "Lote marcado para reanudacion.")
        except ValidationError as exc:
            messages.error(request, " ".join(exc.messages))
        return redirect("ciudadanos_importacion_masiva_lote", pk=job.pk)
