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
    AsyncSendRelevamientoToGestionar,
    build_primer_seguimiento_payload,
    build_relevamiento_payload,
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
    def _crear_ancla(cls, comedor, territorial_uid, territorial_nombre):
        """Crea el relevamiento ancla cuando no hay relevamiento inicial.

        Lleva el territorial elegido en el formulario, como un relevamiento
        asignado normal (estado ``Visita pendiente``). Se crea con
        ``_skip_gestionar_sync=True`` para que NO lo envie el signal: el envio a
        GESTIONAR lo hace ``create_asignado`` de forma sincronica y ORDENADA
        (relevamiento antes que seguimiento), porque el alta del seguimiento
        referencia este relevamiento por ``Id_Relevamiento`` y GESTIONAR lo
        necesita ya presente (incluso deriva el tecnico del relevamiento).
        """
        relevamiento = Relevamiento(
            comedor=comedor,
            estado="Visita pendiente",
            territorial_uid=territorial_uid,
            territorial_nombre=territorial_nombre,
        )
        relevamiento._skip_gestionar_sync = True  # pylint: disable=protected-access
        relevamiento.save()
        return relevamiento

    @classmethod
    def _resolver_relevamiento_y_tecnico(
        cls, comedor, relevamiento_id, raw_territorial_data
    ):
        """Resuelve el relevamiento ancla y el tecnico del seguimiento.

        - ``relevamiento_id`` informado (alta desde la fila de un relevamiento) o
          ancla activa ya existente: el territorial se HEREDA del relevamiento.
        - sin relevamiento previo: el territorial del formulario se aplica al
          nuevo ancla y al seguimiento.

        Devuelve ``(relevamiento, tecnico_uid, ancla_nueva)``. ``ancla_nueva`` es
        ``True`` solo cuando se creo un relevamiento ancla nuevo (hay que enviarlo
        a GESTIONAR antes que el seguimiento).
        """
        if relevamiento_id:
            relevamiento = get_object_or_404(
                Relevamiento, id=relevamiento_id, comedor=comedor
            )
            return relevamiento, relevamiento.territorial_uid, False

        existente = cls._get_relevamiento_activo(comedor)
        if existente is not None:
            return existente, existente.territorial_uid, False

        territorial_uid, territorial_nombre = _parse_territorial_payload(
            raw_territorial_data
        )
        relevamiento = cls._crear_ancla(comedor, territorial_uid, territorial_nombre)
        return relevamiento, territorial_uid, True

    @classmethod
    def create_asignado(cls, comedor_id, raw_territorial_data, relevamiento_id=None):
        comedor = get_object_or_404(Comedor, id=comedor_id)

        with transaction.atomic():
            relevamiento, tecnico, ancla_nueva = cls._resolver_relevamiento_y_tecnico(
                comedor, relevamiento_id, raw_territorial_data
            )
            if PrimerSeguimiento.objects.filter(id_relevamiento=relevamiento).exists():
                raise ValidationError(
                    "Ya existe un primer seguimiento para este relevamiento."
                )

            seguimiento = PrimerSeguimiento.objects.create(
                id_relevamiento=relevamiento,
                tecnico=tecnico,
                estado=PrimerSeguimiento.ESTADO_ASIGNADO,
            )

        # Si se creo un ancla nueva, primero aseguramos que el relevamiento exista
        # en GESTIONAR (envio sincronico), porque el alta del seguimiento lo
        # referencia. Recien despues enviamos el seguimiento.
        if ancla_nueva:
            AsyncSendRelevamientoToGestionar(
                relevamiento.id, build_relevamiento_payload(relevamiento)
            ).run()

        AsyncSendPrimerSeguimientoToGestionar(
            seguimiento.id, build_primer_seguimiento_payload(seguimiento)
        ).start()
        return seguimiento
