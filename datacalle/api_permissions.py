from rest_framework.permissions import BasePermission

from users.services_datacalle import is_relevador_calle_user


class EsRelevadorCalle(BasePermission):
    """Sólo entrevistadores de DataCalle consumen la API de la app (D2.1)."""

    message = "Este usuario no tiene habilitado DataCalle."

    def has_permission(self, request, view):
        return is_relevador_calle_user(request.user)
