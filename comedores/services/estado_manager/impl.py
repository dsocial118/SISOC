from __future__ import annotations

from django.db import transaction

from comedores.models import EstadoGeneral, EstadoHistorial


def registrar_cambio_estado(
    *,
    comedor,
    estado_general: EstadoGeneral | None = None,
    actividad=None,
    proceso=None,
    detalle=None,
    usuario=None,
):
    """
    Genera un nuevo historial para el comedor cuando cambia su estado.

    Permite recibir directamente una instancia de ``EstadoGeneral`` o bien los
    componentes necesarios para crearla en caso de que todavía no exista.
    """

    if not comedor or not getattr(comedor, "pk", None):
        raise ValueError("El comedor debe estar guardado antes de registrar su estado.")

    if estado_general is None:
        if actividad is None or proceso is None:
            raise ValueError(
                "Se requiere un estado de actividad y subestado para registrar el historial."
            )
        estado_general, _ = EstadoGeneral.objects.get_or_create(
            estado_actividad=actividad,
            estado_proceso=proceso,
            estado_detalle=detalle,
        )

    ultimo = getattr(comedor, "ultimo_estado", None)
    if ultimo and ultimo.estado_general_id == estado_general.id:
        return ultimo

    with transaction.atomic():
        historial = EstadoHistorial.objects.create(
            comedor=comedor,
            estado_general=estado_general,
            usuario=usuario,
        )
        comedor.ultimo_estado = historial
        comedor.save(update_fields=["ultimo_estado"])
        return historial
