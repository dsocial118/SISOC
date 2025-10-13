# custom_filters.py
from django import template
import pandas as pd
from datetime import datetime

register = template.Library()


@register.filter(name="has_group")
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()


@register.filter(name="safe_date")
def safe_date(value):
    """Filtro para manejar fechas NaT de pandas de forma segura"""
    if value is None:
        return ""
    
    # Verificar si es un valor NaT de pandas
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    
    # Si es una fecha válida, devolverla
    if isinstance(value, (datetime, pd.Timestamp)):
        try:
            # Verificar que no sea NaT antes de convertir
            if hasattr(value, 'date') and pd.notna(value):
                return value.date()
            elif hasattr(value, 'strftime') and pd.notna(value):
                return value
        except (ValueError, AttributeError):
            pass
    
    return str(value) if value else ""


@register.filter(name="safe_crispy")
def safe_crispy(field):
    """Filtro seguro para crispy forms que verifica que el campo sea válido"""
    if not field:
        return ""
    
    # Verificar que sea un campo de formulario válido
    if not hasattr(field, 'form'):
        return ""
    
    try:
        from crispy_forms.templatetags.crispy_forms_filters import as_crispy_field
        return as_crispy_field(field)
    except Exception:
        return str(field)
