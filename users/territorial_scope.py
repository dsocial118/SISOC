from __future__ import annotations

from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q

from core.models import Localidad, Municipio, Provincia
from users.models import Profile, ProfileTerritorialScope


@dataclass(frozen=True)
class TerritorialScope:
    provincia_id: int
    municipio_id: int | None = None
    localidad_id: int | None = None
    profile_id: int | None = None
    persisted: bool = True

    @classmethod
    def from_model(cls, scope: ProfileTerritorialScope) -> "TerritorialScope":
        return cls(
            profile_id=scope.profile_id,
            provincia_id=scope.provincia_id,
            municipio_id=scope.municipio_id,
            localidad_id=scope.localidad_id,
            persisted=True,
        )

    @property
    def scope_key(self) -> str:
        return ProfileTerritorialScope.build_scope_key(
            self.provincia_id,
            self.municipio_id,
            self.localidad_id,
        )

    @property
    def is_full_province(self) -> bool:
        return self.municipio_id is None and self.localidad_id is None

    def as_dict(self) -> dict[str, int | None]:
        return {
            "provincia_id": self.provincia_id,
            "municipio_id": self.municipio_id,
            "localidad_id": self.localidad_id,
        }


def _profile_from_user_or_profile(user_or_profile) -> Profile | None:
    if isinstance(user_or_profile, Profile):
        return user_or_profile
    if not user_or_profile or not getattr(user_or_profile, "is_authenticated", False):
        return None
    user_id = getattr(user_or_profile, "pk", None)
    if not user_id:
        return None
    return Profile.objects.filter(user_id=user_id).first()


def is_territorial_user(user) -> bool:
    profile = _profile_from_user_or_profile(user)
    return bool(profile and profile.es_usuario_provincial)


def get_effective_scopes(user_or_profile) -> list[TerritorialScope]:
    """Devuelve scopes reales; usa `Profile.provincia` solo como fallback legacy."""
    profile = _profile_from_user_or_profile(user_or_profile)
    if not profile or not profile.es_usuario_provincial:
        return []

    if profile.pk:
        scopes = list(
            profile.territorial_scopes.order_by(
                "provincia_id",
                "municipio_id",
                "localidad_id",
            )
        )
        if scopes:
            return [TerritorialScope.from_model(scope) for scope in scopes]

    if profile.provincia_id:
        return [
            TerritorialScope(
                profile_id=profile.pk,
                provincia_id=profile.provincia_id,
                persisted=False,
            )
        ]
    return []


def serialize_profile_scopes(profile: Profile | None) -> list[dict[str, int | None]]:
    return [scope.as_dict() for scope in get_effective_scopes(profile)]


def get_full_province_scope_ids(user_or_profile) -> list[int]:
    return [
        scope.provincia_id
        for scope in get_effective_scopes(user_or_profile)
        if scope.is_full_province
    ]


def get_single_full_province_scope_id(user_or_profile) -> int | None:
    provincia_ids = get_full_province_scope_ids(user_or_profile)
    if len(provincia_ids) == 1:
        return provincia_ids[0]
    return None


def _parse_optional_id(value, field_name: str) -> int | None:
    if value in (None, ""):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError({field_name: "Seleccione una opción válida."}) from exc
    if parsed <= 0:
        raise ValidationError({field_name: "Seleccione una opción válida."})
    return parsed


def clean_territorial_scope_payload(payload) -> list[dict[str, int | None]]:
    if payload in (None, "", []):
        return []
    if not isinstance(payload, list):
        raise ValidationError("El formato de alcances territoriales no es válido.")

    cleaned = []
    seen_keys = set()
    for index, item in enumerate(payload, start=1):
        if not isinstance(item, dict):
            raise ValidationError(f"El alcance territorial #{index} no es válido.")

        provincia_id = _parse_optional_id(item.get("provincia_id"), "provincia")
        municipio_id = _parse_optional_id(item.get("municipio_id"), "municipio")
        localidad_id = _parse_optional_id(item.get("localidad_id"), "localidad")

        if not provincia_id:
            raise ValidationError(
                f"El alcance territorial #{index} debe tener provincia."
            )
        if localidad_id and not municipio_id:
            raise ValidationError(
                f"El alcance territorial #{index} requiere municipio para localidad."
            )

        provincia = Provincia.objects.filter(pk=provincia_id).first()
        if provincia is None:
            raise ValidationError(
                f"La provincia del alcance territorial #{index} no existe."
            )

        if municipio_id:
            municipio = Municipio.objects.filter(pk=municipio_id).first()
            if municipio is None:
                raise ValidationError(
                    f"El municipio del alcance territorial #{index} no existe."
                )
            if municipio.provincia_id != provincia_id:
                raise ValidationError(
                    f"El municipio del alcance territorial #{index} no pertenece a la provincia seleccionada."
                )

        if localidad_id:
            localidad = (
                Localidad.objects.select_related("municipio")
                .filter(pk=localidad_id)
                .first()
            )
            if localidad is None:
                raise ValidationError(
                    f"La localidad del alcance territorial #{index} no existe."
                )
            if localidad.municipio_id != municipio_id:
                raise ValidationError(
                    f"La localidad del alcance territorial #{index} no pertenece al municipio seleccionado."
                )
            if localidad.municipio.provincia_id != provincia_id:
                raise ValidationError(
                    f"La localidad del alcance territorial #{index} no pertenece a la provincia seleccionada."
                )

        scope_key = ProfileTerritorialScope.build_scope_key(
            provincia_id,
            municipio_id,
            localidad_id,
        )
        if scope_key in seen_keys:
            raise ValidationError(f"El alcance territorial #{index} está duplicado.")
        seen_keys.add(scope_key)
        cleaned.append(
            {
                "provincia_id": provincia_id,
                "municipio_id": municipio_id,
                "localidad_id": localidad_id,
            }
        )
    return cleaned


@transaction.atomic
def sync_profile_territorial_scopes(
    profile: Profile,
    scopes_data: list[dict[str, int | None]],
) -> None:
    if not profile.es_usuario_provincial:
        scopes_data = []

    scopes_data = clean_territorial_scope_payload(scopes_data)
    profile.territorial_scopes.all().delete()
    for scope_data in scopes_data:
        ProfileTerritorialScope.objects.create(
            profile=profile,
            provincia_id=scope_data["provincia_id"],
            municipio_id=scope_data["municipio_id"],
            localidad_id=scope_data["localidad_id"],
        )

    legacy_provincia_id = None
    if len(scopes_data) == 1 and not scopes_data[0]["municipio_id"]:
        legacy_provincia_id = scopes_data[0]["provincia_id"]
    if profile.provincia_id != legacy_provincia_id:
        profile.provincia_id = legacy_provincia_id
        profile.save(update_fields=["provincia"])


def build_territorial_scope_q(
    scopes: list[TerritorialScope],
    *,
    provincia_lookup: str,
    municipio_lookup: str | None = None,
    localidad_lookup: str | None = None,
) -> Q | None:
    scope_q = Q()
    has_scope = False
    for scope in scopes:
        conditions = {provincia_lookup: scope.provincia_id}
        if scope.localidad_id:
            if not municipio_lookup or not localidad_lookup:
                continue
            conditions[municipio_lookup] = scope.municipio_id
            conditions[localidad_lookup] = scope.localidad_id
        elif scope.municipio_id:
            if not municipio_lookup:
                continue
            conditions[municipio_lookup] = scope.municipio_id
        scope_q |= Q(**conditions)
        has_scope = True
    if not has_scope:
        return None
    return scope_q


def apply_territorial_scope(
    queryset,
    user,
    *,
    provincia_lookup: str,
    municipio_lookup: str | None = None,
    localidad_lookup: str | None = None,
    own_lookup: str | None = None,
    include_own: bool = False,
):
    if not user or not getattr(user, "is_authenticated", False):
        return queryset.none()
    if getattr(user, "is_superuser", False):
        return queryset
    if not is_territorial_user(user):
        return queryset

    scopes = get_effective_scopes(user)
    if not scopes:
        if own_lookup:
            return queryset.filter(**{own_lookup: user})
        return queryset.none()

    scope_q = build_territorial_scope_q(
        scopes,
        provincia_lookup=provincia_lookup,
        municipio_lookup=municipio_lookup,
        localidad_lookup=localidad_lookup,
    )
    if include_own and own_lookup:
        own_q = Q(**{own_lookup: user})
        scope_q = own_q if scope_q is None else scope_q | own_q

    if scope_q is None:
        return queryset.none()
    return queryset.filter(scope_q).distinct()


def apply_full_province_scope(
    queryset,
    user,
    *,
    provincia_lookup: str = "provincia_id",
    own_lookup: str | None = None,
):
    if not user or not getattr(user, "is_authenticated", False):
        return queryset.none()
    if getattr(user, "is_superuser", False):
        return queryset
    if not is_territorial_user(user):
        return queryset

    provincia_ids = get_full_province_scope_ids(user)
    if provincia_ids:
        return queryset.filter(**{f"{provincia_lookup}__in": provincia_ids})
    if own_lookup:
        return queryset.filter(**{own_lookup: user})
    return queryset.none()


def user_can_access_territory(
    user,
    *,
    provincia_id: int | None,
    municipio_id: int | None = None,
    localidad_id: int | None = None,
    owner=None,
) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return True
    if not is_territorial_user(user):
        return True

    scopes = get_effective_scopes(user)
    if not scopes:
        return bool(owner is not None and getattr(owner, "pk", owner) == user.pk)

    for scope in scopes:
        if scope.provincia_id != provincia_id:
            continue
        if scope.is_full_province:
            return True
        if scope.municipio_id != municipio_id:
            continue
        if scope.localidad_id is None:
            return True
        if scope.localidad_id == localidad_id:
            return True
    return False
