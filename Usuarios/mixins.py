from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin,
)
from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied
from django.db.models import Q


class PermisosMixin(PermissionRequiredMixin):
    """
    Verifica al mismo tiempo usuario logeado y tenga alguno de los permisos indicados o un grupo que tenga alguno de esos permisos (Requiere agregar
    un atributo 'permission_required ' en la vista, colocando un permiso o una tupla)

    """

    def has_permission(self):
        acceso = False
        permisos_de_grupo = False
        user = self.request.user
        if Group.objects.filter(user=user).exists():
            group = Group.objects.filter(user=user)

        for group in Group.objects.all():
            permissions = group.permissions.all()
            lista = []

            for p in permissions:
                lista.append("Usuarios." + p.codename)
            if self.permission_required in lista:
                permisos_de_grupo = True
        permisos_de_usuario = any(user.has_perm(p) for p in self.permission_required)
        if permisos_de_usuario or permisos_de_grupo:
            acceso = True
        return acceso

    def handle_no_permission(self):
        self.raise_exception = self.request.user.is_authenticated
        self.permission_denied_message = "No posee permisos para realizar la acción"
        return super(PermisosMixin, self).handle_no_permission()


def users_con_perm(perm_name):
    return User.objects.filter(
        Q(user_permissions__codename=perm_name)
        | Q(groups__permissions__codename=perm_name)
    ).distinct()
