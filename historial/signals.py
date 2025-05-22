from django.db.models.signals import pre_save, post_save, pre_delete
from django.dispatch import receiver
from django.forms.models import model_to_dict
from weakref import WeakKeyDictionary

from config.middlewares.threadlocals import get_current_user
from .async_handlers import log_action_async

_PRE_SAVE_CACHE = WeakKeyDictionary()

# Apps que no queremos que se registren
APPS_IGNORADAS = {
    "admin",
    "auth",
    "contenttypes",
    "sessions",
    "staticfiles",
    "historial",
    "dashboard",
}


@receiver(pre_save)
def cache_old_state(sender, instance, **kwargs):
    # Filtrar por app
    if sender._meta.app_label in APPS_IGNORADAS:
        return
    if instance.pk:
        try:
            old = sender.objects.get(pk=instance.pk)
            _PRE_SAVE_CACHE[instance] = model_to_dict(old)
        except sender.DoesNotExist:
            _PRE_SAVE_CACHE.pop(instance, None)


@receiver(post_save)
def log_create_update(sender, instance, created, **kwargs):
    if sender._meta.app_label in APPS_IGNORADAS:
        return

    usuario = get_current_user()
    new = model_to_dict(instance)
    old = _PRE_SAVE_CACHE.pop(instance, {}) if not created else {}
    diferencias = {
        k: {"old": old.get(k), "new": v} for k, v in new.items() if old.get(k) != v
    }

    accion = "crear" if created else "actualizar"
    log_action_async(usuario, accion, instance, diferencias)


@receiver(pre_delete)
def log_delete(sender, instance, **kwargs):
    if sender._meta.app_label in APPS_IGNORADAS:
        return

    usuario = get_current_user()
    diferencias = model_to_dict(instance)
    log_action_async(usuario, "eliminar", instance, diferencias)
