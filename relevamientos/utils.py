"""Funciones auxiliares para la app ``relevamientos``.

Estas utilidades encapsulan lógica de transformación y consulta de datos,
permitiendo mantener el servicio principal enfocado en la orquestación.
"""

from typing import Any, Callable, Dict, Optional, Type

from django.db import models


def get_recursos(nombre: str, recursos_data: Dict[str, str], model: Type[models.Model]):
    """Obtener un queryset con los recursos existentes en la base de datos.

    Args:
        nombre: Clave en ``recursos_data`` con nombres separados por comas.
        recursos_data: Diccionario con datos crudos de los recursos.
        model: Clase de modelo de Django a consultar.

    Returns:
        QuerySet de instancias de ``model`` coincidentes o ``model.objects.none()``
        si ``nombre`` no está presente o es vacío.
    """
    recursos_str = recursos_data.pop(nombre, "")
    if recursos_str:
        recursos_arr = [n.strip() for n in recursos_str.split(",")]
        return model.objects.filter(nombre__in=recursos_arr)
    return model.objects.none()


def convert_to_boolean(value) -> bool:
    """
    Convierte varios tipos de valores a booleanos.
    Acepta strings ("Y", "N", "True", "False", "") y booleanos (True, False).
    """
    try:
        # Si ya es un booleano, devolverlo directamente
        if isinstance(value, bool):
            return value

        # Si es string, convertir según los mapeos conocidos
        if isinstance(value, str):
            # Mapeo para strings Y/N (formato GESTIONAR)
            if value in {"Y", "N", ""}:
                return {"Y": True, "N": False, "": False}[value]

            # Mapeo para strings True/False (formato JSON estándar)
            if value.lower() in ["true", "false"]:
                return value.lower() == "true"

        # Si llegamos aquí, el valor no es reconocido
        raise ValueError(
            f"Valor inesperado para booleano: {value} (tipo: {type(value)})"
        )

    except (KeyError, AttributeError) as exc:
        raise ValueError(
            f"Valor inesperado para booleano: {value} (tipo: {type(value)})"
        ) from exc


def get_object_or_none(
    model: Type[models.Model], field_name: str, value: Any
) -> Optional[models.Model]:
    """Obtener una instancia que coincida con ``field_name`` y ``value``.

    Si no existe una instancia o se encuentran múltiples, se devuelve ``None``.

    Args:
        model: Clase de modelo de Django a consultar.
        field_name: Nombre del campo para filtrar.
        value: Valor utilizado para el filtro.
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
    """Asignar valores desde ``data`` a ``instance`` y guardarla.

    Args:
        instance: Instancia de modelo a actualizar.
        data: Diccionario de nombres de campo y valores.

    Returns:
        La instancia actualizada.
    """
    for field, value in data.items():
        setattr(instance, field, value)
    instance.save()
    return instance


def populate_data(
    data: Dict[str, Any], transformations: Dict[str, Callable[[Any], Any]]
) -> Dict[str, Any]:
    """Aplicar funciones de transformación a ``data`` si las claves existen.

    Args:
        data: Diccionario con valores crudos.
        transformations: Mapeo de claves a funciones que transforman los valores
            correspondientes.

    Returns:
        El diccionario ``data`` con las transformaciones aplicadas.
    """
    for key, func in transformations.items():
        if key in data:
            data[key] = func(data[key])
    return data
