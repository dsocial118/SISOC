from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from comedores.models import CapacitacionComedorCertificado
from comedores.services.capacitaciones_certificados_service import (
    is_alimentar_comunidad_program,
    review_certificate,
    serialize_certificate,
)
from comedores.services.comedor_service import ComedorService


def capacitacion_certificado_estado_ajax(request, pk, certificado_id):
    if request.method != "POST":
        return JsonResponse(
            {"success": False, "error": "Método no permitido."},
            status=405,
        )

    comedor = ComedorService.get_scoped_comedor_or_404(pk, request.user)
    if not is_alimentar_comunidad_program(comedor):
        return JsonResponse(
            {
                "success": False,
                "error": "Capacitaciones no habilitadas para este programa.",
            },
            status=404,
        )
    certificado = get_object_or_404(
        CapacitacionComedorCertificado,
        pk=certificado_id,
        comedor=comedor,
    )
    estado = (request.POST.get("estado") or "").strip()
    observacion = request.POST.get("observacion")

    try:
        review_certificate(certificado, estado, request.user, observacion=observacion)
    except ValidationError as exc:
        if hasattr(exc, "message_dict"):
            detail = exc.message_dict
        elif hasattr(exc, "messages"):
            detail = exc.messages
        else:
            detail = str(exc)
        return JsonResponse({"success": False, "error": detail}, status=400)

    return JsonResponse(
        {
            "success": True,
            "item": serialize_certificate(certificado, request=request),
        },
        status=200,
    )
