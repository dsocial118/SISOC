"""Contrato Python público de las capacidades compartidas de Comedores."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from django.db.models import Sum
from django.db.models.signals import post_delete, post_save

from comedores.models import Comedor, ValorComida
from core.soft_delete.signals import post_restore, post_soft_delete
from organizaciones.models import Organizacion


@dataclass(frozen=True)
class MetricasComedores:
    """Proyección de sólo lectura para consumidores externos del contexto."""

    cantidad_espacios: int
    presupuesto_desayuno: int | float
    presupuesto_merienda: int | float
    presupuesto_comida: int | float


def obtener_metricas_dashboard() -> MetricasComedores:
    """Devuelve los indicadores de Comedores que consume el Dashboard."""

    def _presupuesto(tipo: str):
        return (
            ValorComida.objects.filter(tipo=tipo).aggregate(total=Sum("valor"))["total"]
            or 0
        )

    return MetricasComedores(
        cantidad_espacios=Comedor.objects.count(),
        presupuesto_desayuno=_presupuesto("desayuno"),
        presupuesto_merienda=_presupuesto("merienda"),
        presupuesto_comida=_presupuesto("comida"),
    )


def registrar_observador_dashboard(callback: Callable[[], None]) -> None:
    """Registra un observador sin exponer los modelos o señales del dominio."""

    def _notificar(**_kwargs):
        callback()

    uid_base = f"comedores.dashboard.{callback.__module__}.{callback.__name__}"
    for signal, sender, suffix in (
        (post_save, Comedor, "save-comedor"),
        (post_delete, Comedor, "delete-comedor"),
        (post_soft_delete, Comedor, "soft-delete-comedor"),
        (post_restore, Comedor, "restore-comedor"),
        (post_save, ValorComida, "save-valor-comida"),
        (post_delete, ValorComida, "delete-valor-comida"),
    ):
        signal.connect(
            _notificar,
            sender=sender,
            dispatch_uid=f"{uid_base}.{suffix}",
        )


def obtener_ids_comedores() -> tuple[int, ...]:
    """Expone los identificadores de todos los comedores para adaptadores externos."""

    return tuple(Comedor.objects.values_list("pk", flat=True))


def obtener_ids_comedores_del_tecnico(user) -> tuple[int, ...]:
    """Expone los comedores asignados a las dúplas activas de un técnico."""

    duplas = user.dupla_tecnico.filter(estado="Activo")
    return tuple(Comedor.objects.filter(dupla__in=duplas).values_list("pk", flat=True))


def obtener_ids_organizaciones_de_comedores(
    comedor_ids: tuple[int, ...]
) -> tuple[int, ...]:
    """Expone las organizaciones vinculadas a una selección de comedores."""

    return tuple(
        Comedor.objects.filter(pk__in=comedor_ids, organizacion__isnull=False)
        .values_list("organizacion_id", flat=True)
        .distinct()
    )


def obtener_ids_organizaciones() -> tuple[int, ...]:
    """Expone los identificadores de todas las organizaciones."""

    return tuple(Organizacion.objects.values_list("pk", flat=True))
