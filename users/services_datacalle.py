"""Servicios de los roles de DataCalle (SISOC - Mobile).

El rol vive en ``Profile.datacalle_rol`` y es la unica fuente de verdad:
administrador > coordinador > entrevistador, jerarquico y decreciente.

``Profile.es_relevador_calle`` se conserva por contrato con la app (D1.2 lo
expone en ``/api/users/me/``) pero **ya no decide nada**: significa "accede a
DataCalle" y lo tienen los tres roles. Quien necesite saber *que puede hacer*
un usuario, pregunta por el rol.
"""

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from core.models import Provincia
from users.profile_utils import get_profile_or_none
from users.territorial_scope import get_full_province_scope_ids


def is_relevador_calle_user(user) -> bool:
    """Indica si el usuario accede a DataCalle (SISOC - Mobile).

    Pese al nombre, hoy lo llevan los tres roles (administrador, coordinador y
    entrevistador): no depende de ``AccesoComedorPWA`` ni de
    ``es_usuario_provincial``, habilita el login mobile.
    """
    if not user or not getattr(user, "is_authenticated", False):
        return False
    profile = get_profile_or_none(user)
    return bool(getattr(profile, "es_relevador_calle", False))


def get_relevador_calle_rol(user) -> str:
    """Rol con el que el usuario opera en DataCalle (``""`` si no tiene ninguno).

    Devuelve rol para los tres (administrador, coordinador y entrevistador).
    """
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


def get_datacalle_rol(user) -> str:
    """Rol DataCalle del usuario, o ``""`` si no tiene ninguno."""
    if not user or not getattr(user, "is_authenticated", False):
        return ""
    profile = get_profile_or_none(user)
    return getattr(profile, "datacalle_rol", "") or ""


def tiene_acceso_datacalle(user) -> bool:
    """Si el usuario entra a la app. Los tres roles entran (matriz, punto 5)."""
    return get_datacalle_rol(user) in {
        "administrador",
        "coordinador",
        "entrevistador",
    }


def es_administrador_datacalle(user) -> bool:
    """Administrador Nacional: sin restriccion territorial."""
    return get_datacalle_rol(user) == "administrador"


def es_coordinador_datacalle(user) -> bool:
    """Gestiona operativos: coordinador provincial **o** administrador.

    La jerarquia es decreciente, asi que el superior incluye al inferior. El
    superusuario entra por arriba de todo: la version anterior de esta regla
    preguntaba por un permiso, y Django se lo concede siempre, asi que sin este
    bypass un superusuario sin grupo DataCalle perderia el cierre de operativos.
    """
    if getattr(user, "is_superuser", False):
        return True
    return get_datacalle_rol(user) in {"administrador", "coordinador"}


def es_solo_app(user) -> bool:
    """Relevador: no entra a SISOC (RN05)."""
    return get_datacalle_rol(user) == "entrevistador"


def get_datacalle_provincia_ids(user):
    """Provincias sobre las que opera, o ``None`` si son todas.

    ``None`` es "sin restriccion territorial" y solo lo devuelve el
    administrador; la lista vacia es "no puede operar en ninguna".
    """
    rol = get_datacalle_rol(user)
    if not rol:
        return []
    if rol == "administrador":
        return None
    if rol == "entrevistador":
        profile = get_profile_or_none(user)
        if not profile:
            return []
        return list(
            profile.relevador_calle_provincias.values_list("provincia_id", flat=True)
        )
    return get_full_province_scope_ids(user)


def get_relevador_calle_provincias(user) -> list[dict]:
    """Provincias de alcance del usuario en DataCalle, como ``[{id, nombre}]``.

    Sale de ``get_datacalle_provincia_ids``, que sabe de donde leer segun el rol:
    el entrevistador las tiene en ``relevador_calle_provincias`` y el coordinador
    en ``territorial_scopes``. Para el administrador devuelve el pais entero en
    vez de una lista vacia, que es lo que hacia antes y era falso.

    La forma no cambia (contrato D1.2), asi que la app no se entera.
    """
    provincia_ids = get_datacalle_provincia_ids(user)
    if provincia_ids is None:
        queryset = Provincia.objects.all()
    elif provincia_ids:
        queryset = Provincia.objects.filter(id__in=provincia_ids)
    else:
        return []
    return [
        {"id": provincia.id, "nombre": provincia.nombre}
        for provincia in queryset.order_by("nombre")
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
            profile__datacalle_rol="entrevistador",
            profile__relevador_calle_provincias__provincia_id=provincia_id,
        )
        .select_related("profile")
        .distinct()
        .order_by("first_name", "last_name", "username")
    )


def es_coordinador_calle(user) -> bool:
    """Alias historico de ``es_coordinador_datacalle``.

    Se conserva mientras queden llamadores; no agregar usos nuevos.
    """
    return es_coordinador_datacalle(user)


def get_relevadores_administrables(actor):
    """Entrevistadores que un coordinador de DataCalle puede administrar.

    QA-0016 y QA-0018: el coordinador da de alta y de baja a los entrevistadores
    de su provincia, así que tiene que verlos en el listado de usuarios. La
    delegación genérica (``grupos_asignables``) no sirve acá: el entrevistador
    no se marca con un grupo sino con ``datacalle_rol``, así que delegar un
    grupo le mostraría a todos los usuarios sin grupo del país. Esta regla es
    más angosta: sólo relevadores de DataCalle de sus provincias.

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
        profile__datacalle_rol="entrevistador",
        profile__relevador_calle_provincias__provincia_id__in=provincia_ids,
        is_staff=False,
        is_superuser=False,
    )


def validar_alcance_coordinador(profile):
    """RN01/D3: el coordinador provincial tiene exactamente una provincia completa.

    La decision del 2026-09-18 lo declara pero nadie lo verificaba: el alcance
    del coordinador vive en ``ProfileTerritorialScope``, tabla compartida que no
    se puede constrainear (otros roles del backoffice si admiten varias
    provincias), asi que el limite tiene que imponerse en el guardado.

    Se valida con el mismo lector que usa el runtime
    (``get_full_province_scope_ids``, que ademas exige
    ``es_usuario_provincial``): si el perfil no lo satisface, el coordinador
    terminaria viendo el pais entero en el backoffice y nada en la app.
    """
    if getattr(profile, "datacalle_rol", "") != "coordinador":
        return
    provincia_ids = get_full_province_scope_ids(profile)
    if len(provincia_ids) != 1:
        raise ValidationError(
            "Un Coordinador Provincial de DataCalle debe tener exactamente una "
            "provincia completa como alcance territorial."
        )
