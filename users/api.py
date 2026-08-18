"""Contrato Python público para capacidades de acceso PWA de Users."""

from __future__ import annotations

from django.contrib.auth import get_user_model

from users.models import AccesoComedorPWA, AccesoOrganizacionPWA
from users.services_pwa import (
    apply_comedor_organizacion_change,
    preview_organizacion_accesses,
    sync_organizacion_accesses,
)


def aplicar_cambio_organizacion_comedor(
    *,
    comedor_id: int,
    previous_organizacion_id: int | None,
    new_organizacion_id: int | None,
    actor_id: int | None = None,
) -> dict[str, int]:
    """Propaga un cambio de organización usando sólo identificadores estables."""
    actor = None
    if actor_id:
        actor = get_user_model().objects.filter(pk=actor_id).first()
    return apply_comedor_organizacion_change(
        comedor_id=comedor_id,
        previous_organizacion_id=previous_organizacion_id,
        new_organizacion_id=new_organizacion_id,
        actor=actor,
    )


def obtener_ids_organizaciones_con_acceso_pwa(
    organizacion_ids: tuple[int, ...] | None = None,
) -> tuple[int, ...]:
    """Devuelve organizaciones con membresías o proyecciones por reconciliar."""
    memberships = AccesoOrganizacionPWA.objects.filter(activo=True)
    projected_accesses = AccesoComedorPWA.objects.filter(
        activo=True,
        tipo_asociacion=AccesoComedorPWA.TIPO_ASOCIACION_ORGANIZACION,
        organizacion_id__isnull=False,
    )
    if organizacion_ids:
        requested_ids = set(organizacion_ids)
        memberships = memberships.filter(organizacion_id__in=requested_ids)
        projected_accesses = projected_accesses.filter(
            organizacion_id__in=requested_ids
        )
    resolved_ids = set(memberships.values_list("organizacion_id", flat=True))
    resolved_ids.update(
        projected_accesses.values_list("organizacion_id", flat=True)
    )
    return tuple(sorted(resolved_ids))


def previsualizar_accesos_organizacion(
    *, organizacion_id: int, comedor_ids: tuple[int, ...]
) -> dict[str, int]:
    """Calcula altas y bajas sin modificar las proyecciones de acceso."""
    return preview_organizacion_accesses(
        organizacion_id=organizacion_id,
        comedor_ids=comedor_ids,
    )


def sincronizar_accesos_organizacion(
    *, organizacion_id: int, comedor_ids: tuple[int, ...], actor_id: int | None = None
) -> dict[str, int]:
    """Reconcilia una organización dentro de una transacción independiente."""
    actor = None
    if actor_id:
        actor = get_user_model().objects.filter(pk=actor_id).first()
    return sync_organizacion_accesses(
        organizacion_id=organizacion_id,
        comedor_ids=comedor_ids,
        actor=actor,
    )
