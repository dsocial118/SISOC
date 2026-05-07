from __future__ import annotations

from django.db.models import Q, QuerySet

from iam.services import user_has_permission_code

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
    profile = _get_profile(user)
    if not profile:
        return None
    if not getattr(profile, "es_usuario_provincial", False):
        return None
    return getattr(profile, "provincia_id", None)


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
    provincia_id = get_user_provincia_id(user)
    if not provincia_id:
        return False
    return _user_has_any_permission_code(
        user,
        (ROLE_VAT_PROVINCIAL_PERMISSION, VAT_VIEW_CENTRO_PERMISSION),
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

    provincia_id = get_user_provincia_id(user)
    if provincia_id and is_vat_provincial(user):
        return base_qs.filter(provincia_id=provincia_id)

    return _filter_centros_by_assignment(base_qs, user, include_revisores=True)


def filter_centros_queryset_for_management(base_qs: QuerySet, user) -> QuerySet:
    if is_vat_sse(user):
        return base_qs

    provincia_id = get_user_provincia_id(user)
    if (
        provincia_id
        and is_vat_provincial(user)
        and user_has_permission_code(user, VAT_CHANGE_CENTRO_PERMISSION)
    ):
        return base_qs.filter(provincia_id=provincia_id)

    return _filter_centros_by_assignment(base_qs, user, include_revisores=False)


def can_user_access_centro(user, centro) -> bool:
    if is_vat_sse(user):
        return True

    provincia_id = get_user_provincia_id(user)
    if provincia_id and is_vat_provincial(user):
        return centro.provincia_id == provincia_id

    return bool(
        _user_is_referente_for_centro(user, centro)
        or _user_is_revisor_for_centro(user, centro)
    )


def filter_ofertas_queryset_for_user(base_qs: QuerySet, user) -> QuerySet:
    if is_vat_sse(user):
        return base_qs

    provincia_id = get_user_provincia_id(user)
    if provincia_id and is_vat_provincial(user):
        return base_qs.filter(centro__provincia_id=provincia_id)

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

    provincia_id = get_user_provincia_id(user)
    if (
        provincia_id
        and is_vat_provincial(user)
        and user_has_permission_code(user, VAT_CHANGE_CENTRO_PERMISSION)
    ):
        return base_qs.filter(centro__provincia_id=provincia_id)

    if is_vat_referente(user):
        return base_qs.filter(_centro_referente_q(user, prefix="centro__")).distinct()

    return base_qs.none()


def filter_comisiones_queryset_for_user(base_qs: QuerySet, user) -> QuerySet:
    if is_vat_sse(user):
        return base_qs

    provincia_id = get_user_provincia_id(user)
    if provincia_id and is_vat_provincial(user):
        return base_qs.filter(oferta__centro__provincia_id=provincia_id)

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

    provincia_id = get_user_provincia_id(user)
    if (
        provincia_id
        and is_vat_provincial(user)
        and user_has_permission_code(user, VAT_CHANGE_CENTRO_PERMISSION)
    ):
        return base_qs.filter(oferta__centro__provincia_id=provincia_id)

    if is_vat_referente(user):
        return base_qs.filter(
            _centro_referente_q(user, prefix="oferta__centro__")
        ).distinct()

    return base_qs.none()


def filter_sesiones_queryset_for_user(base_qs: QuerySet, user) -> QuerySet:
    if is_vat_sse(user):
        return base_qs

    provincia_id = get_user_provincia_id(user)
    if provincia_id and is_vat_provincial(user):
        return base_qs.filter(comision__oferta__centro__provincia_id=provincia_id)

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

    provincia_id = get_user_provincia_id(user)
    if (
        provincia_id
        and is_vat_provincial(user)
        and user_has_permission_code(user, VAT_CHANGE_CENTRO_PERMISSION)
    ):
        return base_qs.filter(comision__oferta__centro__provincia_id=provincia_id)

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
        and user_has_permission_code(user, VAT_ADD_CENTRO_PERMISSION)
    )


def can_user_edit_centro(user, centro) -> bool:
    if is_vat_sse(user):
        return True

    provincia_id = get_user_provincia_id(user)
    if (
        provincia_id
        and is_vat_provincial(user)
        and user_has_permission_code(user, VAT_CHANGE_CENTRO_PERMISSION)
    ):
        return centro.provincia_id == provincia_id

    return _user_is_referente_for_centro(user, centro)
