import re

from django.db import transaction
from django.db.models import Prefetch, Q
from django.http import Http404
from django.utils import timezone

from iam.services import user_has_permission_code
from comunicados.models import (
    Comunicado,
    EstadoComunicado,
    SubtipoComunicado,
    TipoComunicado,
)
from pwa.models import LecturaMensajePWA
from pwa.services.auditoria_operacion_service import registrar_evento_operacion
from rendicioncuentasmensual.models import RendicionCuentaMensual
from users.services_pwa import get_accessible_comedor_ids

MOBILE_RENDICION_PERMISSION_CODE = "rendicioncuentasmensual.manage_mobile_rendicion"
RENDICION_MESSAGE_ACTION_MARKER = "[SISOC_ACCION]rendicion_detalle:"
RENDICION_MESSAGE_ACTION_RE = re.compile(
    re.escape(RENDICION_MESSAGE_ACTION_MARKER) + r"(?P<rendicion_id>\d+)"
)


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


def _extract_rendicion_id_from_comunicado(comunicado) -> int | None:
    cuerpo = str(getattr(comunicado, "cuerpo", "") or "")
    match = RENDICION_MESSAGE_ACTION_RE.search(cuerpo)
    if not match:
        return None
    try:
        return int(match.group("rendicion_id"))
    except (TypeError, ValueError):
        return None


def _filter_out_finalized_rendicion_messages(items):
    rendicion_ids = {
        rendicion_id
        for item in items
        for rendicion_id in [_extract_rendicion_id_from_comunicado(item)]
        if rendicion_id is not None
    }
    if not rendicion_ids:
        return items

    finalizadas = set(
        RendicionCuentaMensual.objects.filter(
            id__in=rendicion_ids,
            estado=RendicionCuentaMensual.ESTADO_FINALIZADA,
        ).values_list("id", flat=True)
    )
    if not finalizadas:
        return items

    return [
        item
        for item in items
        if _extract_rendicion_id_from_comunicado(item) not in finalizadas
    ]


def list_mensajes_for_espacio(*, comedor_id: int, user):
    _assert_user_has_comedor_access(user=user, comedor_id=comedor_id)
    accessible_comedor_ids = get_accessible_comedor_ids(user)
    queryset = _visible_messages_queryset(comedor_id=comedor_id)
    if not user_has_permission_code(user, MOBILE_RENDICION_PERMISSION_CODE):
        queryset = queryset.exclude(cuerpo__contains=RENDICION_MESSAGE_ACTION_MARKER)
    lecturas_qs = LecturaMensajePWA.objects.filter(
        user=user,
        comedor_id__in=accessible_comedor_ids,
    ).order_by("-fecha_visto", "-id")
    items = list(
        queryset.prefetch_related(
            "adjuntos",
            Prefetch(
                "lecturas_pwa",
                queryset=lecturas_qs,
                to_attr="lecturas_pwa_usuario_espacio",
            ),
        )
    )
    return _filter_out_finalized_rendicion_messages(items)


def get_mensaje_for_espacio(*, comedor_id: int, comunicado_id: int, user) -> Comunicado:
    _assert_user_has_comedor_access(user=user, comedor_id=comedor_id)
    comunicado = next(
        (
            item
            for item in list_mensajes_for_espacio(comedor_id=comedor_id, user=user)
            if item.pk == comunicado_id
        ),
        None,
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
