import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.forms import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from comedores.services.comedor_service import ComedorService
from relevamientos.models import Relevamiento
from relevamientos.service import RelevamientoService

logger = logging.getLogger("django")


def _resolve_scoped_comedor_from_pk(pk, user):
    try:
        return ComedorService.get_scoped_comedor_or_404(pk, user)
    except Http404:
        relevamiento = get_object_or_404(
            Relevamiento.objects.select_related("comedor"), pk=pk
        )
        scoped_comedores = ComedorService.get_scoped_comedor_queryset(user)
        return get_object_or_404(scoped_comedores, pk=relevamiento.comedor_id)


@login_required
@require_POST
def relevamiento_crear_editar_ajax(request, pk):
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
    response = None
    try:
        comedor = _resolve_scoped_comedor_from_pk(pk, request.user)

        if "territorial" in request.POST:
            relevamiento = RelevamientoService.create_pendiente(request, comedor.id)
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
            relevamiento_id = request.POST.get("relevamiento_id")
            if not relevamiento_id:
                return JsonResponse({"error": "Falta relevamiento_id"}, status=400)
            scoped_comedores = ComedorService.get_scoped_comedor_queryset(request.user)
            get_object_or_404(
                Relevamiento.objects.filter(comedor__in=scoped_comedores),
                pk=relevamiento_id,
            )
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
    except Http404:
        return JsonResponse({"error": "No encontrado"}, status=404)
    except Exception:
        logger.exception(
            f"Error procesando relevamiento {pk}",
            extra={
                "body": dict(request.POST),
            },
        )
        return JsonResponse({"error": "Error interno"}, status=500)
    return response
