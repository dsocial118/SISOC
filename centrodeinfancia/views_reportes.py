"""Módulo de reportes de Centro de Infancia (issue #2508)."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView, View

from centrodeinfancia.services_reportes import (
    generar_reporte_cdi_xlsx,
    provincias_en_alcance,
)
from iam.services import user_has_permission_code


# Permiso propio y no `auth.role_exportar_a_csv`: ese es global y habilitaría a
# los roles SIMEPI a exportar comedores, usuarios y el resto de los listados.
PERMISO_REPORTES = "auth.role_reportes_cdi"
PERMISO_EXPORTACION = "auth.role_exportar_a_csv"
XLSX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def puede_exportar_reportes(user):
    """Superusuario, permiso propio del módulo, o el permiso global de exportación."""
    if getattr(user, "is_superuser", False):
        return True
    return user_has_permission_code(user, PERMISO_REPORTES) or user_has_permission_code(
        user, PERMISO_EXPORTACION
    )


class ReportesCDIView(LoginRequiredMixin, TemplateView):
    """Pantalla del módulo; no expone datos por sí misma."""

    template_name = "centrodeinfancia/reportes.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["puede_exportar"] = puede_exportar_reportes(self.request.user)
        context["provincias"] = provincias_en_alcance(self.request.user)
        context["breadcrumb_items"] = [
            {
                "text": "Centro de Desarrollo Infantil",
                "url": reverse("centrodeinfancia"),
            },
            {"text": "Reportes", "active": True},
        ]
        return context


class ReporteCDIDescargaView(LoginRequiredMixin, View):
    """Descarga el XLSX con lo que el usuario puede ver, nunca más que eso."""

    def get(self, request, *args, **kwargs):
        if not puede_exportar_reportes(request.user):
            raise PermissionDenied("No tiene permiso para exportar reportes.")

        # El filtro solo acota: el alcance del usuario se aplica igual.
        provincia_id = request.GET.get("provincia") or None
        contenido = generar_reporte_cdi_xlsx(request.user, provincia_id)
        nombre = f"reporte-cdi-{timezone.localdate():%Y%m%d}.xlsx"
        response = HttpResponse(contenido, content_type=XLSX_CONTENT_TYPE)
        response["Content-Disposition"] = f'attachment; filename="{nombre}"'
        # El archivo contiene datos personales de niños, niñas y responsables.
        response["Cache-Control"] = "private, no-store"
        response["Pragma"] = "no-cache"
        return response
