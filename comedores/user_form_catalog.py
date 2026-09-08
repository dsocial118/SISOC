"""Opciones de Comedores para formularios administrativos de Users."""

from comedores.models import Comedor
from users.form_catalogs import registrar_queryset_formulario


def obtener_comedores_pwa():
    return Comedor.objects.select_related("organizacion").order_by(
        "organizacion__nombre", "nombre"
    )


def registrar_user_form_catalog() -> None:
    registrar_queryset_formulario("comedores_pwa", obtener_comedores_pwa)
