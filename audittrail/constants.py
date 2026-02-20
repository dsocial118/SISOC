"""
Constantes compartidas para la integración de vistas de auditoría.
"""

TRACKED_MODELS = [
    ("comedores", "comedor", "Comedor"),
    ("centrodeinfancia", "centrodeinfancia", "Centro de Infancia"),
    ("relevamientos", "relevamiento", "Relevamiento"),
    ("ciudadanos", "ciudadano", "Ciudadano"),
    ("organizaciones", "organizacion", "Organización"),
]


def tracked_model_choices(include_blank: bool = True):
    """
    Devuelve choices listos para formularios (app.model -> etiqueta amigable).
    """
    choices = []
    if include_blank:
        choices.append(("", "Todos los modelos"))
    choices.extend((f"{app}.{model}", label) for app, model, label in TRACKED_MODELS)
    return choices
