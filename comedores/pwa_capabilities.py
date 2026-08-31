"""Capacidades de Comedores expuestas al flujo PWA de usuarios."""

from comedores.models import Comedor
from comedores.services.capacitaciones_certificados_service import (
    is_alimentar_comunidad_program,
)
from users.pwa_comedores import registrar_capacidad_alimentar_comunidad


def es_comedor_alimentar_comunidad(comedor_id: int) -> bool:
    """Resuelve el programa del comedor sin exponer su modelo a `users`."""
    comedor = Comedor.objects.select_related("programa").filter(pk=comedor_id).first()
    return bool(comedor and is_alimentar_comunidad_program(comedor))


def registrar_capacidades_pwa() -> None:
    """Conecta las reglas de Comedores con los accesos PWA."""
    registrar_capacidad_alimentar_comunidad(es_comedor_alimentar_comunidad)
