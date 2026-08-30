from .services import get_rondas_pendientes_para_request


def ronda_pendiente(request):
    """Expone la próxima ronda de encuesta pendiente del usuario a todos los
    templates, para que el modal (ver templates/includes/base.html) pueda
    aparecer en cualquier página del sistema.

    Usa el mismo cálculo cacheado por request que EncuestaObligatoriaMiddleware
    (ver services.get_rondas_pendientes_para_request): ambos necesitan las
    mismas rondas pendientes del usuario en el mismo request, y sin compartir
    el resultado cada uno dispararía su propia consulta.
    """
    usuario = getattr(request, "user", None)
    if not usuario or not usuario.is_authenticated:
        return {}

    pendientes = get_rondas_pendientes_para_request(request)
    return {"ronda_pendiente": pendientes[0] if pendientes else None}
