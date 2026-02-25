from auditlog.registry import auditlog

from audittrail.constants import get_tracked_model_definitions


def register_tracked_models():
    """
    Registra en django-auditlog los modelos de negocio críticos que se deben auditar.
    """
    for definition in get_tracked_model_definitions():
        model = definition.get_model()
        if getattr(auditlog, "_registry", {}).get(model):
            continue
        auditlog.register(model, exclude_fields=definition.get_excluded_fields())
