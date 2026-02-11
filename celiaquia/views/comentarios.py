import logging
from django.views import View
from django.http import JsonResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.core.exceptions import PermissionDenied

from celiaquia.models import ExpedienteCiudadano, HistorialComentarios
from celiaquia.permissions import can_review_legajo

logger = logging.getLogger("django")


def _in_group(user, group_name):
    return user.groups.filter(name=group_name).exists()


class LegajoComentarioCreateView(View):
    """Agregar comentario técnico a un legajo"""

    @method_decorator(csrf_protect)
    def post(self, request, expediente_id, legajo_id):
        user = request.user
        
        if not user.is_authenticated:
            return JsonResponse(
                {"success": False, "message": "Autenticación requerida."},
                status=403,
            )

        is_admin = user.is_superuser
        is_coord = _in_group(user, "CoordinadorCeliaquia")
        is_tec = _in_group(user, "TecnicoCeliaquia")

        if not (is_admin or is_coord or is_tec):
            return JsonResponse(
                {"success": False, "message": "Permiso denegado."},
                status=403,
            )

        legajo = get_object_or_404(
            ExpedienteCiudadano, pk=legajo_id, expediente__pk=expediente_id
        )

        # Validar que el técnico esté asignado
        if is_tec and not (is_admin or is_coord):
            if not legajo.expediente.asignaciones_tecnicos.filter(tecnico=user).exists():
                return JsonResponse(
                    {
                        "success": False,
                        "message": "No sos el técnico asignado a este expediente.",
                    },
                    status=403,
                )

        comentario_texto = request.POST.get("comentario", "").strip()
        if not comentario_texto:
            return JsonResponse(
                {"success": False, "message": "El comentario no puede estar vacío."},
                status=400,
            )

        archivo = request.FILES.get("archivo")

        # Crear comentario
        comentario = HistorialComentarios.objects.create(
            legajo=legajo,
            tipo_comentario=HistorialComentarios.TIPO_OBSERVACION_GENERAL,
            comentario=comentario_texto,
            usuario=user,
            archivo_adjunto=archivo,
            estado_relacionado=legajo.revision_tecnico,
        )

        logger.info(
            "Comentario técnico agregado: legajo=%s, usuario=%s",
            legajo.pk,
            user.id,
        )

        return JsonResponse(
            {
                "success": True,
                "message": "Comentario agregado correctamente.",
                "comentario": {
                    "id": comentario.pk,
                    "texto": comentario.comentario,
                    "usuario": user.get_full_name() or user.username,
                    "fecha": comentario.fecha_creacion.strftime("%d/%m/%Y %H:%M"),
                    "tiene_archivo": bool(comentario.archivo_adjunto),
                    "archivo_url": comentario.archivo_adjunto.url if comentario.archivo_adjunto else None,
                    "es_provincia": _in_group(user, "ProvinciaCeliaquia"),
                },
            }
        )

    def get(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(["POST"])


class LegajoComentarioListView(View):
    """Listar comentarios de un legajo"""

    def get(self, request, expediente_id, legajo_id):
        user = request.user
        
        if not user.is_authenticated:
            return JsonResponse(
                {"success": False, "message": "Autenticación requerida."},
                status=403,
            )

        legajo = get_object_or_404(
            ExpedienteCiudadano, pk=legajo_id, expediente__pk=expediente_id
        )

        comentarios = legajo.historial_comentarios.filter(
            tipo_comentario__in=[
                HistorialComentarios.TIPO_OBSERVACION_GENERAL,
                HistorialComentarios.TIPO_VALIDACION_TECNICA,
            ]
        ).order_by("-fecha_creacion")

        data = [
            {
                "id": c.pk,
                "texto": c.comentario,
                "usuario": c.usuario.get_full_name() if c.usuario else "Sistema",
                "fecha": c.fecha_creacion.strftime("%d/%m/%Y %H:%M"),
                "tiene_archivo": bool(c.archivo_adjunto),
                "archivo_url": c.archivo_adjunto.url if c.archivo_adjunto else None,
                "es_provincia": _in_group(c.usuario, "ProvinciaCeliaquia") if c.usuario else False,
            }
            for c in comentarios
        ]

        return JsonResponse({"success": True, "comentarios": data})
