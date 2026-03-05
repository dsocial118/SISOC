"""
Vista para descargar padrón final del expediente.
"""

from django.http import HttpResponse
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from celiaquia.models import Expediente
from celiaquia.services.padron_final_service import PadronFinalService
from iam.services import user_has_any_permission_codes

CELIAQUIA_EXPORT_PERMISSION_CODES = (
    "auth.role_coordinadorceliaquia",
    "auth.role_tecnicoceliaquia",
)


class ExpedientePadronFinalExportView(LoginRequiredMixin, View):
    """Descarga padrón final del expediente en Excel."""

    def get(self, request, expediente_id):
        """Genera y descarga el Excel del padrón final."""

        # Verificar permisos
        if not self._tiene_permiso(request.user):
            raise PermissionDenied("No tienes permiso para descargar el padrón final")

        # Obtener expediente
        expediente = get_object_or_404(Expediente, pk=expediente_id)

        # Generar Excel
        contenido = PadronFinalService.generar_padron_final_excel(expediente)

        # Respuesta
        response = HttpResponse(
            contenido,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = (
            f'attachment; filename="padron_final_{expediente_id}.xlsx"'
        )

        return response

    @staticmethod
    def _tiene_permiso(user):
        """Verifica si el usuario tiene permiso para descargar."""
        if not user.is_authenticated:
            return False

        if user.is_superuser or user.is_staff:
            return True

        # Verificar grupos permitidos
        return user_has_any_permission_codes(user, CELIAQUIA_EXPORT_PERMISSION_CODES)
