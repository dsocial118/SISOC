"""
celiaquia/views/confirm_envio.py

Breve descripción:
- Endpoint POST que usa la Provincia para "Confirmar Envío" del expediente.
- Valida en el servidor que:
  1) El expediente pertenezca al usuario autenticado (provincia).
  2) El estado actual sea EN_ESPERA.
  3) Todos los legajos tengan archivo cargado.
- Si todo ok, cambia el estado a CONFIRMACION_DE_ENVIO.

Estados y flujos impactados:
- EN_ESPERA → CONFIRMACION_DE_ENVIO (Provincia pasa a solo lectura).

Dependencias:
- services/expediente_service.py: ExpedienteService.confirmar_envio(expediente)
- services/legajo_service.py: LegajoService.all_legajos_loaded(expediente)
- urls.py: ruta 'expediente_confirm' ya mapea a esta vista
- static/custom/js/expediente_detail.js: dispara fetch POST y espera JSON

Mensajes y errores:
- Devuelve JSON con {"success": True/False, ...}
- ValidationError → 400 con mensaje claro
- Errores inesperados → 500 con mensaje genérico y logger.error
"""

import logging
from django.views import View
from django.http import JsonResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from django.contrib.auth.mixins import LoginRequiredMixin

from celiaquia.models import Expediente
from celiaquia.services.expediente_service import ExpedienteService

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
            # 2) Ejecutar validaciones y transición de estado
            result = ExpedienteService.confirmar_envio(expediente)
            logger.info(
                "Confirmación de envío OK. Expediente %s por %s",
                expediente.codigo,
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
