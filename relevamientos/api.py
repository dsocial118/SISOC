"""Contrato Python público de Relevamientos para consumidores externos."""

from __future__ import annotations

from typing import Callable

from django.db.models.signals import post_delete, post_save

from core.soft_delete.signals import post_restore, post_soft_delete
from relevamientos.models import Prestacion, Relevamiento


def contar_relevamientos() -> int:
    """Devuelve la cantidad de relevamientos para indicadores externos."""

    return Relevamiento.objects.count()


def registrar_observador_dashboard(callback: Callable[[], None]) -> None:
    """Registra un observador de cambios de relevamientos y prestaciones."""

    def _notificar(**_kwargs):
        callback()

    uid_base = f"relevamientos.dashboard.{callback.__module__}.{callback.__name__}"
    for signal, sender, suffix in (
        (post_save, Relevamiento, "save-relevamiento"),
        (post_delete, Relevamiento, "delete-relevamiento"),
        (post_soft_delete, Relevamiento, "soft-delete-relevamiento"),
        (post_restore, Relevamiento, "restore-relevamiento"),
        (post_save, Prestacion, "save-prestacion"),
        (post_delete, Prestacion, "delete-prestacion"),
    ):
        signal.connect(
            _notificar,
            sender=sender,
            dispatch_uid=f"{uid_base}.{suffix}",
        )
