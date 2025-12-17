from django import template
from datetime import date

register = template.Library()


@register.filter
def edad(fecha_nacimiento):
    """Calcula la edad en años a partir de una fecha de nacimiento"""
    if not fecha_nacimiento:
        return None

    today = date.today()
    return (
        today.year
        - fecha_nacimiento.year
        - ((today.month, today.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
    )


@register.filter
def es_menor_18(fecha_nacimiento):
    """Verifica si una persona es menor de 18 años"""
    if not fecha_nacimiento:
        return False

    edad_actual = edad(fecha_nacimiento)
    return edad_actual is not None and edad_actual < 18
