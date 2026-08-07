"""Opciones de Duplas para formularios administrativos de Users."""

from duplas.models import Dupla
from users.form_catalogs import registrar_queryset_formulario


def obtener_duplas_asignadas():
    return Dupla.objects.activas()


def registrar_user_form_catalog() -> None:
    registrar_queryset_formulario("duplas_asignadas", obtener_duplas_asignadas)
