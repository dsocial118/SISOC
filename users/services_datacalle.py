"""Servicios del rol "Relevador DataCalle" (SISOC - Mobile).

Rol simple marcado con ``Profile.es_relevador_calle`` y alcance por provincia en
``RelevadorCalleProvincia``. Es el equivalente, para el modulo de situacion de
calle, de lo que ``services_pwa`` resuelve para comedores: habilita el login
mobile y expone el alcance provincial que la app usa para filtrar operativos.
"""

from django.contrib.auth.models import User

from core.models import Provincia
from users.profile_utils import get_profile_or_none
from users.territorial_scope import get_full_province_scope_ids


def is_relevador_calle_user(user) -> bool:
    """Indica si el usuario es relevador de DataCalle (SISOC - Mobile).

    No depende de ``AccesoComedorPWA`` ni de ``es_usuario_provincial``: habilita
    el login mobile del relevador de situacion de calle.
    """
    if not user or not getattr(user, "is_authenticated", False):
        return False
    profile = get_profile_or_none(user)
    return bool(getattr(profile, "es_relevador_calle", False))


def get_relevador_calle_rol(user) -> str:
    """Rol con el que el usuario opera en DataCalle (``""`` si no es relevador)."""
    if not is_relevador_calle_user(user):
        return ""
    profile = get_profile_or_none(user)
    return getattr(profile, "datacalle_rol", "") or ""


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


def get_relevador_calle_users_for_provincia(provincia_id):
    """Entrevistadores de DataCalle con alcance en una provincia.

    Es la lista con la que el coordinador arma el equipo de un relevamiento.
    """
    if not provincia_id:
        return User.objects.none()
    return (
        User.objects.filter(
            is_active=True,
            profile__es_relevador_calle=True,
            profile__relevador_calle_provincias__provincia_id=provincia_id,
        )
        .select_related("profile")
        .distinct()
        .order_by("first_name", "last_name", "username")
    )


def es_coordinador_calle(user) -> bool:
    """Indica si el usuario gestiona operativos de DataCalle en el backoffice."""
    if not user or not getattr(user, "is_authenticated", False):
        return False
    return user.has_perm("datacalle.change_relevamiento")


def get_relevadores_administrables(actor):
    """Entrevistadores que un coordinador de DataCalle puede administrar.

    QA-0016 y QA-0018: el coordinador da de alta y de baja a los entrevistadores
    de su provincia, así que tiene que verlos en el listado de usuarios. La
    delegación genérica (``grupos_asignables``) no sirve acá: el entrevistador
    no se marca con un grupo sino con un flag, así que delegar un grupo le
    mostraría a todos los usuarios sin grupo del país. Esta regla es más
    angosta: sólo relevadores de DataCalle de sus provincias.

    El objetivo legítimo es un usuario *solo de la app*, que no entra al
    backoffice: ambos caminos de guardado fuerzan ``is_staff=False`` al marcar
    el flag (ver ``UserCreationForm._configure_created_user`` y
    ``CustomUserChangeForm.save``), y la importación masiva no toca el flag. Por
    eso se excluye al staff y a los superusuarios: sin eso, alcanzaría con que
    un usuario del backoffice estuviera además marcado como relevador en la
    provincia para que un coordinador pudiera editarlo —y el formulario de
    usuario permite fijar contraseña—. Marcar el flag degrada a no-staff, así
    que el filtro no puede dejar afuera a un entrevistador real.

    Devuelve ``None`` cuando el actor no es coordinador, para que quien llame
    no altere el alcance de los demás roles.
    """
    if not es_coordinador_calle(actor):
        return None
    provincia_ids = get_full_province_scope_ids(actor)
    if not provincia_ids:
        return None
    return User.objects.filter(
        profile__es_relevador_calle=True,
        profile__relevador_calle_provincias__provincia_id__in=provincia_ids,
        is_staff=False,
        is_superuser=False,
    )
