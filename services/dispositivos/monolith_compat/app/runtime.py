"""Resuelve los puertos de ejecución configurados por cada host."""

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string


def _get_callable(setting_name):
    try:
        dotted_path = getattr(settings, setting_name)
    except AttributeError as exc:
        raise ImproperlyConfigured(
            f"Falta configurar {setting_name} para ejecutar Dispositivos."
        ) from exc
    return import_string(dotted_path)


def actor_from_user(user):
    return _get_callable("DISPOSITIVOS_ACTOR_FROM_USER")(user)


def get_territorial_catalog():
    return _get_callable("DISPOSITIVOS_TERRITORIAL_CATALOG")()


def apply_advanced_filters(queryset, request):
    return _get_callable("DISPOSITIVOS_ADVANCED_FILTERS")(queryset, request)


def get_favorite_filters_section():
    return _get_callable("DISPOSITIVOS_FAVORITE_FILTERS_SECTION")()


def register_favorite_filters() -> None:
    _get_callable("DISPOSITIVOS_REGISTER_FAVORITE_FILTERS")()


def required_permissions(permissions: list[str]):
    return _get_callable("DISPOSITIVOS_REQUIRED_PERMISSIONS")(permissions)
