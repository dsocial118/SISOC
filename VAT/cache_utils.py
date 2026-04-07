import logging

from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from core.soft_delete.signals import post_restore, post_soft_delete
from VAT.models import PlanVersionCurricular, TituloReferencia

logger = logging.getLogger("django")

PLANES_CENTRO_CACHE_VERSION_KEY = "vat:centro:cursos:planes:version"


def get_planes_centro_cache_version():
    """Devuelve la version actual del cache del panel de cursos por centro."""
    return int(cache.get(PLANES_CENTRO_CACHE_VERSION_KEY, 1))


def bump_planes_centro_cache_version():
    """Bumpea la version del cache para invalidar entradas previas."""
    current_version = get_planes_centro_cache_version()
    next_version = current_version + 1
    cache.set(PLANES_CENTRO_CACHE_VERSION_KEY, next_version, None)
    logger.debug(
        "Version de cache de planes curriculares actualizada a %s",
        next_version,
    )
    return next_version


@receiver([post_save, post_delete], sender=PlanVersionCurricular)
@receiver([post_save, post_delete], sender=TituloReferencia)
def invalidate_planes_centro_cache_on_save_or_delete(sender, **kwargs):
    """Invalida el cache cuando cambia un plan o su titulo asociado."""
    bump_planes_centro_cache_version()


@receiver([post_soft_delete, post_restore])
def invalidate_planes_centro_cache_on_soft_delete(sender, instance, **kwargs):
    """Invalida el cache cuando un plan o titulo se da de baja o se restaura."""
    if instance._meta.label_lower in {
        "vat.planversioncurricular",
        "vat.tituloreferencia",
    }:
        bump_planes_centro_cache_version()
