from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from configuraciones.models import Alertas
from dashboard.services import DashboardService
from legajos.models import LegajoAlertas, Legajos, LegajosDerivaciones

from .utils import table_exists


def update_dashboard(sender, instance, **kwargs):
    DashboardService.ejecutar_actualizaciones_legajos()


def register_signals():
    if (
        table_exists("legajos_legajos")
        and table_exists("legajos_legajoalertas")
        and table_exists("legajos_legajosderivaciones")
        and table_exists("configuraciones_alertas")
    ):

        @receiver(post_save, sender=Legajos)
        def trigger_update_legajo(sender, instance, **kwargs):
            return update_dashboard(sender, instance, **kwargs)

        @receiver(post_save, sender=LegajoAlertas)
        def trigger_update_legajoalertas(sender, instance, **kwargs):
            return update_dashboard(sender, instance, **kwargs)

        @receiver(post_save, sender=LegajosDerivaciones)
        def trigger_update_legajoderivaciones(sender, instance, **kwargs):
            return update_dashboard(sender, instance, **kwargs)

        @receiver(post_save, sender=Alertas)
        def trigger_update_alertas(sender, instance, **kwargs):
            return update_dashboard(sender, instance, **kwargs)

        @receiver(post_delete, sender=Legajos)
        def trigger_update_delete_legajo(sender, instance, **kwargs):
            return update_dashboard(sender, instance, **kwargs)

        @receiver(post_delete, sender=LegajoAlertas)
        def trigger_update_delete_legajoalertas(sender, instance, **kwargs):
            return update_dashboard(sender, instance, **kwargs)

        @receiver(post_delete, sender=LegajosDerivaciones)
        def trigger_update_delete_legajoderivaciones(sender, instance, **kwargs):
            return update_dashboard(sender, instance, **kwargs)

        @receiver(post_delete, sender=Alertas)
        def trigger_update_delete_alertas(sender, instance, **kwargs):
            return update_dashboard(sender, instance, **kwargs)


register_signals()
