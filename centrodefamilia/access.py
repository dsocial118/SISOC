"""Reglas de acceso y scope para el dominio CDF (Centro de Familia).

Espeja el patrón de ``centrodeinfancia.access`` adaptado a CDF:
- ``AccesoCDF`` determina qué centros ve un referente (no el FK legacy).
- El scope provincial sigue usando el mecanismo territorial existente.
"""

from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404

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

GRUPO_CDF_REFERENTE_CENTRO = UserGroups.CDF_REFERENTE_CENTRO
ROLE_CDF_SSE_PERMISSION = "auth.role_cdf_sse"


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


def usuarios_cdf_activos(centro):
    """Cantidad de usuarios referentes activos asociados a un CDF."""
    from centrodefamilia.models import AccesoCDF  # noqa: PLC0415

    return AccesoCDF.objects.filter(centro=centro, activo=True).count()


def usuarios_cdf_restantes(centro):
    """Cupo restante de usuarios referentes para un CDF."""
    from centrodefamilia.models import AccesoCDF  # noqa: PLC0415

    return max(
        0,
        AccesoCDF.LIMITE_USUARIOS_POR_CENTRO - usuarios_cdf_activos(centro),
    )


def puede_gestionar_usuarios_cdf(user, centro):
    """Habilita a un actor a gestionar usuarios referentes de un CDF.

    Regla de delegación + territorio, SIN considerar el cupo. Es la base de
    :func:`puede_generar_usuario_cdf` y además sirve como gate de lectura del
    detalle del centro: poder ver el CDF para gestionarlo no debe depender de
    que quede cupo libre (si no, llenar el cupo revocaría el acceso a la ficha).
    """
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if not actor_puede_delegar_grupo_nombre(user, GRUPO_CDF_REFERENTE_CENTRO):
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


def puede_generar_usuario_cdf(user, centro):
    """Regla de negocio para habilitar el botón "Generar usuario" en un CDF.

    - El usuario debe poder delegar el grupo "CDF - Referente centro".
    - Debe ser de la misma provincia que el CDF (salvo superusuario).
    - Debe quedar cupo respecto del máximo por CDF.
    """
    if not puede_gestionar_usuarios_cdf(user, centro):
        return False
    return usuarios_cdf_restantes(centro) > 0


def puede_ver_usuarios_cdf(user, centro):
    """Quién ve el listado de usuarios+credenciales de un CDF.

    Solo el referente del centro (usuario con ``AccesoCDF`` activo en ese CDF)
    o un superusuario. El provincial que genera NO ve este panel.
    """
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if user.is_superuser:
        return True

    from centrodefamilia.models import AccesoCDF  # noqa: PLC0415

    return AccesoCDF.objects.filter(centro=centro, user=user, activo=True).exists()


def puede_tomar_asistencia_cdf(user, centro):
    """Quién puede tomar asistencia en las actividades de un CDF.

    El referente del centro (FK legacy o ``AccesoCDF`` activo), un usuario con
    rol CDF SSE o un superusuario. Espeja el criterio de edición del centro.
    """
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if user.is_superuser:
        return True

    from iam.services import user_has_permission_code  # noqa: PLC0415

    if user_has_permission_code(user, ROLE_CDF_SSE_PERMISSION):
        return True
    if centro.referente_id == user.pk:
        return True

    from centrodefamilia.models import AccesoCDF  # noqa: PLC0415

    return AccesoCDF.objects.filter(centro=centro, user=user, activo=True).exists()


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


def ids_centros_referente_cdf(user):
    """IDs de Centros de Familia donde el usuario es referente (tiene AccesoCDF).

    Devuelve la lista de centros con acceso activo si el usuario es referente
    (tiene al menos un ``AccesoCDF``, activo o histórico); ``None`` si no lo es,
    para que aplique el filtro de scope existente.
    """
    if not user or not getattr(user, "is_authenticated", False):
        return None

    from centrodefamilia.models import AccesoCDF  # noqa: PLC0415

    user_id = getattr(user, "pk", None)
    if not user_id:
        return None

    if not AccesoCDF.objects.filter(user_id=user_id).exists():
        return None
    return list(
        AccesoCDF.objects.filter(user_id=user_id, activo=True).values_list(
            "centro_id", flat=True
        )
    )


def es_referente_cdf(user):
    """Indica si el usuario está vinculado como referente de algún CDF."""
    return ids_centros_referente_cdf(user) is not None


def aplicar_scope_centros_cdf(
    queryset,
    user,
    *,
    id_lookup="id",
    provincia_lookup="provincia",
):
    """Acota un queryset de centros CDF según el alcance del usuario.

    - Superusuario: sin restricción.
    - Referente CDF (AccesoCDF): solo sus centros con acceso activo.
    - Resto: filtro provincial existente (sin cambios de comportamiento).
    """
    if not user or not getattr(user, "is_authenticated", False):
        return queryset
    if getattr(user, "is_superuser", False):
        return queryset

    referente_ids = ids_centros_referente_cdf(user)
    if referente_ids is not None:
        return queryset.filter(**{f"{id_lookup}__in": referente_ids})

    return aplicar_filtro_provincia_usuario(
        queryset,
        user,
        provincia_lookup=provincia_lookup,
    )


def get_object_scoped_cdf_or_404(
    queryset,
    user,
    *args,
    id_lookup="id",
    provincia_lookup="provincia",
    **kwargs,
):
    scoped_queryset = aplicar_scope_centros_cdf(
        queryset,
        user,
        id_lookup=id_lookup,
        provincia_lookup=provincia_lookup,
    )
    return get_object_or_404(scoped_queryset, *args, **kwargs)
