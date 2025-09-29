# celiaquia/views/confirm_envio.py
"""Views for confirming expediente submission."""

import logging

from django.contrib import messages  # ✅ import correcto
from django.views import View
from django.http import JsonResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect
from django.core.exceptions import ValidationError
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q

from celiaquia.models import Expediente, ExpedienteCiudadano
from celiaquia.services.expediente_service import ExpedienteService
from celiaquia.views.expediente import _is_ajax

logger = logging.getLogger(__name__)


class ExpedienteConfirmView(LoginRequiredMixin, View):
    """
    POST: confirma el envío del expediente (provincia). Responde JSON.
    - Si faltan archivos => 400 con mensaje (o messages.error si no es AJAX).
    - Si no tiene permisos => 403 con mensaje.
    - Nunca 404 por reglas de negocio.
    """

    def post(self, request, pk: int):
        # 1) Traer el expediente por PK (sin filtrar por usuario para evitar 404 falsos)
        expediente = get_object_or_404(
            Expediente.objects.select_related(
                "usuario_provincia", "usuario_provincia__profile"
            ),
            pk=pk,
        )

        # 2) Chequeo de permisos: dueño, misma provincia o staff
        user = request.user
        same_owner = user == expediente.usuario_provincia

        def _prov_id(u):
            try:
                return getattr(getattr(u, "profile", None), "provincia_id", None)
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

        # 3) Validación de negocio: todos los legajos con los 2 archivos requeridos
        faltantes_qs = (
            ExpedienteCiudadano.objects.select_related("ciudadano")
            .filter(expediente_id=expediente.pk)
            .filter(
                Q(archivo2__isnull=True)
                | Q(archivo2="")
                | Q(archivo3__isnull=True)
                | Q(archivo3="")
            )
        )

        if faltantes_qs.exists():
            ejemplos = [
                f"{l.ciudadano.apellido}, {l.ciudadano.nombre} (DNI {l.ciudadano.documento})"
                for l in faltantes_qs[:10]
            ]
            msg = (
                "No podés confirmar el envío: hay legajos sin los 2 archivos requeridos. "
                + (
                    "Ejemplos: "
                    + "; ".join(ejemplos)
                    + (" …" if faltantes_qs.count() > 10 else "")
                )
            )
            logger.info("Validación en confirmar envío falló: %s", msg)

            if _is_ajax(request):
                return JsonResponse(
                    {
                        "success": False,
                        "error": msg,
                        "faltantes_ids": list(
                            faltantes_qs.values_list("id", flat=True)
                        ),
                    },
                    status=400,
                )
            messages.error(request, msg)
            return redirect("expediente_detail", pk=expediente.pk)

        # 4) Transición de estado / lógica de confirmación
        try:
            result = ExpedienteService.confirmar_envio(expediente, request.user)
            logger.info(
                "Confirmación de envío OK. Expediente %s por %s",
                expediente.pk,
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
            logger.warning("Validación en confirmar envío falló: %s", e, exc_info=True)
            msg = "No se pudo confirmar el envío: revise los datos e intente de nuevo."
            return JsonResponse({"success": False, "error": msg}, status=400)
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
