from django.db.models import Q

from users.territorial_scope import get_effective_scopes, is_territorial_user

from .models import Dispositivo


def get_dispositivos_queryset():
    return Dispositivo.objects.select_related("provincia", "municipio").order_by(
        "-created_at",
        "nombre_institucion",
    )


def apply_dispositivos_scope(queryset, user):
    """Acota el queryset de dispositivos al alcance territorial del usuario.

    - Sin usuario autenticado: queryset vacío.
    - Superusuario o usuario sin alcance provincial: sin restricción.
    - Usuario provincial: provincia y, si corresponde, municipio.

    El modelo ``Dispositivo`` no tiene localidad, por lo que un alcance a nivel
    localidad se respeta hasta su municipio (la granularidad más fina posible).
    Un usuario provincial sin alcances configurados no ve ningún registro.
    """
    if not user or not getattr(user, "is_authenticated", False):
        return queryset.none()
    if getattr(user, "is_superuser", False):
        return queryset
    if not is_territorial_user(user):
        return queryset

    scopes = get_effective_scopes(user)
    if not scopes:
        return queryset.none()

    scope_q = Q()
    for scope in scopes:
        condiciones = {"provincia_id": scope.provincia_id}
        if scope.municipio_id:
            condiciones["municipio_id"] = scope.municipio_id
        scope_q |= Q(**condiciones)
    return queryset.filter(scope_q).distinct()


def get_dispositivos_geography_scope(user):
    """Mapa ``provincia_id -> set(municipio_id) | None`` para acotar el formulario.

    Devuelve ``None`` si el usuario no tiene restricción territorial (sin usuario,
    superusuario o usuario no provincial). Cuando el valor de una provincia es
    ``None`` significa que se permite la provincia completa; un ``set`` limita a
    esos municipios.
    """
    if not user or not getattr(user, "is_authenticated", False):
        return None
    if getattr(user, "is_superuser", False) or not is_territorial_user(user):
        return None

    restriccion = {}
    for scope in get_effective_scopes(user):
        provincia_id = scope.provincia_id
        if provincia_id in restriccion and restriccion[provincia_id] is None:
            continue
        if scope.municipio_id is None:
            restriccion[provincia_id] = None
        else:
            restriccion.setdefault(provincia_id, set()).add(scope.municipio_id)
    return restriccion


def save_dispositivo_from_form(form, *, instance=None):
    dispositivo = form.save(commit=False)
    if instance is not None:
        dispositivo.pk = instance.pk
    dispositivo.save()
    return dispositivo


def delete_dispositivo(instance):
    instance.delete()
