"""Utility helpers for the ``relevamientos`` app.

These functions encapsulate common data manipulation logic used by the
service layer to keep ``service.py`` focused on orchestration.
"""

from typing import Any, Callable, Dict, Optional, Type

from django.db import models


def get_recursos(nombre: str, recursos_data: Dict[str, str], model: Type[models.Model]):
    """Return a queryset of resources existing in the database.

    Args:
        nombre: Key in ``recursos_data`` with comma-separated resource names.
        recursos_data: Dictionary containing raw data with resource names.
        model: Django model class to query.

    Returns:
        Queryset of matching ``model`` instances or ``model.objects.none()`` when
        ``nombre`` is not present or empty.
    """
    recursos_str = recursos_data.pop(nombre, "")
    if recursos_str:
        recursos_arr = [n.strip() for n in recursos_str.split(",")]
        return model.objects.filter(nombre__in=recursos_arr)
    return model.objects.none()


def convert_to_boolean(value: str) -> bool:
    """Convert ``Y``/``N`` strings to boolean values.

    Args:
        value: String containing ``"Y"`` or ``"N"``.

    Returns:
        ``True`` if value is ``"Y"`` or ``False`` if ``"N"``.

    Raises:
        ValueError: If value is not ``"Y"`` or ``"N"``.
    """
    if value in {"Y", "N"}:
        return value == "Y"
    raise ValueError(f"Valor inesperado para booleano: {value}")


def get_object_or_none(
    model: Type[models.Model], field_name: str, value: Any
) -> Optional[models.Model]:
    """Return a model instance matching ``field_name`` and ``value``.

    If no instance exists or multiple are found, ``None`` is returned.

    Args:
        model: Django model class to query.
        field_name: Name of the field to filter.
        value: Value used for filtering.
    """
    try:
        return model.objects.get(**{field_name: value})
    except model.DoesNotExist:  # type: ignore[attr-defined]
        return None
    except model.MultipleObjectsReturned:  # type: ignore[attr-defined]
        return model.objects.filter(**{field_name: value}).first()


def assign_values_to_instance(
    instance: models.Model, data: Dict[str, Any]
) -> models.Model:
    """Assign values from ``data`` to ``instance`` and save it.

    Args:
        instance: Django model instance to update.
        data: Dictionary of field names and values.

    Returns:
        The updated instance.
    """
    for field, value in data.items():
        setattr(instance, field, value)
    instance.save()
    return instance


def populate_data(
    data: Dict[str, Any], transformations: Dict[str, Callable[[Any], Any]]
) -> Dict[str, Any]:
    """Apply transformation functions to ``data`` if keys are present.

    Args:
        data: Dictionary with raw values.
        transformations: Mapping of keys to callables used to transform the
            corresponding values.

    Returns:
        The ``data`` dictionary with transformations applied.
    """
    for key, func in transformations.items():
        if key in data:
            data[key] = func(data[key])
    return data
