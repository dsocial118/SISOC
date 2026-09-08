from django.shortcuts import redirect
from django.urls import reverse, NoReverseMatch

from users.profile_utils import get_profile_or_none, needs_profile_confirmation


COMMON_EXEMPT_PATHS = {
    "/logout",
    "/logout/",
    "/api/users/login/",
    "/api/users/logout/",
    "/api/users/password-reset/request/",
    "/api/users/password-reset/confirm/",
}

COMMON_EXEMPT_PREFIXES = (
    "/static/",
    "/media/",
    "/api/",
    "/password_reset/",
    "/reset/",
    "/password/reset/confirm/",
)


def _is_login_path(path):
    try:
        login_path = reverse("login")
    except NoReverseMatch:
        return False
    return bool(login_path and login_path != "/" and path == login_path)


class FirstLoginPasswordChangeMiddleware:
    """Redirige a cambio de contraseña obligatorio en primer ingreso web."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user and getattr(user, "is_authenticated", False):
            profile = get_profile_or_none(user)
            must_change = bool(getattr(profile, "must_change_password", False))
            if must_change and not self._is_exempt_path(request.path):
                return redirect("password_change_required")

        return self.get_response(request)

    @staticmethod
    def _is_exempt_path(path):
        exempt_paths = COMMON_EXEMPT_PATHS | {"/password/first-change/"}
        if path in exempt_paths:
            return True

        if path.startswith(COMMON_EXEMPT_PREFIXES):
            return True

        return _is_login_path(path)


class ProfileConfirmationMiddleware:
    """Obliga a confirmar los datos personales una vez por usuario.

    Corre después de ``FirstLoginPasswordChangeMiddleware`` y exime la ruta de
    cambio de contraseña obligatorio: si un usuario arrastra los dos flags, el
    orden es primero contraseña y después datos personales, sin que los dos
    middlewares se redirijan entre sí en bucle.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if (
            user
            and getattr(user, "is_authenticated", False)
            and not self._is_exempt_path(request.path)
            and needs_profile_confirmation(user)
        ):
            return redirect("confirmar_datos_personales")

        return self.get_response(request)

    @staticmethod
    def _is_exempt_path(path):
        exempt_paths = COMMON_EXEMPT_PATHS | {"/password/first-change/"}
        try:
            exempt_paths.add(reverse("confirmar_datos_personales"))
        except NoReverseMatch:
            exempt_paths.add("/mi-cuenta/confirmar/")
        if path in exempt_paths:
            return True

        if path.startswith(COMMON_EXEMPT_PREFIXES):
            return True

        return _is_login_path(path)
