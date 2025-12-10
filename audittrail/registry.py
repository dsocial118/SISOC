from auditlog.registry import auditlog


def register_tracked_models():
    """
    Registra en django-auditlog los modelos de negocio críticos que se deben auditar.
    """
    from ciudadanos.models import Ciudadano  # pylint: disable=import-outside-toplevel
    from comedores.models import Comedor  # pylint: disable=import-outside-toplevel
    from organizaciones.models import (
        Organizacion,
    )  # pylint: disable=import-outside-toplevel
    from relevamientos.models import (
        Relevamiento,
    )  # pylint: disable=import-outside-toplevel

    tracked_models = (
        (Comedor, ["fecha_creacion", "fecha_actualizacion"]),
        (Relevamiento, ["fecha_creacion"]),
        (Ciudadano, ["creado", "modificado"]),
        (Organizacion, ["fecha_creacion"]),
    )

    for model, excluded_fields in tracked_models:
        if getattr(auditlog, "_registry", {}).get(model):
            continue
        auditlog.register(model, exclude_fields=excluded_fields)
