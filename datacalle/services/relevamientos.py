"""Lógica de negocio de los relevamientos de DataCalle.

El alcance es provincial: el coordinador sólo ve y gestiona los operativos de
su provincia (D2.1). Se apoya en el alcance territorial que ya usa el resto del
backoffice (``users.territorial_scope``).
"""

from django.contrib.auth.models import User
from django.db.models import Count

from core.models import Provincia
from datacalle.models import Relevamiento
from dispositivos.models import Dispositivo
from users.territorial_scope import (
    get_full_province_scope_ids,
    is_territorial_user,
)


def get_relevamientos_queryset():
    return Relevamiento.objects.select_related(
        "provincia",
        "municipio",
        "localidad",
        "dispositivo",
    ).prefetch_related("equipo")


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


def get_entrevistadores_para_usuario(user):
    """Entrevistadores de DataCalle con los que el usuario puede armar equipo.

    Se filtra por el alcance del actor, no por la provincia elegida en el
    formulario: para un coordinador es exactamente el padrón de su provincia,
    así que no hace falta una cascada. Que el equipo corresponda a la provincia
    del operativo lo valida ``RelevamientoForm.clean``.
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
