"""Revinculación automática de expedientes de pago al aparecer una admisión.

Medido sobre producción (2026-08-21): en 2025 el 97,7% de los expedientes de pago
resolvía su admisión, y en 2026 solo el 45%. La hipótesis más probable es de
tiempos — el expediente de pago se carga antes de que la admisión exista en
SISOC. Sin este reintento, esos casos quedarían en ``null`` para siempre aunque
la admisión se cargue después.
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from admisiones.models.admisiones import Admision

logger = logging.getLogger("django")


@receiver(post_save, sender=Admision)
def revincular_expedientes_pago(sender, instance, **kwargs):
    """Engancha los expedientes de pago sueltos del comedor de esta admisión.

    Nunca pisa un vínculo existente. Un fallo acá no debe impedir guardar la
    admisión, así que se registra y se sigue.
    """
    del sender, kwargs

    comedor_id = getattr(instance, "comedor_id", None)
    if not comedor_id:
        return

    try:
        from expedientespagos.vinculacion import revincular_expedientes_sueltos

        resultado = revincular_expedientes_sueltos(comedor=comedor_id)
        if resultado["vinculados"]:
            logger.info(
                "Expedientes de pago revinculados al guardar la admisión %s: %s",
                instance.pk,
                resultado["vinculados"],
            )
    except Exception:
        logger.exception(
            "Error al revincular expedientes de pago",
            extra={"admision_pk": instance.pk, "comedor_id": comedor_id},
        )
