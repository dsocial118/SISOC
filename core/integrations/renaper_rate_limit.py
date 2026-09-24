"""Reserva turnos de consulta RENAPER entre todos los procesos SISOC."""

from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from core.models import RenaperConsultaRateLimit


def reserve_consulta_delay(*, requests_per_second: int) -> float:
    """Reserva un turno global y devuelve cuánto falta para poder consultar."""
    if requests_per_second <= 0:
        raise ValueError("El límite de consultas RENAPER debe ser positivo.")

    interval_us = (1_000_000 + requests_per_second - 1) // requests_per_second
    with transaction.atomic():
        limit = RenaperConsultaRateLimit.objects.select_for_update().get(pk=1)
        now = timezone.now()
        slot = max(now, limit.next_available_at)
        limit.next_available_at = slot + timedelta(microseconds=interval_us)
        limit.save(update_fields=["next_available_at"])
    return max((slot - now).total_seconds(), 0.0)
