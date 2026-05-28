from __future__ import annotations

from django.db.models import Q, QuerySet

from iam.services import user_has_permission_code
from users.territorial_scope import (
    apply_territorial_scope,
    get_effective_scopes,
    get_single_full_province_scope_id,
    user_can_access_territory,
)

ROLE_VAT_SSE_PERMISSION = "auth.role_vat_sse"
ROLE_VAT_PROVINCIAL_PERMISSION = "auth.role_provincia_vat"
ROLE_REFERENTE_CENTRO_PERMISSIONS = (
    "auth.role_referentecentrovat",
    "auth.role_centroreferentevat",
)
ROLE_REVISOR_CENTRO_PERMISSION = "auth.role_revisorcentrovat"
VAT_VIEW_CENTRO_PERMISSION = "VAT.view_centro"
VAT_ADD_CENTRO_PERMISSION = "VAT.add_centro"
VAT_CHANGE_CENTRO_PERMISSION = "VAT.change_centro"


def _user_has_any_permission_code(user, permission_codes) -> bool:
    return any(user_has_permission_code(user, code) for code in permission_codes)


def _get_profile(user):
    return getattr(user, "profile", None)


def get_user_provincia_id(user) -> int | None:
    return get_single_full_province_scope_id(user)


def is_vat_sse(user) -> bool:
    if not user:
        return False
    return bool(
        user.is_superuser or user_has_permission_code(user, ROLE_VAT_SSE_PERMISSION)
    )


def is_vat_referente(user) -> bool:
    if not user:
        return False
    return _user_has_any_permission_code(user, ROLE_REFERENTE_CENTRO_PERMISSIONS)


def is_vat_revisor(user) -> bool:
    if not user:
        return False
    return user_has_permission_code(user, ROLE_REVISOR_CENTRO_PERMISSION)


def is_vat_provincial(user) -> bool:
    if not user:
        return False
    profile = _get_profile(user)
    if not getattr(profile, "es_usuario_provincial", False):
        return False
    return _user_has_any_permission_code(
        user,
        (ROLE_VAT_PROVINCIAL_PERMISSION, VAT_VIEW_CENTRO_PERMISSION),
    )


def _has_effective_territorial_scopes(user) -> bool:
    return bool(get_effective_scopes(user))


def _filter_centros_by_territorial_scope(base_qs: QuerySet, user) -> QuerySet:
    return apply_territorial_scope(
        base_qs,
        user,
        provincia_lookup="provincia_id",
        municipio_lookup="municipio_id",
        localidad_lookup="localidad_id",
    )


def _filter_related_centros_by_territorial_scope(
    base_qs: QuerySet,
    user,
    *,
    prefix: str,
) -> QuerySet:
    return apply_territorial_scope(
        base_qs,
        user,
        provincia_lookup=f"{prefix}provincia_id",
        municipio_lookup=f"{prefix}municipio_id",
        localidad_lookup=f"{prefix}localidad_id",
    )


def _centro_referente_q(user, prefix: str = "") -> Q:
    return Q(**{f"{prefix}referentes__id": user.id}) | Q(
        **{f"{prefix}referente_id": user.id}
    )


def _centro_revisor_q(user, prefix: str = "") -> Q:
    return Q(**{f"{prefix}revisores__id": user.id})


def _assigned_centros_q(user, include_revisores: bool) -> Q | None:
    query = Q()
    has_scope = False
    if is_vat_referente(user):
        query |= _centro_referente_q(user)
        has_scope = True
    if include_revisores and is_vat_revisor(user):
        query |= _centro_revisor_q(user)
        has_scope = True
    if not has_scope:
        return None
    return query


def _filter_centros_by_assignment(
    base_qs: QuerySet, user, include_revisores: bool
) -> QuerySet:
    query = _assigned_centros_q(user, include_revisores)
    if query is None:
        return base_qs.none()
    return base_qs.filter(query).distinct()


def _user_is_referente_for_centro(user, centro) -> bool:
    if not is_vat_referente(user):
        return False
    if getattr(centro, "referente_id", None) == getattr(user, "id", None):
        return True
    if not getattr(centro, "pk", None):
        return False
    referentes = getattr(centro, "referentes", None)
    if referentes is None:
        return False
    return referentes.filter(pk=user.id).exists()


def _user_is_revisor_for_centro(user, centro) -> bool:
    if not is_vat_revisor(user) or not getattr(centro, "pk", None):
        return False
    revisores = getattr(centro, "revisores", None)
    if revisores is None:
        return False
    return revisores.filter(pk=user.id).exists()


def filter_centros_queryset_for_user(base_qs: QuerySet, user) -> QuerySet:
    if is_vat_sse(user):
        return base_qs

    if is_vat_provincial(user) and _has_effective_territorial_scopes(user):
        return _filter_centros_by_territorial_scope(base_qs, user)

    return _filter_centros_by_assignment(base_qs, user, include_revisores=True)


def filter_centros_queryset_for_management(base_qs: QuerySet, user) -> QuerySet:
    if is_vat_sse(user):
        return base_qs

    if (
        is_vat_provincial(user)
        and _has_effective_territorial_scopes(user)
        and user_has_permission_code(user, VAT_CHANGE_CENTRO_PERMISSION)
    ):
        return _filter_centros_by_territorial_scope(base_qs, user)

    return _filter_centros_by_assignment(base_qs, user, include_revisores=False)


def can_user_access_centro(user, centro) -> bool:
    if is_vat_sse(user):
        return True

    if is_vat_provincial(user) and _has_effective_territorial_scopes(user):
        return user_can_access_territory(
            user,
            provincia_id=centro.provincia_id,
            municipio_id=centro.municipio_id,
            localidad_id=centro.localidad_id,
        )

    return bool(
        _user_is_referente_for_centro(user, centro)
        or _user_is_revisor_for_centro(user, centro)
    )


def filter_ofertas_queryset_for_user(base_qs: QuerySet, user) -> QuerySet:
    if is_vat_sse(user):
        return base_qs

    if is_vat_provincial(user) and _has_effective_territorial_scopes(user):
        return _filter_related_centros_by_territorial_scope(
            base_qs,
            user,
            prefix="centro__",
        )

    query = Q()
    has_scope = False
    if is_vat_referente(user):
        query |= _centro_referente_q(user, prefix="centro__")
        has_scope = True
    if is_vat_revisor(user):
        query |= _centro_revisor_q(user, prefix="centro__")
        has_scope = True
    if has_scope:
        return base_qs.filter(query).distinct()

    return base_qs.none()


def filter_ofertas_queryset_for_management(base_qs: QuerySet, user) -> QuerySet:
    if is_vat_sse(user):
        return base_qs

    if (
        is_vat_provincial(user)
        and _has_effective_territorial_scopes(user)
        and user_has_permission_code(user, VAT_CHANGE_CENTRO_PERMISSION)
    ):
        return _filter_related_centros_by_territorial_scope(
            base_qs,
            user,
            prefix="centro__",
        )

    if is_vat_referente(user):
        return base_qs.filter(_centro_referente_q(user, prefix="centro__")).distinct()

    return base_qs.none()


def filter_comisiones_queryset_for_user(base_qs: QuerySet, user) -> QuerySet:
    if is_vat_sse(user):
        return base_qs

    if is_vat_provincial(user) and _has_effective_territorial_scopes(user):
        return _filter_related_centros_by_territorial_scope(
            base_qs,
            user,
            prefix="oferta__centro__",
        )

    query = Q()
    has_scope = False
    if is_vat_referente(user):
        query |= _centro_referente_q(user, prefix="oferta__centro__")
        has_scope = True
    if is_vat_revisor(user):
        query |= _centro_revisor_q(user, prefix="oferta__centro__")
        has_scope = True
    if has_scope:
        return base_qs.filter(query).distinct()

    return base_qs.none()


def filter_comisiones_queryset_for_management(base_qs: QuerySet, user) -> QuerySet:
    if is_vat_sse(user):
        return base_qs

    if (
        is_vat_provincial(user)
        and _has_effective_territorial_scopes(user)
        and user_has_permission_code(user, VAT_CHANGE_CENTRO_PERMISSION)
    ):
        return _filter_related_centros_by_territorial_scope(
            base_qs,
            user,
            prefix="oferta__centro__",
        )

    if is_vat_referente(user):
        return base_qs.filter(
            _centro_referente_q(user, prefix="oferta__centro__")
        ).distinct()

    return base_qs.none()


def filter_sesiones_queryset_for_user(base_qs: QuerySet, user) -> QuerySet:
    if is_vat_sse(user):
        return base_qs

    if is_vat_provincial(user) and _has_effective_territorial_scopes(user):
        return _filter_related_centros_by_territorial_scope(
            base_qs,
            user,
            prefix="comision__oferta__centro__",
        )

    query = Q()
    has_scope = False
    if is_vat_referente(user):
        query |= _centro_referente_q(user, prefix="comision__oferta__centro__")
        has_scope = True
    if is_vat_revisor(user):
        query |= _centro_revisor_q(user, prefix="comision__oferta__centro__")
        has_scope = True
    if has_scope:
        return base_qs.filter(query).distinct()

    return base_qs.none()


def filter_sesiones_queryset_for_management(base_qs: QuerySet, user) -> QuerySet:
    if is_vat_sse(user):
        return base_qs

    if (
        is_vat_provincial(user)
        and _has_effective_territorial_scopes(user)
        and user_has_permission_code(user, VAT_CHANGE_CENTRO_PERMISSION)
    ):
        return _filter_related_centros_by_territorial_scope(
            base_qs,
            user,
            prefix="comision__oferta__centro__",
        )

    if is_vat_referente(user):
        return base_qs.filter(
            _centro_referente_q(user, prefix="comision__oferta__centro__")
        ).distinct()

    return base_qs.none()


def can_user_add_vat_entities(user) -> bool:
    return is_vat_sse(user)


def can_user_create_centro(user) -> bool:
    if is_vat_sse(user):
        return True

    return bool(
        is_vat_provincial(user)
        and _has_effective_territorial_scopes(user)
        and user_has_permission_code(user, VAT_ADD_CENTRO_PERMISSION)
    )


def can_user_edit_centro(user, centro) -> bool:
    if is_vat_sse(user):
        return True

    if (
        is_vat_provincial(user)
        and _has_effective_territorial_scopes(user)
        and user_has_permission_code(user, VAT_CHANGE_CENTRO_PERMISSION)
    ):
        return user_can_access_territory(
            user,
            provincia_id=centro.provincia_id,
            municipio_id=centro.municipio_id,
            localidad_id=centro.localidad_id,
        )

    return _user_is_referente_for_centro(user, centro)


GRUPO_REFERENTE_CENTRO_VAT = "CFP"
LIMITE_USUARIOS_POR_CENTRO_VAT = 10


def usuarios_centro_vat_activos(centro) -> int:
    """Cantidad de usuarios referentes activos asociados a un Centro VAT.

    Cuenta los `referentes` (M2M existente) más el `referente` legado (FK)
    si no figura en la M2M, para reflejar el total real de usuarios con
    acceso al centro.
    """
    if not getattr(centro, "pk", None):
        return 0
    referentes_ids = set(centro.referentes.values_list("id", flat=True))
    if centro.referente_id:
        referentes_ids.add(centro.referente_id)
    return len(referentes_ids)


def usuarios_centro_vat_restantes(centro) -> int:
    """Cupo restante de usuarios referentes para un Centro VAT."""
    return max(0, LIMITE_USUARIOS_POR_CENTRO_VAT - usuarios_centro_vat_activos(centro))


def _actor_puede_delegar_grupo_nombre(user, grupo_nombre: str) -> bool:
    """Reusa el mecanismo IAM existente `Profile.grupos_asignables`."""
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if user.is_superuser:
        return True
    profile = _get_profile(user)
    if not profile:
        return False
    return profile.grupos_asignables.filter(name=grupo_nombre).exists()


def puede_generar_usuario_centro_vat(user, centro) -> bool:
    """Regla para habilitar el botón "Generar usuario" en un Centro VAT.

    - El actor debe poder editar el centro (regla VAT existente).
    - Debe poder delegar el grupo "CFP".
    - Debe quedar cupo respecto del máximo por centro.
    """
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if not can_user_edit_centro(user, centro):
        return False
    if not _actor_puede_delegar_grupo_nombre(user, GRUPO_REFERENTE_CENTRO_VAT):
        return False
    return usuarios_centro_vat_restantes(centro) > 0


def puede_ver_usuarios_centro_vat(user, centro) -> bool:
    """Quién ve el listado de usuarios+credenciales de un Centro VAT.

    Solo el referente del centro (membresía en `referentes`/`referente`) o
    SSE/superusuario. Se valida la pertenencia directa al M2M para que el
    panel también funcione con usuarios generados antes de que se les asigne
    el permiso de rol.
    """
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if is_vat_sse(user):
        return True
    if not getattr(centro, "pk", None):
        return False
    if getattr(centro, "referente_id", None) == getattr(user, "id", None):
        return True
    return centro.referentes.filter(pk=user.id).exists()
