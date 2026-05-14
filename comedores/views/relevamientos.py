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


def _get_validation_error_message(error):
    return "; ".join(error.messages) if getattr(error, "messages", None) else str(error)


def _error_response(request, is_ajax, message, status_code, redirect_to, **kwargs):
    if is_ajax:
        return JsonResponse({"error": message}, status=status_code)
    messages.error(request, message)
    return redirect(redirect_to, **kwargs)


def _success_response(request, is_ajax, message, relevamiento):
    if is_ajax:
        url = reverse(
            "relevamiento_detalle",
            kwargs={
                "pk": relevamiento.pk,
                "comedor_pk": relevamiento.comedor.pk,
            },
        )
        return JsonResponse({"url": url}, status=200)

    messages.success(request, message)
    return redirect(
        "relevamiento_detalle",
        pk=relevamiento.pk,
        comedor_pk=relevamiento.comedor.pk,
    )


def _handle_create_pendiente(request, comedor, is_ajax):
    relevamiento = RelevamientoService.create_pendiente(request, comedor.id)
    return _success_response(
        request,
        is_ajax,
        "Relevamiento territorial creado correctamente.",
        relevamiento,
    )


def _handle_update_territorial(request, comedor, is_ajax):
    relevamiento_id = request.POST.get("relevamiento_id")
    if not relevamiento_id:
        return _error_response(
            request,
            is_ajax,
            "Falta relevamiento_id.",
            400,
            "relevamientos",
            comedor_pk=comedor.pk,
        )

    scoped_comedores = ComedorService.get_scoped_comedor_queryset(request.user)
    relevamiento_editar = get_object_or_404(
        Relevamiento.objects.filter(comedor__in=scoped_comedores),
        pk=relevamiento_id,
    )
    if not request.user.has_perm("relevamientos.change_relevamiento"):
        return _error_response(
            request,
            is_ajax,
            "No tiene permisos para asignar territorial al relevamiento.",
            403,
            "relevamiento_detalle",
            pk=relevamiento_editar.pk,
            comedor_pk=relevamiento_editar.comedor.pk,
        )

    try:
        relevamiento = RelevamientoService.update_territorial(request)
    except ValidationError as error:
        return _error_response(
            request,
            is_ajax,
            _get_validation_error_message(error),
            400,
            "relevamiento_detalle",
            pk=relevamiento_editar.pk,
            comedor_pk=relevamiento_editar.comedor.pk,
        )

    return _success_response(
        request,
        is_ajax,
        "Relevamiento territorial actualizado correctamente.",
        relevamiento,
    )


@login_required
@require_POST
def relevamiento_crear_editar_ajax(request, pk):
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
    response = None
    try:
        comedor = _resolve_scoped_comedor_from_pk(pk, request.user)

        if "territorial" in request.POST:
            response = _handle_create_pendiente(request, comedor, is_ajax)
        elif "territorial_editar" in request.POST:
            response = _handle_update_territorial(request, comedor, is_ajax)
        else:
            response = _error_response(
                request,
                is_ajax,
                "Acción no reconocida.",
                400,
                "comedor_detalle",
                pk=pk,
            )
    except ValidationError as error:
        return _error_response(
            request,
            is_ajax,
            _get_validation_error_message(error),
            400,
            "relevamientos",
            comedor_pk=comedor.pk if "comedor" in locals() else pk,
        )
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
