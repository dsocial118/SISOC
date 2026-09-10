from django.db import transaction
from django.db.models import Q

from core.services.advanced_filters import AdvancedFilterEngine
from pas.models import PasHistorialEstado, PasPersona
from pas.services.filter_config import (
    CHOICE_OPS,
    FIELD_MAP,
    FIELD_TYPES,
    NUM_OPS,
    TEXT_OPS,
)
from pas.services.ddjj_service import asegurar_invitacion_vigente


PAS_ADVANCED_FILTER = AdvancedFilterEngine(
    field_map=FIELD_MAP,
    field_types=FIELD_TYPES,
    allowed_ops={
        "text": TEXT_OPS,
        "number": NUM_OPS,
        "choice": CHOICE_OPS,
    },
)


def get_personas_filtradas(request_or_get):
    queryset = (
        PasPersona.objects.select_related("provincia", "municipio", "estado")
        .prefetch_related("avisos")
        .order_by("apellidos", "nombres", "id")
    )
    params = getattr(request_or_get, "GET", request_or_get)
    query = str(params.get("q") or "").strip()
    estado = str(params.get("estado") or "").strip()

    if query:
        search_filter = (
            Q(apellidos__icontains=query)
            | Q(nombres__icontains=query)
            | Q(cuit__icontains=query)
        )
        if query.isdigit():
            search_filter |= Q(dni=int(query)) | Q(id_persona=int(query))
        queryset = queryset.filter(search_filter)

    if estado:
        queryset = queryset.filter(estado__nombre__iexact=estado)

    return PAS_ADVANCED_FILTER.filter_queryset(queryset, params).distinct()


@transaction.atomic
def registrar_persona(form, usuario=None):
    persona = form.save(commit=False)
    persona.estado = form.cleaned_data["estado"]
    persona.save()
    form.save_m2m()
    persona.avisos.set(form.cleaned_data["avisos"])

    historial = PasHistorialEstado.objects.create(
        persona=persona,
        estado_anterior=None,
        estado_nuevo=persona.estado,
        usuario=usuario,
    )
    historial.avisos_nuevos.set(form.cleaned_data["avisos"])
    asegurar_invitacion_vigente(persona, usuario=usuario)
    return persona


@transaction.atomic
def cambiar_estado(persona, form, usuario=None):
    estado_anterior = persona.estado
    avisos_anteriores = list(persona.avisos.all())
    estado_nuevo = form.cleaned_data["estado"]
    avisos_nuevos = list(form.cleaned_data["avisos"])

    persona.estado = estado_nuevo
    persona.save(update_fields=["estado", "fecha_actualizacion"])
    persona.avisos.set(avisos_nuevos)

    historial = PasHistorialEstado.objects.create(
        persona=persona,
        estado_anterior=estado_anterior,
        estado_nuevo=estado_nuevo,
        usuario=usuario,
    )
    historial.avisos_anteriores.set(avisos_anteriores)
    historial.avisos_nuevos.set(avisos_nuevos)
    return persona
