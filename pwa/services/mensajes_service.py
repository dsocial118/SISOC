from django.db import transaction
from django.db.models import Prefetch, Q
from django.http import Http404
from django.utils import timezone

from comunicados.models import (
    Comunicado,
    EstadoComunicado,
    SubtipoComunicado,
    TipoComunicado,
)
from pwa.models import LecturaMensajePWA
from pwa.services.auditoria_operacion_service import registrar_evento_operacion
from users.services_pwa import get_accessible_comedor_ids


def _assert_user_has_comedor_access(*, user, comedor_id: int) -> None:
    if comedor_id not in set(get_accessible_comedor_ids(user)):
        raise Http404("Espacio no encontrado.")


def _visible_messages_queryset(*, comedor_id: int):
    return (
        Comunicado.objects.filter(
            tipo=TipoComunicado.EXTERNO,
            subtipo__in=(
                SubtipoComunicado.INSTITUCIONAL,
                SubtipoComunicado.COMEDORES,
            ),
            estado=EstadoComunicado.PUBLICADO,
        )
        .filter(
            Q(fecha_vencimiento__isnull=True) | Q(fecha_vencimiento__gt=timezone.now())
        )
        .filter(
            Q(subtipo=SubtipoComunicado.INSTITUCIONAL)
            | Q(
                subtipo=SubtipoComunicado.COMEDORES,
                para_todos_comedores=True,
            )
            | Q(
                subtipo=SubtipoComunicado.COMEDORES,
                comedores__id=comedor_id,
            )
        )
        .distinct()
        .order_by("-fecha_publicacion", "-fecha_creacion", "-id")
    )


def list_mensajes_for_espacio(*, comedor_id: int, user):
    _assert_user_has_comedor_access(user=user, comedor_id=comedor_id)
    accessible_comedor_ids = get_accessible_comedor_ids(user)
    lecturas_qs = LecturaMensajePWA.objects.filter(
        user=user,
        comedor_id__in=accessible_comedor_ids,
    ).order_by("-fecha_visto", "-id")
    return _visible_messages_queryset(comedor_id=comedor_id).prefetch_related(
        "adjuntos",
        Prefetch(
            "lecturas_pwa",
            queryset=lecturas_qs,
            to_attr="lecturas_pwa_usuario_espacio",
        ),
    )


def get_mensaje_for_espacio(*, comedor_id: int, comunicado_id: int, user) -> Comunicado:
    _assert_user_has_comedor_access(user=user, comedor_id=comedor_id)
    comunicado = (
        list_mensajes_for_espacio(comedor_id=comedor_id, user=user)
        .filter(pk=comunicado_id)
        .first()
    )
    if not comunicado:
        raise Http404("Mensaje no encontrado.")
    return comunicado


def _snapshot_lectura(lectura: LecturaMensajePWA) -> dict:
    return {
        "id": lectura.id,
        "comunicado_id": lectura.comunicado_id,
        "comedor_id": lectura.comedor_id,
        "user_id": lectura.user_id,
        "visto": lectura.visto,
        "fecha_visto": lectura.fecha_visto,
    }


@transaction.atomic
def marcar_mensaje_como_visto(*, comedor_id: int, comunicado_id: int, actor):
    comunicado = get_mensaje_for_espacio(
        comedor_id=comedor_id,
        comunicado_id=comunicado_id,
        user=actor,
    )
    now = timezone.now()

    if comunicado.subtipo == SubtipoComunicado.INSTITUCIONAL:
        lecturas = []
        first_lectura = None
        for accessible_comedor_id in get_accessible_comedor_ids(actor):
            lectura, created = LecturaMensajePWA.objects.get_or_create(
                comunicado=comunicado,
                comedor_id=accessible_comedor_id,
                user=actor,
                defaults={
                    "visto": True,
                    "fecha_visto": now,
                },
            )
            snapshot_antes = None if created else _snapshot_lectura(lectura)
            if not lectura.visto or not lectura.fecha_visto:
                lectura.visto = True
                lectura.fecha_visto = now
                lectura.save(
                    update_fields=["visto", "fecha_visto", "fecha_actualizacion"]
                )

            if created or not snapshot_antes or snapshot_antes["visto"] is False:
                registrar_evento_operacion(
                    actor=actor,
                    comedor_id=accessible_comedor_id,
                    entidad="mensaje_lectura",
                    entidad_id=lectura.id,
                    accion="create" if created else "update",
                    snapshot_antes=snapshot_antes,
                    snapshot_despues=_snapshot_lectura(lectura),
                    metadata={
                        "comunicado_id": comunicado.id,
                        "origen": "comunicados",
                    },
                )
            if first_lectura is None:
                first_lectura = lectura
            lecturas.append(lectura)
        comunicado.lecturas_pwa_usuario_espacio = lecturas
        return comunicado, first_lectura

    lectura, created = LecturaMensajePWA.objects.get_or_create(
        comunicado=comunicado,
        comedor_id=comedor_id,
        user=actor,
        defaults={
            "visto": True,
            "fecha_visto": now,
        },
    )
    snapshot_antes = None if created else _snapshot_lectura(lectura)
    if not lectura.visto or not lectura.fecha_visto:
        lectura.visto = True
        lectura.fecha_visto = now
        lectura.save(update_fields=["visto", "fecha_visto", "fecha_actualizacion"])

    if created or not snapshot_antes or snapshot_antes["visto"] is False:
        registrar_evento_operacion(
            actor=actor,
            comedor_id=comedor_id,
            entidad="mensaje_lectura",
            entidad_id=lectura.id,
            accion="create" if created else "update",
            snapshot_antes=snapshot_antes,
            snapshot_despues=_snapshot_lectura(lectura),
            metadata={
                "comunicado_id": comunicado.id,
                "origen": "comunicados",
            },
        )

    comunicado.lecturas_pwa_usuario_espacio = [lectura]
    return comunicado, lectura
