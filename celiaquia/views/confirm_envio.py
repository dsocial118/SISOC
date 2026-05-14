# celiaquia/views/confirm_envio.py
"""Views for confirming expediente submission."""

import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.http import HttpResponseNotAllowed, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View

from celiaquia.models import Expediente, RegistroErroneo
from celiaquia.services.expediente_service import ExpedienteService
from celiaquia.services.legajo_service import LegajoService
from celiaquia.views.expediente import _is_ajax

logger = logging.getLogger("django")


class ExpedienteConfirmView(LoginRequiredMixin, View):
    """
    POST: confirma el envio del expediente (provincia). Responde JSON.
    - Si faltan archivos => 400 con mensaje (o messages.error si no es AJAX).
    - Si no tiene permisos => 403 con mensaje.
    - Nunca 404 por reglas de negocio.
    """

    def post(self, request, pk: int):
        expediente = get_object_or_404(
            Expediente.objects.select_related(
                "usuario_provincia", "usuario_provincia__profile"
            ),
            pk=pk,
        )

        user = request.user
        same_owner = user == expediente.usuario_provincia

        def _prov_id(usuario):
            try:
                return getattr(getattr(usuario, "profile", None), "provincia_id", None)
            except Exception:
                return None

        same_province = (
            _prov_id(user)
            and _prov_id(expediente.usuario_provincia)
            and _prov_id(user) == _prov_id(expediente.usuario_provincia)
        )

        if not (user.is_staff or same_owner or same_province):
            msg = "No tiene permisos para confirmar este expediente."
            return JsonResponse({"success": False, "error": msg}, status=403)

        if expediente.estado.nombre != "EN_ESPERA":
            msg = (
                "El expediente no esta en estado EN_ESPERA. "
                f"Estado actual: {expediente.estado.nombre}"
            )
            logger.info("Validacion en confirmar envio fallo: %s", msg)
            if _is_ajax(request):
                return JsonResponse({"success": False, "error": msg}, status=400)
            messages.error(request, msg)
            return redirect("expediente_detail", pk=expediente.pk)

        registros_erroneos = RegistroErroneo.objects.filter(
            expediente=expediente, procesado=False
        )
        if registros_erroneos.exists():
            msg = (
                "No se puede confirmar el envio: hay "
                f"{registros_erroneos.count()} registros con errores pendientes."
            )
            logger.info("Validacion en confirmar envio fallo: %s", msg)
            if _is_ajax(request):
                return JsonResponse({"success": False, "error": msg}, status=400)
            messages.error(request, msg)
            return redirect("expediente_detail", pk=expediente.pk)

        faltantes = LegajoService.faltantes_archivos(expediente, limit=10)
        if faltantes:
            ejemplos = [
                (
                    f"{item['apellido']}, {item['nombre']} (DNI {item['documento']})"
                    f" - faltan: {', '.join(item['faltan_nombres'])}"
                )
                for item in faltantes
            ]
            msg = (
                "No podes confirmar el envio: hay legajos sin toda la documentacion "
                "obligatoria segun su tipo de ciudadano. "
                + (
                    "Ejemplos: "
                    + "; ".join(ejemplos)
                    + (" ..." if len(faltantes) >= 10 else "")
                )
            )
            logger.info("Validacion en confirmar envio fallo: %s", msg)

            if _is_ajax(request):
                return JsonResponse(
                    {
                        "success": False,
                        "error": msg,
                        "faltantes_ids": [item["legajo_id"] for item in faltantes],
                    },
                    status=400,
                )
            messages.error(request, msg)
            return redirect("expediente_detail", pk=expediente.pk)

        try:
            result = ExpedienteService.confirmar_envio(expediente, request.user)
            logger.info(
                "Confirmacion de envio OK. Expediente %s por %s",
                expediente.pk,
                request.user.username,
            )
            return JsonResponse(
                {
                    "success": True,
                    "message": "Expediente enviado a Subsecretaria.",
                    "estado": expediente.estado.display_name(),
                    "datos": result,
                }
            )
        except ValidationError as exc:
            logger.warning(
                "Validacion en confirmar envio fallo: %s", exc, exc_info=True
            )
            if getattr(exc, "messages", None):
                error_msg = "; ".join(
                    str(message) for message in exc.messages if message
                )
            elif getattr(exc, "message", None):
                error_msg = str(exc.message)
            else:
                error_msg = str(exc)
            return JsonResponse({"success": False, "error": error_msg}, status=400)
        except Exception as exc:
            logger.error("Error inesperado al confirmar envio: %s", exc, exc_info=True)
            return JsonResponse(
                {
                    "success": False,
                    "error": "No se pudo confirmar el envio. Revisa los datos e intenta de nuevo.",
                },
                status=500,
            )

    def get(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(["POST"])
