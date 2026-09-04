import logging
from django.views import View
from django.http import JsonResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from celiaquia.models import ExpedienteCiudadano, HistorialComentarios
from celiaquia.services.comentarios_tecnicos_service import ComentariosTecnicosService
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


ALLOWED_UPLOAD_TYPES = {"application/pdf", "image/jpeg", "image/png"}
MAX_UPLOAD_MB = 5

#: Tipos de comentario que se listan en el panel del legajo.
TIPOS_LISTABLES = [
    HistorialComentarios.TIPO_OBSERVACION_GENERAL,
    HistorialComentarios.TIPO_VALIDACION_TECNICA,
    HistorialComentarios.TIPO_COMENTARIO_TECNICO,
]


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


def _resolver_legajo_para_nacion(request, expediente_id, legajo_id):
    """Valida que el usuario sea Nación con acceso al legajo.

    Devuelve ``(legajo, None)`` cuando puede operar, o ``(None, JsonResponse)``
    con el error a devolver. Centraliza el chequeo que comparten las tres vistas
    de comentarios técnicos.
    """
    user = request.user

    if not user.is_authenticated:
        return None, JsonResponse(
            {"success": False, "message": "Autenticación requerida."}, status=403
        )

    # El perfil territorial define a un usuario de Provincia, aun cuando por
    # configuración acumule permisos de Nación. Estos endpoints crean o
    # anticipan comentarios internos, por lo que no deben exponerlos antes de
    # su publicación durante Subsanar/Rechazar.
    if is_territorial_user(user):
        return None, JsonResponse(
            {"success": False, "message": "Permiso denegado."}, status=403
        )

    is_admin = user.is_superuser
    is_coord = _has_permission(user, ROLE_COORDINADOR_CELIAQUIA_PERMISSION)
    is_tec = _has_permission(user, ROLE_TECNICO_CELIAQUIA_PERMISSION)

    if not (is_admin or is_coord or is_tec):
        return None, JsonResponse(
            {"success": False, "message": "Permiso denegado."}, status=403
        )

    legajo = get_object_or_404(
        ExpedienteCiudadano, pk=legajo_id, expediente__pk=expediente_id
    )

    # Validar que el técnico esté asignado
    if is_tec and not (is_admin or is_coord):
        if not legajo.expediente.asignaciones_tecnicos.filter(tecnico=user).exists():
            return None, JsonResponse(
                {
                    "success": False,
                    "message": "No sos el técnico asignado a este expediente.",
                },
                status=403,
            )

    return legajo, None


def _es_autor_provincial(usuario) -> bool:
    """True si el comentario lo escribió un usuario provincial.

    No alcanza con mirar el permiso de rol: un superusuario los tiene todos y
    quedaría etiquetado como Provincia. El alcance territorial es lo que
    distingue de verdad a un usuario provincial, y es el mismo criterio con el
    que se decide qué comentarios recibe.
    """
    return bool(usuario) and is_territorial_user(usuario)


def _deduplicar_para_provincia(comentarios):
    """Quita las observaciones técnicas repetidas, conservando el resto.

    El técnico puede registrar la misma observación más de una vez y el
    historial interno las conserva todas, pero a la Provincia se le muestra una
    sola vez cada una. La lista vuelve ordenada de más nueva a más vieja."""
    tecnicos = [c for c in comentarios if c.es_comentario_tecnico]
    resto = [c for c in comentarios if not c.es_comentario_tecnico]
    return sorted(
        resto + ComentariosTecnicosService.deduplicar(tecnicos),
        key=lambda c: c.fecha_creacion,
        reverse=True,
    )


def _serializar_comentario(comentario, es_provincia=None):
    """Representación JSON de un comentario del panel del legajo."""
    if es_provincia is None:
        es_provincia = _es_autor_provincial(comentario.usuario)
    return {
        "id": comentario.pk,
        "texto": comentario.comentario,
        "usuario": (
            comentario.usuario.get_full_name() or comentario.usuario.username
            if comentario.usuario
            else "Sistema"
        ),
        "fecha": comentario.fecha_creacion.strftime("%d/%m/%Y %H:%M"),
        "tiene_archivo": bool(comentario.archivo_adjunto),
        "archivo_url": (
            comentario.archivo_adjunto.url if comentario.archivo_adjunto else None
        ),
        "es_provincia": es_provincia,
        "es_interno": comentario.es_interno,
        # Campos del comentario técnico estructurado (nulos en el resto).
        "es_comentario_tecnico": comentario.es_comentario_tecnico,
        "tipo_documento": comentario.tipo_documento,
        "tipo_documento_display": comentario.get_tipo_documento_display(),
        "tiene_observaciones": comentario.tiene_observaciones,
        "observacion_codigo": comentario.observacion_codigo,
        "publicado_en": (
            comentario.publicado_en.strftime("%d/%m/%Y %H:%M")
            if comentario.publicado_en
            else None
        ),
    }


class LegajoComentarioCreateView(View):
    """Agregar comentario técnico a un legajo.

    Acepta dos formatos: el comentario técnico estructurado del issue #2318
    (cuando llega `tipo_documento`) y el comentario libre previo, que se
    conserva para no romper a los consumidores existentes del endpoint.
    """

    @method_decorator(csrf_protect)
    def post(self, request, expediente_id, legajo_id):
        legajo, error = _resolver_legajo_para_nacion(request, expediente_id, legajo_id)
        if error:
            return error

        if (request.POST.get("tipo_documento") or "").strip():
            return self._crear_comentario_tecnico(request, legajo)
        return self._crear_comentario_libre(request, legajo)

    def _crear_comentario_tecnico(self, request, legajo):
        """Alta estructurada: tipo de documento + Sí/No + observación."""
        try:
            comentario = ComentariosTecnicosService.registrar(
                legajo,
                tipo_documento=request.POST.get("tipo_documento"),
                tiene_observaciones=request.POST.get("tiene_observaciones"),
                observacion_codigo=request.POST.get("observacion_codigo"),
                observacion_libre=request.POST.get("observacion_libre", ""),
                usuario=request.user,
            )
        except ValidationError as exc:
            return JsonResponse(
                {"success": False, "message": "; ".join(exc.messages)}, status=400
            )

        return JsonResponse(
            {
                "success": True,
                "message": "Comentario técnico guardado correctamente.",
                "comentario": _serializar_comentario(comentario, es_provincia=False),
            }
        )

    def _crear_comentario_libre(self, request, legajo):
        """Alta previa al issue #2318: texto libre con archivo opcional."""
        user = request.user
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
                "comentario": _serializar_comentario(
                    comentario, es_provincia=_es_autor_provincial(user)
                ),
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
            tipo_comentario__in=TIPOS_LISTABLES
        )

        # Los comentarios internos solo son visibles para Nación. Un usuario
        # territorial (provincial) nunca los recibe, aún si por configuración
        # tuviera además algún rol de Nación.
        es_nacion = (is_admin or is_coord or is_tec) and not is_territorial_user(user)
        if not es_nacion:
            comentarios_qs = comentarios_qs.filter(es_interno=False)

        comentarios = list(
            comentarios_qs.select_related("usuario")
            .prefetch_related("usuario__groups")
            .order_by("-fecha_creacion")
        )

        # Nación ve el historial completo, incluidas las observaciones repetidas.
        # A la Provincia se le muestra una sola vez cada observación publicada.
        if not es_nacion:
            comentarios = _deduplicar_para_provincia(comentarios)

        data = [_serializar_comentario(c) for c in comentarios]

        return JsonResponse({"success": True, "comentarios": data})


class LegajoMotivoPreviewView(View):
    """Previsualización del motivo de Subsanar/Rechazar.

    Devuelve la concatenación de las observaciones técnicas del legajo para que
    los modales la muestren. Es solo una vista previa: al confirmar, el motivo
    se vuelve a calcular en el backend (`RevisarLegajoView`), que es la fuente
    de verdad.
    """

    def get(self, request, expediente_id, legajo_id):
        legajo, error = _resolver_legajo_para_nacion(request, expediente_id, legajo_id)
        if error:
            return error

        lineas = ComentariosTecnicosService.lineas_concatenadas(legajo)
        return JsonResponse(
            {
                "success": True,
                "lineas": lineas,
                "motivo": ComentariosTecnicosService.texto_concatenado(legajo),
                "tiene_observaciones": bool(lineas),
            }
        )
