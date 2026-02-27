from auditlog.registry import auditlog

from audittrail.constants import get_tracked_model_definitions


def register_tracked_models():
    """
    Registra en django-auditlog los modelos de negocio críticos que se deben auditar.
    """
    for definition in get_tracked_model_definitions():
        model = definition.get_model()
        registry = getattr(auditlog, "_registry", {})
        try:
            already_registered = model in registry
        except TypeError:
            already_registered = False

        if already_registered:
            continue
        auditlog.register(model, exclude_fields=definition.get_excluded_fields())
