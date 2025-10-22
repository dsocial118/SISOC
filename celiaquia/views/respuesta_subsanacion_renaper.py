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
            logger.info("=== INICIO RESPUESTA SUBSANACION RENAPER ===")
            logger.info(f"pk={pk}, legajo_id={legajo_id}")
            logger.info(f"POST data: {request.POST}")
            logger.info(f"FILES: {request.FILES}")

            # Obtener el legajo
            legajo = get_object_or_404(
                ExpedienteCiudadano, pk=legajo_id, expediente__pk=pk
            )
            logger.info(f"Legajo encontrado: {legajo.pk}")

            # Verificar permisos sobre el expediente asociado
            can_confirm_subsanacion(request.user, legajo.expediente)
            logger.info("Permisos verificados")

            # Verificar que el legajo esté en estado de subsanación
            if legajo.revision_tecnico != "SUBSANAR":
                logger.warning(
                    f"Estado revision_tecnico incorrecto: {legajo.revision_tecnico}"
                )
                return JsonResponse(
                    {
                        "success": False,
                        "error": "El legajo no está en estado de subsanación",
                    }
                )

            comentario = request.POST.get("comentario", "").strip()
            archivo = request.FILES.get("archivo")
            logger.info(f"Comentario: {comentario[:50] if comentario else 'VACIO'}")
            logger.info(f"Archivo: {archivo.name if archivo else 'NO ENVIADO'}")

            if not comentario:
                logger.warning("Comentario vacio")
                return JsonResponse(
                    {"success": False, "error": "El comentario es obligatorio"},
                    status=400,
                )

            # Guardar respuesta
            logger.info("Guardando respuesta...")
            legajo.subsanacion_renaper_comentario = comentario
            legajo.revision_tecnico = "SUBSANADO"

            if archivo:
                logger.info(f"Guardando archivo: {archivo.name}")
                legajo.subsanacion_renaper_archivo = archivo

            legajo.save()
            logger.info("Legajo guardado exitosamente")

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
