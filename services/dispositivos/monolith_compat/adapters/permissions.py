"""Adaptador temporal de autorización de rutas del monolito."""

from core.decorators import permissions_any_required


def permisos_requeridos(permisos: list[str]):
    return permissions_any_required(permisos)
