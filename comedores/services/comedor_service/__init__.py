"""Servicio para gestión de comedores."""

from .impl import ComedorService, MENSAJE_ERROR_AGREGAR_NOMINA, messages, normalize_nomina_tab

__all__ = ["ComedorService", "MENSAJE_ERROR_AGREGAR_NOMINA", "messages", "normalize_nomina_tab"]
