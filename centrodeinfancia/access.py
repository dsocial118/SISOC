from django.shortcuts import get_object_or_404

from core.constants import UserGroups
from users.models import Profile

GRUPO_CDI_REFERENTE_CENTRO = UserGroups.CDI_REFERENTE_CENTRO


def actor_puede_delegar_grupo_nombre(user, grupo_nombre):
    """Indica si el usuario puede delegar (asignar) un grupo por nombre.

    Reutiliza el mecanismo IAM existente `Profile.grupos_asignables`; el
    superusuario puede delegar cualquier grupo.
    """
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if user.is_superuser:
        return True
    profile = getattr(user, "profile", None)
    if not profile:
        return False
    return profile.grupos_asignables.filter(name=grupo_nombre).exists()


def usuarios_cdi_activos(centro):
    """Cantidad de usuarios referentes activos asociados a un CDI."""
    from centrodeinfancia.models import AccesoCDI  # noqa: PLC0415

    return AccesoCDI.objects.filter(centro=centro, activo=True).count()


def usuarios_cdi_restantes(centro):
    """Cupo restante de usuarios referentes para un CDI."""
    from centrodeinfancia.models import AccesoCDI  # noqa: PLC0415

    return max(
        0,
        AccesoCDI.LIMITE_USUARIOS_POR_CENTRO - usuarios_cdi_activos(centro),
    )


def puede_generar_usuario_cdi(user, centro):
    """Regla de negocio para habilitar el botón "Generar usuario" en un CDI.

    - El usuario debe poder delegar el grupo "CDI - Referente centro".
    - Debe ser de la misma provincia que el CDI (salvo superusuario).
    - Debe quedar cupo respecto del máximo por CDI.
    """
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if not actor_puede_delegar_grupo_nombre(user, GRUPO_CDI_REFERENTE_CENTRO):
        return False
    if usuarios_cdi_restantes(centro) <= 0:
        return False
    if user.is_superuser:
        return True

    provincia_usuario = get_provincia_usuario(user)
    if provincia_usuario is None:
        return False
    return centro.provincia_id == provincia_usuario.id


def puede_ver_usuarios_cdi(user, centro):
    """Quién ve el listado de usuarios+credenciales de un CDI.

    Solo el referente del centro (usuario con `AccesoCDI` activo en ese CDI)
    o un superusuario. El provincial que genera NO ve este panel.
    """
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if user.is_superuser:
        return True

    from centrodeinfancia.models import AccesoCDI  # noqa: PLC0415

    return AccesoCDI.objects.filter(centro=centro, user=user, activo=True).exists()


def get_provincia_usuario(user):
    if not user or not user.is_authenticated:
        return None

    try:
        profile = Profile.objects.select_related("provincia").get(user=user)
    except Exception:
        return None
    return profile.provincia


def aplicar_filtro_provincia_usuario(queryset, user, provincia_lookup="provincia"):
    provincia_usuario = get_provincia_usuario(user)
    if provincia_usuario:
        return queryset.filter(**{provincia_lookup: provincia_usuario})
    return queryset


def get_object_scoped_por_provincia_or_404(
    queryset,
    user,
    *args,
    provincia_lookup="provincia",
    **kwargs,
):
    scoped_queryset = aplicar_filtro_provincia_usuario(
        queryset,
        user,
        provincia_lookup=provincia_lookup,
    )
    return get_object_or_404(scoped_queryset, *args, **kwargs)


def _ids_centros_referente(user):
    """IDs de CDIs donde el usuario es referente (tiene AccesoCDI).

    Devuelve la lista de centros con acceso activo si el usuario es referente
    (tiene al menos un `AccesoCDI`, activo o histórico); `None` si no lo es,
    para que aplique el filtro provincial existente.
    """
    if not user or not getattr(user, "is_authenticated", False):
        return None

    from centrodeinfancia.models import AccesoCDI  # noqa: PLC0415

    user_id = getattr(user, "pk", None)
    if not user_id:
        return None

    if not AccesoCDI.objects.filter(user_id=user_id).exists():
        return None
    return list(
        AccesoCDI.objects.filter(user_id=user_id, activo=True).values_list(
            "centro_id", flat=True
        )
    )


def es_referente_cdi(user):
    """Indica si el usuario está vinculado como referente de algún CDI."""
    return _ids_centros_referente(user) is not None


def aplicar_scope_centros_cdi(
    queryset,
    user,
    *,
    id_lookup="id",
    provincia_lookup="provincia",
):
    """Acota un queryset según el alcance del usuario.

    - Superusuario: sin restricción.
    - Referente CDI: solo sus centros con `AccesoCDI` activo.
    - Resto: filtro provincial existente (sin cambios de comportamiento).
    """
    if not user or not getattr(user, "is_authenticated", False):
        return queryset
    if getattr(user, "is_superuser", False):
        return queryset

    referente_ids = _ids_centros_referente(user)
    if referente_ids is not None:
        return queryset.filter(**{f"{id_lookup}__in": referente_ids})

    return aplicar_filtro_provincia_usuario(
        queryset,
        user,
        provincia_lookup=provincia_lookup,
    )


def get_object_scoped_cdi_or_404(
    queryset,
    user,
    *args,
    id_lookup="id",
    provincia_lookup="provincia",
    **kwargs,
):
    scoped_queryset = aplicar_scope_centros_cdi(
        queryset,
        user,
        id_lookup=id_lookup,
        provincia_lookup=provincia_lookup,
    )
    return get_object_or_404(scoped_queryset, *args, **kwargs)
