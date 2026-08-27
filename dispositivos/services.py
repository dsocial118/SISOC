from django.db.models import Q

from .boundary import DispositivosActor, get_geography_scope_map
from .models import Dispositivo


def get_dispositivos_queryset():
    return Dispositivo.objects.select_related("provincia", "municipio").order_by(
        "-created_at",
        "nombre_institucion",
    )


def apply_dispositivos_scope(queryset, actor: DispositivosActor):
    """Acota el queryset de dispositivos al alcance territorial del actor.

    - Sin usuario autenticado: queryset vacío.
    - Superusuario o usuario sin alcance provincial: sin restricción.
    - Usuario provincial: provincia y, si corresponde, municipio.

    El modelo ``Dispositivo`` no tiene localidad, por lo que un alcance a nivel
    localidad se respeta hasta su municipio (la granularidad más fina posible).
    Un usuario provincial sin alcances configurados no ve ningún registro.
    """
    if not actor.is_authenticated:
        return queryset.none()
    if actor.is_superuser:
        return queryset
    if not actor.is_territorial:
        return queryset

    if not actor.scopes:
        return queryset.none()

    scope_q = Q()
    for scope in actor.scopes:
        condiciones = {"provincia_id": scope.provincia_id}
        if scope.municipio_id:
            condiciones["municipio_id"] = scope.municipio_id
        scope_q |= Q(**condiciones)
    return queryset.filter(scope_q).distinct()


def get_dispositivos_geography_scope(actor: DispositivosActor | None):
    """Mapa ``provincia_id -> set(municipio_id) | None`` para acotar el formulario.

    Devuelve ``None`` si el usuario no tiene restricción territorial.
    """
    return get_geography_scope_map(actor)


def save_dispositivo_from_form(form, *, instance=None):
    dispositivo = form.save(commit=False)
    if instance is not None:
        dispositivo.pk = instance.pk
    dispositivo.save()
    return dispositivo


def delete_dispositivo(instance):
    instance.delete()
