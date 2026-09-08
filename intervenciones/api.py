"""Contrato Python público para los catálogos de Intervenciones."""

from __future__ import annotations

from dataclasses import dataclass

from intervenciones.constants import PROGRAMA_ALIASES_CENTRO_INFANCIA
from intervenciones.models.intervenciones import (
    SubIntervencion,
    TipoDestinatario,
    TipoIntervencion,
)


@dataclass(frozen=True)
class ConfiguracionFormularioCDI:
    """Opciones autorizadas para un formulario de intervención de CDI."""

    tipos: object
    subtipos: object
    destinatario_fijo: object | None


def programa_aliases_cdi() -> tuple[str, ...]:
    """Devuelve los alias del catálogo que corresponden a Centro de Infancia."""

    return tuple(PROGRAMA_ALIASES_CENTRO_INFANCIA)


def obtener_configuracion_formulario_cdi(
    tipo_seleccionado_id: int | None,
    subtipo_seleccionado_id: int | None,
    destinatario_fijo_nombre: str | None = None,
) -> ConfiguracionFormularioCDI:
    """Resuelve catálogos de CDI sin exponer imports a los consumidores."""

    destinatario_fijo = None
    if destinatario_fijo_nombre:
        destinatario_fijo = TipoDestinatario.objects.filter(
            nombre__iexact=destinatario_fijo_nombre
        ).first()
    return ConfiguracionFormularioCDI(
        tipos=TipoIntervencion.para_programas(
            *PROGRAMA_ALIASES_CENTRO_INFANCIA,
            include_ids=[tipo_seleccionado_id] if tipo_seleccionado_id else None,
        ),
        subtipos=SubIntervencion.para_tipo(
            tipo_seleccionado_id,
            include_ids=[subtipo_seleccionado_id] if subtipo_seleccionado_id else None,
        ),
        destinatario_fijo=destinatario_fijo,
    )
