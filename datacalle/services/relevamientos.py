"""Lógica de negocio de los relevamientos de DataCalle.

El alcance es provincial: el coordinador sólo ve y gestiona los operativos de
su provincia (D2.1). Se apoya en el alcance territorial que ya usa el resto del
backoffice (``users.territorial_scope``).
"""

from django.contrib.auth.models import User
from django.db.models import Count

from core.models import Municipio, Provincia
from datacalle.models import Relevamiento
from dispositivos.models import Dispositivo
from users.territorial_scope import (
    get_full_province_scope_ids,
    get_geography_scope_map,
    is_territorial_user,
)


def get_relevamientos_queryset():
    return (
        Relevamiento.objects.select_related("provincia", "municipio", "dispositivo")
        .prefetch_related("equipo", "localidades")
        .annotate(cantidad_encuestas=Count("encuestas", distinct=True))
    )


def _provincia_ids_del_usuario(user):
    """Provincias sobre las que el usuario puede operar, o ``None`` si es todas."""
    if not user or not getattr(user, "is_authenticated", False):
        return []
    if getattr(user, "is_superuser", False) or not is_territorial_user(user):
        return None
    return get_full_province_scope_ids(user)


def apply_relevamientos_scope(queryset, user):
    """Acota el queryset a la provincia del usuario.

    - Sin usuario autenticado: vacío.
    - Superusuario o usuario sin alcance provincial: sin restricción.
    - Usuario provincial: sólo sus provincias; sin alcance configurado, nada.
    """
    provincia_ids = _provincia_ids_del_usuario(user)
    if provincia_ids is None:
        return queryset
    if not provincia_ids:
        return queryset.none()
    return queryset.filter(provincia_id__in=provincia_ids)


def get_provincias_para_usuario(user):
    """Provincias que el usuario puede elegir al planificar un operativo."""
    provincia_ids = _provincia_ids_del_usuario(user)
    queryset = Provincia.objects.all().order_by("nombre")
    if provincia_ids is None:
        return queryset
    return queryset.filter(id__in=provincia_ids)


def get_dispositivos_para_usuario(user):
    """Dispositivos de alojamiento que el usuario puede elegir."""
    queryset = Dispositivo.objects.all().order_by("nombre_institucion")
    provincia_ids = _provincia_ids_del_usuario(user)
    if provincia_ids is None:
        return queryset
    if not provincia_ids:
        return Dispositivo.objects.none()
    return queryset.filter(provincia_id__in=provincia_ids)


def get_dispositivos_para_provincia(user, provincia_id):
    """Dispositivos de una provincia concreta, dentro del alcance del usuario.

    QA-0010: el selector tiene que mostrar sólo los de la provincia elegida en
    la planificación, no todo el alcance del actor (que para un administrador
    nacional es el país entero).
    """
    if not provincia_id:
        return Dispositivo.objects.none()
    return get_dispositivos_para_usuario(user).filter(provincia_id=provincia_id)


def get_entrevistadores_para_usuario(user):
    """Entrevistadores de DataCalle dentro del alcance del actor.

    Es el universo máximo; el selector del formulario se acota además a la
    provincia elegida con ``get_entrevistadores_para_provincia``.
    """
    queryset = (
        User.objects.filter(is_active=True, profile__es_relevador_calle=True)
        .select_related("profile")
        .distinct()
        .order_by("first_name", "last_name", "username")
    )
    provincia_ids = _provincia_ids_del_usuario(user)
    if provincia_ids is None:
        return queryset
    if not provincia_ids:
        return User.objects.none()
    return queryset.filter(
        profile__relevador_calle_provincias__provincia_id__in=provincia_ids
    )


def get_entrevistadores_para_provincia(user, provincia_id):
    """Entrevistadores de una provincia concreta, dentro del alcance del actor.

    QA-0013: el equipo se arma sólo con relevadores de la provincia elegida.
    """
    if not provincia_id:
        return User.objects.none()
    return get_entrevistadores_para_usuario(user).filter(
        profile__relevador_calle_provincias__provincia_id=provincia_id
    )


def get_municipios_para_usuario(user, provincia_id):
    """Municipios de la provincia, respetando el alcance del coordinador.

    QA-0008: si el alcance territorial baja a municipio, el selector no puede
    ofrecer toda la provincia.
    """
    if not provincia_id:
        return Municipio.objects.none()
    queryset = Municipio.objects.filter(provincia_id=provincia_id).order_by("nombre")
    mapa = get_geography_scope_map(user)
    if mapa is None:
        return queryset
    municipios = mapa.get(int(provincia_id), False)
    if municipios is False:
        return Municipio.objects.none()
    if municipios is None:
        return queryset
    return queryset.filter(pk__in=municipios)


def save_relevamiento_from_form(form, *, user=None):
    relevamiento = form.save(commit=False)
    if relevamiento.creado_por_id is None and user is not None:
        relevamiento.creado_por = user
    relevamiento.full_clean(exclude=["creado_por"])
    relevamiento.save()
    form.save_m2m()
    return relevamiento


def delete_relevamiento(relevamiento, *, user=None):
    """Baja lógica: queda recuperable desde la papelera de SISOC."""
    relevamiento.delete(user=user)
    return relevamiento


def marcar_en_curso(relevamiento):
    """Pasa el operativo a ``en_curso`` con el primer caso cargado (D2.2)."""
    if relevamiento.estado != Relevamiento.Estado.PLANIFICADO:
        return relevamiento
    relevamiento.estado = Relevamiento.Estado.EN_CURSO
    relevamiento.save(update_fields=["estado", "updated_at"])
    return relevamiento


def resumen_por_estado(user):
    """Conteo de operativos por estado dentro del alcance del usuario."""
    queryset = apply_relevamientos_scope(Relevamiento.objects.all(), user)
    conteos = dict(
        queryset.values_list("estado").annotate(total=Count("id")).order_by()
    )
    return {
        "total": sum(conteos.values()),
        "por_estado": [
            {"valor": valor, "etiqueta": etiqueta, "total": conteos.get(valor, 0)}
            for valor, etiqueta in Relevamiento.Estado.choices
        ],
    }
