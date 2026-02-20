from auditlog.registry import auditlog


def register_tracked_models():
    """
    Registra en django-auditlog los modelos de negocio críticos que se deben auditar.
    """
    from ciudadanos.models import Ciudadano
    from centrodeinfancia.models import CentroDeInfancia
    from comedores.models import Comedor
    from organizaciones.models import Organizacion
    from relevamientos.models import Relevamiento

    tracked_models = (
        (Comedor, ["fecha_creacion", "fecha_actualizacion"]),
        (CentroDeInfancia, ["fecha_creacion"]),
        (Relevamiento, ["fecha_creacion"]),
        (Ciudadano, ["creado", "modificado"]),
        (Organizacion, ["fecha_creacion"]),
    )

    for model, excluded_fields in tracked_models:
        if getattr(auditlog, "_registry", {}).get(model):
            continue
        auditlog.register(model, exclude_fields=excluded_fields)
