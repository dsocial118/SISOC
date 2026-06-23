"""Vistas de respuesta a subsanaciones (Fase 2): carga múltiple de archivos."""

import logging

from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_protect

from celiaquia.models import ExpedienteCiudadano, RevisionTecnico
from celiaquia.permissions import can_edit_legajo_files
from celiaquia.services.subsanacion_service import SubsanacionService
from celiaquia.utils import error_response, success_response

logger = logging.getLogger("django")


class SubsanacionRespuestaUploadView(View):
    """La provincia responde la subsanación activa de un legajo adjuntando uno o
    varios archivos como evidencia nueva (sin reemplazar la documentación
    original)."""

    def get(self, *_a, **_k):
        return HttpResponseNotAllowed(["POST"])

    @method_decorator(csrf_protect)
    def post(self, request, pk, legajo_id):
        legajo = get_object_or_404(ExpedienteCiudadano, pk=legajo_id, expediente__pk=pk)

        try:
            can_edit_legajo_files(request.user, legajo.expediente, legajo)
        except PermissionDenied as exc:
            return error_response(str(exc) or "Permiso denegado.", status=403)

        if legajo.revision_tecnico != RevisionTecnico.SUBSANAR:
            return error_response(
                "El legajo no tiene una subsanación técnica activa.",
                status=400,
            )

        if legajo.estado_validacion_renaper == 3:
            return error_response(
                "El legajo tiene una subsanación Renaper pendiente.",
                status=400,
            )

        archivos = request.FILES.getlist("archivos")
        if not archivos:
            # Compatibilidad con inputs de un solo archivo.
            archivo_unico = request.FILES.get("archivo")
            if archivo_unico:
                archivos = [archivo_unico]

        try:
            subsanacion = SubsanacionService.responder(
                legajo=legajo,
                archivos=archivos,
                usuario=request.user,
                descripcion=request.POST.get("descripcion", ""),
                observacion_id=request.POST.get("observacion_id") or None,
            )
        except ValidationError as exc:
            mensaje = "; ".join(exc.messages) if hasattr(exc, "messages") else str(exc)
            return error_response(mensaje, status=400)
        except Exception as exc:  # pragma: no cover - error inesperado
            logger.error(
                "Error al responder subsanación de legajo %s: %s",
                legajo.pk,
                exc,
                exc_info=True,
            )
            return error_response(
                "Ocurrió un error al subir los archivos de subsanación.",
                status=500,
            )

        return success_response(
            "Archivos de subsanación cargados correctamente.",
            extra_data={
                "subsanacion_id": subsanacion.pk,
                "archivos": subsanacion.archivos.count(),
            },
        )
