import logging
from django.views import View
from django.http import JsonResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.core.exceptions import ObjectDoesNotExist

from celiaquia.models import ExpedienteCiudadano, HistorialComentarios
from iam.services import user_has_permission_code
from users.territorial_scope import is_territorial_user, user_can_access_territory

logger = logging.getLogger("django")
ROLE_COORDINADOR_CELIAQUIA_PERMISSION = "auth.role_coordinadorceliaquia"
ROLE_TECNICO_CELIAQUIA_PERMISSION = "auth.role_tecnicoceliaquia"
ROLE_PROVINCIA_CELIAQUIA_PERMISSION = "auth.role_provinciaceliaquia"


def _has_permission(user, permission_code):
    return user_has_permission_code(user, permission_code)


def _safe_profile(user):
    if not user:
        return None
    try:
        return user.profile
    except (AttributeError, ObjectDoesNotExist):
        return None


def _user_has_permission_cached(user, permission_code):
    if not user:
        return False
    return user_has_permission_code(user, permission_code)


ALLOWED_UPLOAD_TYPES = {"application/pdf", "image/jpeg", "image/png"}
MAX_UPLOAD_MB = 5


def _provincia_can_access_comment_legajo(user, legajo) -> bool:
    if not is_territorial_user(user):
        return False

    owner = getattr(legajo.expediente, "usuario_provincia", None)
    ciudadano = getattr(legajo, "ciudadano", None)
    territorio = {
        "provincia_id": getattr(ciudadano, "provincia_id", None),
        "municipio_id": getattr(ciudadano, "municipio_id", None),
        "localidad_id": getattr(ciudadano, "localidad_id", None),
    }
    if any(value is not None for value in territorio.values()):
        return user_can_access_territory(user, **territorio, owner=owner)

    owner_profile = _safe_profile(owner)
    owner_provincia_id = getattr(owner_profile, "provincia_id", None)
    if owner_provincia_id is None:
        return True
    return user_can_access_territory(
        user,
        provincia_id=owner_provincia_id,
        owner=owner,
    )


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
        is_coord = _has_permission(user, ROLE_COORDINADOR_CELIAQUIA_PERMISSION)
        is_tec = _has_permission(user, ROLE_TECNICO_CELIAQUIA_PERMISSION)

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
            if not legajo.expediente.asignaciones_tecnicos.filter(
                tecnico=user
            ).exists():
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

        # Comentario interno: visible solo para Nación. Solo usuarios de Nación
        # llegan a esta vista (provincia no puede crear comentarios).
        es_interno = str(request.POST.get("es_interno", "")).strip().lower() in {
            "1",
            "true",
            "on",
            "yes",
        }

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
            es_interno=es_interno,
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
                    "archivo_url": (
                        comentario.archivo_adjunto.url
                        if comentario.archivo_adjunto
                        else None
                    ),
                    "es_provincia": _has_permission(
                        user, ROLE_PROVINCIA_CELIAQUIA_PERMISSION
                    ),
                    "es_interno": comentario.es_interno,
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
        is_coord = _has_permission(user, ROLE_COORDINADOR_CELIAQUIA_PERMISSION)
        is_tec = _has_permission(user, ROLE_TECNICO_CELIAQUIA_PERMISSION)
        is_prov = _has_permission(user, ROLE_PROVINCIA_CELIAQUIA_PERMISSION)

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
            if not legajo.expediente.asignaciones_tecnicos.filter(
                tecnico=user
            ).exists():
                return JsonResponse(
                    {
                        "success": False,
                        "message": "No sos el técnico asignado a este expediente.",
                    },
                    status=403,
                )

        # Provincia: debe pertenecer a la misma provincia
        if is_prov and not (is_admin or is_coord):
            if not _provincia_can_access_comment_legajo(user, legajo):
                return JsonResponse(
                    {
                        "success": False,
                        "message": "No pertenece al alcance territorial del expediente.",
                    },
                    status=403,
                )

        comentarios_qs = legajo.historial_comentarios.filter(
            tipo_comentario__in=[
                HistorialComentarios.TIPO_OBSERVACION_GENERAL,
                HistorialComentarios.TIPO_VALIDACION_TECNICA,
            ]
        )

        # Los comentarios internos solo son visibles para Nación. Un usuario
        # provincial (sin rol de Nación) nunca los recibe.
        es_nacion = is_admin or is_coord or is_tec
        if not es_nacion:
            comentarios_qs = comentarios_qs.filter(es_interno=False)

        comentarios = (
            comentarios_qs.select_related("usuario")
            .prefetch_related("usuario__groups")
            .order_by("-fecha_creacion")
        )

        data = [
            {
                "id": c.pk,
                "texto": c.comentario,
                "usuario": c.usuario.get_full_name() if c.usuario else "Sistema",
                "fecha": c.fecha_creacion.strftime("%d/%m/%Y %H:%M"),
                "tiene_archivo": bool(c.archivo_adjunto),
                "archivo_url": c.archivo_adjunto.url if c.archivo_adjunto else None,
                "es_provincia": _user_has_permission_cached(
                    c.usuario,
                    ROLE_PROVINCIA_CELIAQUIA_PERMISSION,
                ),
                "es_interno": c.es_interno,
            }
            for c in comentarios
        ]

        return JsonResponse({"success": True, "comentarios": data})
