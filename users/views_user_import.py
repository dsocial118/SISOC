from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views import View

from users.forms import UserImportForm
from users.views import AdminRequiredMixin
from users.services_user_import import (
    USER_IMPORT_TEMPLATE_FILENAME,
    create_user_import_job,
    generate_user_import_template,
)
from users.services_user_import_jobs import (
    can_resume_user_import_job,
    get_recent_user_import_jobs,
    get_user_import_job_or_404,
    request_resume_user_import_job,
)

USER_IMPORT_PERMISSION_CODE = "auth.add_user"


class UserImportJobCreateView(AdminRequiredMixin, View):
    required_permissions = (USER_IMPORT_PERMISSION_CODE,)
    template_name = "user/user_import_form.html"

    def get(self, request, *args, **kwargs):
        return render(
            request,
            self.template_name,
            self._build_context(form=UserImportForm()),
        )

    def post(self, request, *args, **kwargs):
        form = UserImportForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, self.template_name, self._build_context(form=form))

        try:
            job = create_user_import_job(
                uploaded_file=form.cleaned_data["archivo"],
                requested_by=request.user,
                send_credentials=bool(form.cleaned_data["enviar_credenciales"]),
                is_pwa_import=bool(form.cleaned_data["es_pwa"]),
            )
        except ValidationError as exc:
            form.add_error("archivo", " ".join(exc.messages))
            return render(request, self.template_name, self._build_context(form=form))

        messages.success(
            request,
            (
                f"Lote de importacion creado con {job.total_rows} filas. "
                "El procesamiento continua en background. "
                "Puede seguir el estado desde el detalle del lote."
            ),
        )
        return HttpResponseRedirect(
            reverse("usuarios_importar_detalle", kwargs={"pk": job.pk})
        )

    def _build_context(self, *, form):
        return {
            "form": form,
            "template_download_url": reverse("usuarios_importar_plantilla"),
            "recent_jobs": get_recent_user_import_jobs(requested_by=self.request.user),
        }


class UserImportJobDetailView(AdminRequiredMixin, View):
    required_permissions = (USER_IMPORT_PERMISSION_CODE,)
    template_name = "user/user_import_job_detail.html"
    paginate_by = 50

    def get(self, request, *args, **kwargs):
        job = get_user_import_job_or_404(job_id=kwargs["pk"])
        rows_qs = job.rows.order_by("fila", "id")
        status_filter = request.GET.get("estado")
        if status_filter:
            rows_qs = rows_qs.filter(status=status_filter)
        paginator = Paginator(rows_qs, self.paginate_by)
        page_obj = paginator.get_page(request.GET.get("page"))
        return render(
            request,
            self.template_name,
            {
                "job": job,
                "page_obj": page_obj,
                "is_resume_available": can_resume_user_import_job(job),
                "upload_url": reverse("usuarios_importar"),
                "status_filter": status_filter,
            },
        )


class UserImportJobResumeView(AdminRequiredMixin, View):
    required_permissions = (USER_IMPORT_PERMISSION_CODE,)

    def post(self, request, *args, **kwargs):
        job = get_user_import_job_or_404(job_id=kwargs["pk"])
        try:
            request_resume_user_import_job(job=job)
        except ValidationError as exc:
            messages.error(request, " ".join(exc.messages))
        else:
            messages.success(
                request,
                "El lote quedo pendiente para reanudarse desde la ultima fila fallida.",
            )
        return HttpResponseRedirect(
            reverse("usuarios_importar_detalle", kwargs={"pk": job.pk})
        )


class UserImportTemplateView(AdminRequiredMixin, View):
    required_permissions = (USER_IMPORT_PERMISSION_CODE,)

    def get(self, request, *args, **kwargs):
        content = generate_user_import_template()
        response = HttpResponse(
            content,
            content_type=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
        )
        response["Content-Disposition"] = (
            f'attachment; filename="{USER_IMPORT_TEMPLATE_FILENAME}"'
        )
        return response
