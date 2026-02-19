from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.views.decorators.http import require_POST

from comedores.services.validacion_service import ValidacionService
from core.security import safe_redirect


@login_required
@require_POST
def validar_comedor(request, pk):
    accion = request.POST.get("accion")
    comentario = request.POST.get("comentario", "")
    opciones = request.POST.getlist("opciones") if accion == "no_validar" else None
    next_url = request.POST.get("next") or request.GET.get("next")

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

    return safe_redirect(
        request,
        default=reverse("comedor_detalle", kwargs={"pk": pk}),
        target=next_url,
    )
