import logging
from django.views import View
from django.http import JsonResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.core.exceptions import ObjectDoesNotExist

from celiaquia.models import ExpedienteCiudadano, HistorialComentarios

logger = logging.getLogger("django")


def _in_group(user, group_name):
    return bool(user) and user.is_authenticated and user.groups.filter(name=group_name).exists()


def _safe_profile(user):
    if not user:
        return None
    try:
        return user.profile
    except ObjectDoesNotExist:
        return None


def _user_has_group_cached(user, group_name):
    if not user:
        return False
    return any(group.name == group_name for group in user.groups.all())


ALLOWED_UPLOAD_TYPES = {"application/pdf", "image/jpeg", "image/png"}
MAX_UPLOAD_MB = 5


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
        if archivo:
            if archivo.content_type not in ALLOWED_UPLOAD_TYPES:
                return JsonResponse(
                    {"success": False, "message": "Tipo de archivo inválido."},
                    status=400,
                )
            if archivo.size > MAX_UPLOAD_MB * 1024 * 1024:
                return JsonResponse(
                    {"success": False, "message": "Archivo demasiado grande."},
                    status=400,
                )

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

        is_admin = user.is_superuser
        is_coord = _in_group(user, "CoordinadorCeliaquia")
        is_tec = _in_group(user, "TecnicoCeliaquia")
        is_prov = _in_group(user, "ProvinciaCeliaquia")

        if not (is_admin or is_coord or is_tec or is_prov):
            return JsonResponse(
                {"success": False, "message": "Permiso denegado."},
                status=403,
            )

        legajo = get_object_or_404(
            ExpedienteCiudadano, pk=legajo_id, expediente__pk=expediente_id
        )

        # Técnico: debe estar asignado
        if is_tec and not (is_admin or is_coord):
            if not legajo.expediente.asignaciones_tecnicos.filter(tecnico=user).exists():
                return JsonResponse(
                    {
                        "success": False,
                        "message": "No sos el técnico asignado a este expediente.",
                    },
                    status=403,
                )

        # Provincia: debe pertenecer a la misma provincia
        if is_prov and not (is_admin or is_coord):
            owner = getattr(legajo.expediente, "usuario_provincia", None)
            up = _safe_profile(user)
            op = _safe_profile(owner) if owner else None
            if (
                not owner
                or not up
                or not op
                or getattr(up, "provincia_id", None) != getattr(op, "provincia_id", None)
            ):
                return JsonResponse(
                    {
                        "success": False,
                        "message": "No pertenece a la misma provincia del expediente.",
                    },
                    status=403,
                )

        comentarios = legajo.historial_comentarios.filter(
            tipo_comentario__in=[
                HistorialComentarios.TIPO_OBSERVACION_GENERAL,
                HistorialComentarios.TIPO_VALIDACION_TECNICA,
            ]
        ).select_related("usuario").prefetch_related("usuario__groups").order_by(
            "-fecha_creacion"
        )

        data = [
            {
                "id": c.pk,
                "texto": c.comentario,
                "usuario": c.usuario.get_full_name() if c.usuario else "Sistema",
                "fecha": c.fecha_creacion.strftime("%d/%m/%Y %H:%M"),
                "tiene_archivo": bool(c.archivo_adjunto),
                "archivo_url": c.archivo_adjunto.url if c.archivo_adjunto else None,
                "es_provincia": _user_has_group_cached(c.usuario, "ProvinciaCeliaquia"),
            }
            for c in comentarios
        ]

        return JsonResponse({"success": True, "comentarios": data})
