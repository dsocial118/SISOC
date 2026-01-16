from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from comedores.services.validacion_service import ValidacionService


@login_required
@require_POST
def validar_comedor(request, pk):
    accion = request.POST.get("accion")
    comentario = request.POST.get("comentario", "")
    opciones = request.POST.getlist("opciones") if accion == "no_validar" else None

    success, mensaje = ValidacionService.validar_comedor(
        comedor_id=pk,
        user=request.user,
        accion=accion,
        opciones=opciones,
        comentario=comentario,
    )

    if success:
        messages.success(request, mensaje)
    else:
        messages.error(request, mensaje)

    return redirect("comedor_detalle", pk=pk)
