"""Opciones de Organizaciones para formularios administrativos de Users."""

from organizaciones.models import Organizacion
from users.form_catalogs import registrar_queryset_formulario


def obtener_organizaciones_pwa():
    return Organizacion.objects.all().order_by("nombre")


def registrar_user_form_catalog() -> None:
    registrar_queryset_formulario("organizaciones_pwa", obtener_organizaciones_pwa)
