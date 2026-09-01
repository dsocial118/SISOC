"""Servicios del rol "Relevador DataCalle" (SISOC - Mobile).

Rol simple marcado con ``Profile.es_relevador_calle`` y alcance por provincia en
``RelevadorCalleProvincia``. Es el equivalente, para el modulo de situacion de
calle, de lo que ``services_pwa`` resuelve para comedores: habilita el login
mobile y expone el alcance provincial que la app usa para filtrar operativos.
"""

from core.models import Provincia
from users.profile_utils import get_profile_or_none


def is_relevador_calle_user(user) -> bool:
    """Indica si el usuario es relevador de DataCalle (SISOC - Mobile).

    No depende de ``AccesoComedorPWA`` ni de ``es_usuario_provincial``: habilita
    el login mobile del relevador de situacion de calle.
    """
    if not user or not getattr(user, "is_authenticated", False):
        return False
    profile = get_profile_or_none(user)
    return bool(getattr(profile, "es_relevador_calle", False))


def get_relevador_calle_provincia_ids(user) -> list[int]:
    """IDs de provincias de alcance de un relevador de DataCalle."""
    if not is_relevador_calle_user(user):
        return []
    profile = get_profile_or_none(user)
    if not profile:
        return []
    return list(
        profile.relevador_calle_provincias.values_list("provincia_id", flat=True)
    )


def get_relevador_calle_provincias(user) -> list[dict]:
    """Provincias de alcance del relevador como ``[{id, nombre}]`` (por nombre)."""
    provincia_ids = get_relevador_calle_provincia_ids(user)
    if not provincia_ids:
        return []
    return [
        {"id": provincia.id, "nombre": provincia.nombre}
        for provincia in Provincia.objects.filter(id__in=provincia_ids).order_by(
            "nombre"
        )
    ]
