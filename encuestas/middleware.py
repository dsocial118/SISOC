from django.shortcuts import redirect
from django.urls import NoReverseMatch, reverse

from users.middleware import COMMON_EXEMPT_PATHS, COMMON_EXEMPT_PREFIXES

from .services import get_rondas_pendientes_para_request

# El modal de encuesta obligatoria (templates/encuestas/partials/responder_modal.html)
# se muestra en cualquier página vía context processor, así que no hace falta
# una ruta dedicada como password_change_required/confirmar_datos_personales:
# alcanza con eximir el propio endpoint de respuesta y mandar todo lo demás a
# 'inicio', que ya trae el modal puesto.
ENCUESTAS_EXEMPT_PREFIXES = ("/encuestas/responder/",)


class EncuestaObligatoriaMiddleware:
    """Bloquea la navegación mientras el usuario tenga una ronda obligatoria
    sin responder.

    Mismo patrón que ``FirstLoginPasswordChangeMiddleware`` y
    ``ProfileConfirmationMiddleware`` (users/middleware.py). Se registra
    después de ambos a propósito: contraseña y datos personales pendientes
    tienen prioridad sobre responder una encuesta.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if (
            user
            and getattr(user, "is_authenticated", False)
            and not self._is_exempt_path(request)
            and self._tiene_ronda_obligatoria_pendiente(request)
        ):
            return redirect("inicio")

        return self.get_response(request)

    @staticmethod
    def _tiene_ronda_obligatoria_pendiente(request) -> bool:
        return any(
            ronda.encuesta.es_obligatoria
            for ronda in get_rondas_pendientes_para_request(request)
        )

    @staticmethod
    def _is_exempt_path(request):
        path = request.path
        # Contraseña y datos personales pendientes tienen prioridad sobre
        # responder una encuesta (ver docstring de la clase): hay que eximir
        # sus rutas acá también, no solo la del propio middleware que las
        # redirige, o se arma un loop de redirects entre ese middleware y
        # este (mismo motivo por el que ProfileConfirmationMiddleware exime
        # "/password/first-change/" en users/middleware.py).
        exempt_paths = set(COMMON_EXEMPT_PATHS) | {"/password/first-change/"}
        try:
            exempt_paths.add(reverse("confirmar_datos_personales"))
        except NoReverseMatch:
            exempt_paths.add("/mi-cuenta/confirmar/")
        if path in exempt_paths:
            return True
        if path.startswith(COMMON_EXEMPT_PREFIXES) or path.startswith(
            ENCUESTAS_EXEMPT_PREFIXES
        ):
            return True
        if path.startswith("/encuestas/") and request.user.has_perm(
            "encuestas.change_encuesta"
        ):
            return True
        try:
            return path == reverse("inicio")
        except NoReverseMatch:
            return False
