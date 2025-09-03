from django import template

register = template.Library()


@register.inclusion_tag("hitos/hito_row.html")
def render_hito(hitos, fechas_hitos, campo, descripcion, comedor, es_tecnico_comedor):
    """
    Template tag para renderizar una fila de hito de manera consistente.

    Args:
        hitos: Objeto con los hitos del comedor
        fechas_hitos: Diccionario con las fechas de cada hito
        campo: Nombre del campo del hito (ej: 'retiro_tarjeta')
        descripcion: Descripción legible del hito (ej: 'Retiro de Tarjeta')
        comedor: Objeto comedor
        es_tecnico_comedor: Boolean indicando si el usuario puede restaurar

    Returns:
        Dict con el contexto para el template
    """
    hito_completado = getattr(hitos, campo, False) if hitos else False
    fecha_hito = fechas_hitos.get(campo) if fechas_hitos else None

    return {
        "campo": campo,
        "descripcion": descripcion,
        "hito_completado": hito_completado,
        "fecha_hito": fecha_hito,
        "comedor": comedor,
        "es_tecnico_comedor": es_tecnico_comedor,
    }
