import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms import ValidationError
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from relevamientos.service import RelevamientoService

logger = logging.getLogger("django")


@login_required
@require_POST
def relevamiento_crear_editar_ajax(request, pk):
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
    response = None
    try:
        if "territorial" in request.POST:
            relevamiento = RelevamientoService.create_pendiente(request, pk)
            if is_ajax:
                url = reverse(
                    "relevamiento_detalle",
                    kwargs={
                        "pk": relevamiento.pk,
                        "comedor_pk": relevamiento.comedor.pk,
                    },
                )
                response = JsonResponse({"url": url}, status=200)
            else:
                messages.success(
                    request, "Relevamiento territorial creado correctamente."
                )
                response = redirect(
                    "relevamiento_detalle",
                    pk=relevamiento.pk,
                    comedor_pk=relevamiento.comedor.pk,
                )
        elif "territorial_editar" in request.POST:
            relevamiento = RelevamientoService.update_territorial(request)
            if is_ajax:
                response = JsonResponse(
                    {
                        "url": f"/comedores/{relevamiento.comedor.pk}/relevamiento/{relevamiento.pk}"
                    },
                    status=200,
                )
            else:
                messages.success(
                    request, "Relevamiento territorial actualizado correctamente."
                )
                response = redirect(
                    "relevamiento_detalle",
                    pk=relevamiento.pk,
                    comedor_pk=relevamiento.comedor.pk,
                )
        else:
            if is_ajax:
                response = JsonResponse({"error": "Acción no reconocida"}, status=400)
            else:
                messages.error(request, "Acción no reconocida.")
                response = redirect("comedor_detalle", pk=pk)
    except ValidationError as e:
        return JsonResponse({"error": e.message}, status=400)
    except Exception:
        logger.exception(
            f"Error procesando relevamiento {pk}",
            extra={
                "body": dict(request.POST),
            },
        )
        return JsonResponse({"error": "Error interno"}, status=500)
    return response
