"""Ejemplo de uso del servicio de comentarios en views."""

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse

from celiaquia.models import ExpedienteCiudadano, HistorialComentarios
from celiaquia.services.comentarios_service import ComentariosService


@login_required
def agregar_comentario_validacion(request, legajo_id):
    """Ejemplo: Agregar comentario de validación técnica."""
    if request.method == "POST":
        legajo = get_object_or_404(ExpedienteCiudadano, id=legajo_id)
        comentario = request.POST.get("comentario")

        if comentario:
            ComentariosService.agregar_validacion_tecnica(
                legajo=legajo, comentario=comentario, usuario=request.user
            )
            messages.success(request, "Comentario agregado exitosamente")

        return redirect("legajo_detail", legajo_id=legajo_id)


@login_required
def solicitar_subsanacion(request, legajo_id):
    """Ejemplo: Solicitar subsanación con motivo."""
    if request.method == "POST":
        legajo = get_object_or_404(ExpedienteCiudadano, id=legajo_id)
        motivo = request.POST.get("motivo_subsanacion")

        if motivo:
            # Actualizar estado del legajo
            legajo.revision_tecnico = "SUBSANAR"
            legajo.subsanacion_motivo = motivo
            legajo.save()  # Esto disparará el signal automáticamente

            messages.success(request, "Subsanación solicitada exitosamente")

        return redirect("legajo_detail", legajo_id=legajo_id)


@login_required
def responder_subsanacion(request, legajo_id):
    """Ejemplo: Responder a una subsanación."""
    if request.method == "POST":
        legajo = get_object_or_404(ExpedienteCiudadano, id=legajo_id)
        respuesta = request.POST.get("respuesta_subsanacion")
        archivo = request.FILES.get("archivo_respuesta")

        if respuesta:
            ComentariosService.agregar_subsanacion_respuesta(
                legajo=legajo,
                respuesta=respuesta,
                usuario=request.user,
                archivo_adjunto=archivo,
            )

            # Actualizar estado del legajo
            legajo.revision_tecnico = "SUBSANADO"
            legajo.save()

            messages.success(request, "Respuesta de subsanación registrada")

        return redirect("legajo_detail", legajo_id=legajo_id)


@login_required
def obtener_historial_comentarios(request, legajo_id):
    """API: Obtener historial de comentarios de un legajo."""
    legajo = get_object_or_404(ExpedienteCiudadano, id=legajo_id)
    comentarios = ComentariosService.obtener_historial_legajo(legajo)

    data = []
    for comentario in comentarios:
        data.append(
            {
                "id": comentario.id,
                "tipo": comentario.get_tipo_comentario_display(),
                "comentario": comentario.comentario,
                "usuario": (
                    comentario.usuario.username if comentario.usuario else "Sistema"
                ),
                "fecha": comentario.fecha_creacion.strftime("%Y-%m-%d %H:%M"),
                "estado_relacionado": comentario.estado_relacionado,
                "tiene_archivo": bool(comentario.archivo_adjunto),
            }
        )

    return JsonResponse({"comentarios": data})


@login_required
def obtener_comentarios_por_tipo(request, legajo_id, tipo_comentario):
    """API: Obtener comentarios de un tipo específico."""
    legajo = get_object_or_404(ExpedienteCiudadano, id=legajo_id)

    # Validar tipo de comentario
    tipos_validos = [
        choice[0] for choice in HistorialComentarios.TIPO_COMENTARIO_CHOICES
    ]
    if tipo_comentario not in tipos_validos:
        return JsonResponse({"error": "Tipo de comentario inválido"}, status=400)

    comentarios = ComentariosService.obtener_comentarios_por_tipo(
        legajo=legajo, tipo_comentario=tipo_comentario
    )

    data = []
    for comentario in comentarios:
        data.append(
            {
                "id": comentario.id,
                "comentario": comentario.comentario,
                "usuario": (
                    comentario.usuario.username if comentario.usuario else "Sistema"
                ),
                "fecha": comentario.fecha_creacion.strftime("%Y-%m-%d %H:%M"),
                "estado_relacionado": comentario.estado_relacionado,
            }
        )

    return JsonResponse({"comentarios": data})
