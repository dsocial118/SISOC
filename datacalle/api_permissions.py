from rest_framework.permissions import BasePermission

from users.services_datacalle import tiene_acceso_datacalle


class TieneAccesoDataCalle(BasePermission):
    """Los tres roles de DataCalle consumen la API de la app (D2.1).

    El relevador releva; el coordinador y el administrador ademas gestionan.
    Que puede hacer cada uno lo decide la vista, no este permiso.
    """

    message = "Este usuario no tiene habilitado DataCalle."

    def has_permission(self, request, view):
        return tiene_acceso_datacalle(request.user)


# Alias historico: se conserva mientras queden importadores.
EsRelevadorCalle = TieneAccesoDataCalle
