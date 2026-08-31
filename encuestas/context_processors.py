from users.profile_utils import get_profile_or_none, needs_profile_confirmation

from .services import get_rondas_pendientes_para_request


def ronda_pendiente(request):
    """Expone la próxima ronda de encuesta pendiente del usuario a todos los
    templates, para que el modal (ver templates/includes/base.html) pueda
    aparecer en cualquier página del sistema.

    Usa el mismo cálculo cacheado por request que EncuestaObligatoriaMiddleware
    (ver services.get_rondas_pendientes_para_request): ambos necesitan las
    mismas rondas pendientes del usuario en el mismo request, y sin compartir
    el resultado cada uno dispararía su propia consulta.

    Si el usuario todavía tiene pendiente el cambio de contraseña obligatorio
    o la confirmación de datos personales, no se muestra el modal: esos dos
    flujos tienen prioridad (ver docstring de EncuestaObligatoriaMiddleware) y
    además ninguno de esos otros middlewares conoce la ruta
    /encuestas/responder/, así que si el modal apareciera igual, el POST de
    "Responder" quedaría interceptado y redirigido antes de llegar a la vista
    -sin guardar nada y sin ningún error visible para el usuario.
    """
    usuario = getattr(request, "user", None)
    if not usuario or not usuario.is_authenticated:
        return {}

    profile = get_profile_or_none(usuario)
    if getattr(profile, "must_change_password", False) or needs_profile_confirmation(
        usuario
    ):
        return {}

    pendientes = get_rondas_pendientes_para_request(request)
    return {"ronda_pendiente": pendientes[0] if pendientes else None}
