import logging
from django.shortcuts import get_object_or_404
from django.views import View
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect

from celiaquia.models import ExpedienteCiudadano
from celiaquia.permissions import can_confirm_subsanacion

logger = logging.getLogger("django")


def _in_group(user, name: str) -> bool:
    return user.is_authenticated and user.groups.filter(name=name).exists()


class RespuestaSubsanacionRenaperView(View):
    """Vista para responder a subsanación Renaper"""

    def dispatch(self, request, *args, **kwargs):
        # Verificar permisos - solo provincia
        user = request.user
        if not user.is_authenticated:
            raise PermissionDenied("Autenticación requerida.")

        is_admin = user.is_superuser
        is_prov = _in_group(user, "ProvinciaCeliaquia")

        if not (is_admin or is_prov):
            raise PermissionDenied("Permiso denegado.")

        return super().dispatch(request, *args, **kwargs)

    @method_decorator(csrf_protect)
    def post(self, request, pk, legajo_id):
        try:
            # Obtener el legajo
            legajo = get_object_or_404(
                ExpedienteCiudadano, pk=legajo_id, expediente__pk=pk
            )

            # Verificar permisos sobre el expediente asociado
            can_confirm_subsanacion(request.user, legajo.expediente)

            # Verificar que el legajo esté en estado de subsanación Renaper
            if legajo.estado_validacion_renaper != 3:
                return JsonResponse(
                    {
                        "success": False,
                        "error": "El legajo no está en estado de subsanación Renaper",
                    }
                )

            comentario = request.POST.get("comentario", "").strip()
            archivo = request.FILES.get("archivo")

            if not comentario:
                return JsonResponse(
                    {"success": False, "error": "El comentario es obligatorio"}
                )

            # Guardar respuesta
            legajo.subsanacion_renaper_comentario = comentario
            if archivo:
                legajo.subsanacion_renaper_archivo = archivo

            # Mantener estado de subsanación Renaper (3) hasta que técnico valide nuevamente
            # legajo.estado_validacion_renaper = 3  # Ya está en 3, no cambiar
            legajo.revision_tecnico = "SUBSANADO"

            legajo.save(
                update_fields=[
                    "subsanacion_renaper_comentario",
                    "subsanacion_renaper_archivo",
                    "revision_tecnico",
                    "modificado_en",
                ]
            )

            return JsonResponse(
                {
                    "success": True,
                    "message": "Respuesta a subsanación Renaper enviada correctamente",
                }
            )

        except PermissionDenied as exc:
            logger.warning(
                "celiaquia.respuesta_subsanacion.permission_denied",
                extra={
                    "user_id": getattr(request.user, "id", None),
                    "legajo_id": legajo_id,
                    "expediente_id": pk,
                    "error": str(exc),
                },
            )
            return JsonResponse(
                {"success": False, "error": str(exc)},
                status=403,
            )

        except Exception as e:
            logger.error(
                "Error al responder subsanación Renaper legajo %s: %s",
                legajo_id,
                str(e),
                exc_info=True,
            )
            return JsonResponse(
                {
                    "success": False,
                    "error": "Se produjo un error inesperado. Por favor, inténtelo nuevamente más tarde.",
                },
                status=500,
            )
