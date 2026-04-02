from __future__ import annotations

from django.db.models import QuerySet

from iam.services import user_has_permission_code

ROLE_VAT_SSE_PERMISSION = "auth.role_vat_sse"
ROLE_VAT_PROVINCIAL_PERMISSION = "auth.role_provincia_vat"
ROLE_REFERENTE_CENTRO_PERMISSIONS = (
    "auth.role_referentecentrovat",
    "auth.role_centroreferentevat",
)
VAT_VIEW_CENTRO_PERMISSION = "VAT.view_centro"


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


def filter_centros_queryset_for_user(base_qs: QuerySet, user) -> QuerySet:
    if is_vat_sse(user):
        return base_qs

    provincia_id = get_user_provincia_id(user)
    if provincia_id and is_vat_provincial(user):
        return base_qs.filter(provincia_id=provincia_id)

    if is_vat_referente(user):
        return base_qs.filter(referente_id=user.id)

    return base_qs.none()


def can_user_access_centro(user, centro) -> bool:
    if is_vat_sse(user):
        return True

    provincia_id = get_user_provincia_id(user)
    if provincia_id and is_vat_provincial(user):
        return centro.provincia_id == provincia_id

    return bool(is_vat_referente(user) and centro.referente_id == user.id)


def filter_ofertas_queryset_for_user(base_qs: QuerySet, user) -> QuerySet:
    if is_vat_sse(user):
        return base_qs

    provincia_id = get_user_provincia_id(user)
    if provincia_id and is_vat_provincial(user):
        return base_qs.filter(centro__provincia_id=provincia_id)

    if is_vat_referente(user):
        return base_qs.filter(centro__referente_id=user.id)

    return base_qs.none()


def filter_comisiones_queryset_for_user(base_qs: QuerySet, user) -> QuerySet:
    if is_vat_sse(user):
        return base_qs

    provincia_id = get_user_provincia_id(user)
    if provincia_id and is_vat_provincial(user):
        return base_qs.filter(oferta__centro__provincia_id=provincia_id)

    if is_vat_referente(user):
        return base_qs.filter(oferta__centro__referente_id=user.id)

    return base_qs.none()


def filter_sesiones_queryset_for_user(base_qs: QuerySet, user) -> QuerySet:
    if is_vat_sse(user):
        return base_qs

    provincia_id = get_user_provincia_id(user)
    if provincia_id and is_vat_provincial(user):
        return base_qs.filter(comision__oferta__centro__provincia_id=provincia_id)

    if is_vat_referente(user):
        return base_qs.filter(comision__oferta__centro__referente_id=user.id)

    return base_qs.none()


def can_user_add_vat_entities(user) -> bool:
    return is_vat_sse(user)
