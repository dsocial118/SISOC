from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied

def group_required(*group_names):
    """
    Restringe el acceso a vistas basadas en el grupo del usuario.
    Si el usuario pertenece a alguno de los grupos especificados o es superusuario, se le permite el acceso.
    De lo contrario, se lanza un PermissionDenied.
    """
    def in_groups(u):
        if u.is_authenticated:
            if bool(u.groups.filter(name__in=group_names)) or u.is_superuser:
                return True
        raise PermissionDenied
    return user_passes_test(in_groups)
