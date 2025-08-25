import logging
from pyexpat.errors import messages
from django.views import View
from django.http import JsonResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect
from django.core.exceptions import ValidationError
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from celiaquia.models import Expediente
from celiaquia.services.expediente_service import ExpedienteService
from celiaquia.views.expediente import _is_ajax

logger = logging.getLogger(__name__)


class ExpedienteConfirmView(LoginRequiredMixin, View):
    """POST: confirma el envío del expediente (provincia). Responde JSON."""

    def post(self, request, pk):
        # 1) Traer expediente del usuario provincia (pertenencia)
        expediente = get_object_or_404(
            Expediente,
            pk=pk,
            usuario_provincia=request.user,
        )
        try:
            # Validación: todos los legajos con los 3 archivos
            faltantes_qs = expediente.expediente_ciudadanos.filter(
                Q(archivo1__isnull=True) | Q(archivo2__isnull=True) | Q(archivo3__isnull=True)
            )
            if faltantes_qs.exists():
                # Armamos un mensaje breve + devolvemos ids por si el front quiere resaltar
                ejemplos = [
                    f"{l.ciudadano.apellido}, {l.ciudadano.nombre} (DNI {l.ciudadano.documento})"
                    for l in faltantes_qs.select_related("ciudadano")[:10]
                ]
                msg = (
                    "No podés confirmar el envío: hay legajos sin los 3 archivos. "
                    + "Ejemplos: " + "; ".join(ejemplos)
                    + (" …" if faltantes_qs.count() > 10 else "")
                )

                if _is_ajax(request):
                    return JsonResponse(
                        {
                            "success": False,
                            "error": msg,
                            "faltantes_ids": list(faltantes_qs.values_list("id", flat=True)),
                        },
                        status=400,
                    )
                messages.error(request, msg)
                return redirect("expediente_detail", pk=pk)

            # 2) Ejecutar validaciones y transición de estado
            result = ExpedienteService.confirmar_envio(expediente)
            logger.info(
                "Confirmación de envío OK. Expediente por %s",
                
                request.user.username,
            )
            return JsonResponse(
                {
                    "success": True,
                    "message": "Expediente enviado a Subsecretaría.",
                    "estado": expediente.estado.display_name(),
                    "datos": result,
                }
            )
        except ValidationError as e:
            logger.warning("Validación en confirmar envío falló: %s", e)
            return JsonResponse({"success": False, "error": str(e)}, status=400)
        except Exception as e:
            logger.error("Error inesperado al confirmar envío: %s", e, exc_info=True)
            return JsonResponse(
                {
                    "success": False,
                    "error": "Ocurrió un error inesperado al confirmar el envío.",
                },
                status=500,
            )

    def get(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(["POST"])
