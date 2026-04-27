"""Service layer for primer seguimiento de relevamiento."""

import logging

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404

from comedores.models import Comedor
from relevamientos.models import PrimerSeguimiento, Relevamiento
from relevamientos.service import _parse_territorial_payload
from relevamientos.tasks import (
    AsyncSendPrimerSeguimientoToGestionar,
    build_primer_seguimiento_payload,
)

logger = logging.getLogger("django")


class PrimerSeguimientoService:
    """Business rules for creating primer seguimiento instances."""

    ESTADOS_RELEVAMIENTO_COMPLETO = ("Finalizado", "Finalizado/Excepciones")

    @classmethod
    def _get_relevamiento_activo(cls, comedor):
        return (
            Relevamiento.objects.filter(comedor=comedor)
            .filter(
                Q(estado__isnull=True)
                | ~Q(estado__in=cls.ESTADOS_RELEVAMIENTO_COMPLETO)
            )
            .order_by("-fecha_creacion", "-id")
            .first()
        )

    @classmethod
    def _crear_ancla_local(cls, comedor):
        relevamiento = Relevamiento(comedor=comedor, estado="Pendiente")
        relevamiento._skip_gestionar_sync = True
        relevamiento.save()
        return relevamiento

    @classmethod
    def resolve_or_create_relevamiento_ancla(cls, comedor):
        return cls._get_relevamiento_activo(comedor) or cls._crear_ancla_local(comedor)

    @classmethod
    def create_asignado(cls, comedor_id, raw_territorial_data):
        territorial_uid, _territorial_nombre = _parse_territorial_payload(
            raw_territorial_data
        )
        comedor = get_object_or_404(Comedor, id=comedor_id)

        with transaction.atomic():
            relevamiento = cls.resolve_or_create_relevamiento_ancla(comedor)
            if PrimerSeguimiento.objects.filter(id_relevamiento=relevamiento).exists():
                raise ValidationError(
                    "Ya existe un primer seguimiento para el relevamiento activo."
                )

            seguimiento = PrimerSeguimiento.objects.create(
                id_relevamiento=relevamiento,
                tecnico=territorial_uid,
                estado=PrimerSeguimiento.ESTADO_ASIGNADO,
            )

        payload = build_primer_seguimiento_payload(seguimiento)
        AsyncSendPrimerSeguimientoToGestionar(seguimiento.id, payload).start()
        return seguimiento
