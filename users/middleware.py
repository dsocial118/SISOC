from django.shortcuts import redirect
from django.urls import reverse, NoReverseMatch


class FirstLoginPasswordChangeMiddleware:
    """Redirige a cambio de contraseña obligatorio en primer ingreso web."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user and getattr(user, "is_authenticated", False):
            profile = getattr(user, "profile", None)
            must_change = bool(getattr(profile, "must_change_password", False))
            if must_change and not self._is_exempt_path(request.path):
                return redirect("password_change_required")

        return self.get_response(request)

    @staticmethod
    def _is_exempt_path(path):
        exempt_paths = {
            "/logout",
            "/logout/",
            "/password/first-change/",
            "/api/users/login/",
            "/api/users/logout/",
            "/api/users/password-reset/request/",
            "/api/users/password-reset/confirm/",
        }
        if path in exempt_paths:
            return True

        static_prefixes = ("/static/", "/media/", "/api/")
        if path.startswith(static_prefixes):
            return True
        if path.startswith("/password_reset/"):
            return True
        if path.startswith("/reset/"):
            return True
        if path.startswith("/password/reset/confirm/"):
            return True

        try:
            login_path = reverse("login")
            if login_path and login_path != "/" and path == login_path:
                return True
        except NoReverseMatch:
            pass

        return False
