from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist

from core.constants import UserGroups
from core.models import Provincia
from users.models import Profile
from users.services_delegation import effective_delegatable_groups_qs
from users.territorial_scope import (
    apply_territorial_scope,
    get_single_full_province_scope_id,
    is_territorial_user,
    user_can_access_territory,
)

GRUPO_CDI_REFERENTE_CENTRO = UserGroups.CDI_REFERENTE_CENTRO


def actor_puede_delegar_grupo_nombre(user, grupo_nombre):
    """Indica si el usuario puede delegar (asignar) un grupo por nombre.

    Reutiliza el alcance efectivo de delegación; el superusuario puede delegar
    cualquier grupo.
    """
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if user.is_superuser:
        return True
    return effective_delegatable_groups_qs(user).filter(name=grupo_nombre).exists()


def puede_generar_usuario_egp(user):
    """Indica si el usuario puede generar referentes provinciales SIMEPI."""
    return actor_puede_delegar_grupo_nombre(user, UserGroups.SIMEPI_EGP)


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
    if not is_territorial_user(user):
        return False

    return user_can_access_territory(
        user,
        provincia_id=centro.provincia_id,
        municipio_id=getattr(centro, "municipio_id", None),
        localidad_id=getattr(centro, "localidad_id", None),
    )


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

    user_id = getattr(user, "pk", None)
    if user_id:
        profile = (
            Profile.objects.select_related("provincia").filter(user_id=user_id).first()
        )
        if profile and profile.provincia:
            return profile.provincia

    try:
        provincia = user.profile.provincia
    except (AttributeError, ObjectDoesNotExist):
        provincia = None
    if provincia:
        return provincia

    provincia_id = get_single_full_province_scope_id(user)
    if not provincia_id:
        return None
    return Provincia.objects.filter(pk=provincia_id).first()


def _sibling_territorial_lookup(provincia_lookup, sibling):
    parts = provincia_lookup.split("__")
    if parts[-1] == "provincia_id":
        parts[-1] = f"{sibling}_id"
        return "__".join(parts)
    if parts[-1] == "provincia":
        parts[-1] = sibling
        return "__".join(parts)
    return None


def aplicar_filtro_provincia_usuario(queryset, user, provincia_lookup="provincia"):
    if is_territorial_user(user):
        return apply_territorial_scope(
            queryset,
            user,
            provincia_lookup=provincia_lookup,
            municipio_lookup=_sibling_territorial_lookup(provincia_lookup, "municipio"),
            localidad_lookup=_sibling_territorial_lookup(provincia_lookup, "localidad"),
        )

    provincia_usuario = get_provincia_usuario(user)
    if provincia_usuario:
        return queryset.filter(**{provincia_lookup: provincia_usuario})

    return apply_territorial_scope(
        queryset,
        user,
        provincia_lookup=provincia_lookup,
        municipio_lookup=_sibling_territorial_lookup(provincia_lookup, "municipio"),
        localidad_lookup=_sibling_territorial_lookup(provincia_lookup, "localidad"),
    )


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


def _ids_centros_trabajador(user):
    """IDs de CDIs donde el usuario está vinculado como trabajador."""
    if not user or not getattr(user, "is_authenticated", False):
        return None

    from centrodeinfancia.models import Trabajador  # noqa: PLC0415

    user_id = getattr(user, "pk", None)
    if not user_id:
        return None
    if not Trabajador.objects.filter(usuario_id=user_id).exists():
        return None
    return list(
        Trabajador.objects.filter(usuario_id=user_id).values_list(
            "centro_id", flat=True
        )
    )


def es_auditor_simepi(user):
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return False
    group_names = set(user.groups.values_list("name", flat=True))
    if {
        UserGroups.SIMEPI_ADMINISTRADOR,
        UserGroups.SIMEPI_ANALISTA_DATOS,
    } & group_names:
        return False
    return UserGroups.SIMEPI_AUDITORIA in group_names


def tiene_alcance_simepi_nacional(user):
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return True
    return user.groups.filter(
        name__in=(
            UserGroups.SIMEPI_ADMINISTRADOR,
            UserGroups.SIMEPI_ANALISTA_DATOS,
            UserGroups.SIMEPI_EQUIPO_NACIONAL,
            UserGroups.SIMEPI_AUDITORIA,
        )
    ).exists()


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
    - Trabajador CDI: solo los centros donde su FK `usuario` está vinculado.
    - Resto: filtro provincial existente (sin cambios de comportamiento).
    """
    if not user or not getattr(user, "is_authenticated", False):
        return queryset
    if tiene_alcance_simepi_nacional(user):
        return queryset

    referente_ids = _ids_centros_referente(user)
    trabajador_ids = _ids_centros_trabajador(user)
    if referente_ids is not None or trabajador_ids is not None:
        centro_ids = set(referente_ids or []) | set(trabajador_ids or [])
        return queryset.filter(**{f"{id_lookup}__in": centro_ids})

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
