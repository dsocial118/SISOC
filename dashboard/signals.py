from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from comedores.models.relevamiento import Relevamiento
from comedores.models.relevamiento import Prestacion
from comedores.models.comedor import Comedor, ValorComida
from dashboard.models import Dashboard
from dashboard.utils import (
    contar_comedores_activos,
    contar_relevamientos_activos,
    calcular_presupuesto_desayuno,
    calcular_presupuesto_merienda,
    calcular_presupuesto_comida,
)

from .utils import table_exists


def update_dashboard_key(llave, cantidad):
    """
    Actualiza o crea un elemento del Dashboard para el concepto deseado con la cantidad recibida

    :param llave: Concepto en el Dashboard
    :param cantidad: Cantidad a definir del concepto en el Dashboard
    """
    dashboard = Dashboard.objects.update_or_create(
        llave=llave,
        defaults={"cantidad": cantidad},
    )
    return dashboard


def update_dashboard_comedores(sender, instance, **kwargs):
    update_dashboard_key("cantidad_comedores_activos", contar_comedores_activos())
    update_dashboard_key(
        "cantidad_relevamientos_activos", contar_relevamientos_activos()
    )
    # update_dashboard_key("cantidad_beneficiarios", contar_beneficiarios())
    update_dashboard_key("presupuesto_desayuno", calcular_presupuesto_desayuno())
    update_dashboard_key("presupuesto_merienda", calcular_presupuesto_merienda())
    update_dashboard_key("presupuesto_comida", calcular_presupuesto_comida())


def register_signals():
    if (
        table_exists("comedores_comedor")
        and table_exists("comedores_relevamiento")
        and table_exists("comedores_prestacion")
        and table_exists("comedores_valorcomida")
    ):

        @receiver(post_save, sender=Comedor)
        def trigger_update_comedor(sender, instance, **kwargs):
            return update_dashboard_comedores(sender, instance, **kwargs)

        @receiver(post_save, sender=Relevamiento)
        def trigger_update_relevamiento(sender, instance, **kwargs):
            return update_dashboard_comedores(sender, instance, **kwargs)

        @receiver(post_save, sender=Prestacion)
        def trigger_update_prestacion(sender, instance, **kwargs):
            return update_dashboard_comedores(sender, instance, **kwargs)

        @receiver(post_save, sender=ValorComida)
        def trigger_update_valorcomida(sender, instance, **kwargs):
            return update_dashboard_comedores(sender, instance, **kwargs)

        @receiver(post_delete, sender=Comedor)
        def trigger_update_delete_comedor(sender, instance, **kwargs):
            return update_dashboard_comedores(sender, instance, **kwargs)

        @receiver(post_delete, sender=Relevamiento)
        def trigger_update_delete_relevamiento(sender, instance, **kwargs):
            return update_dashboard_comedores(sender, instance, **kwargs)

        @receiver(post_delete, sender=Prestacion)
        def trigger_update_delete_prestacion(sender, instance, **kwargs):
            return update_dashboard_comedores(sender, instance, **kwargs)

        @receiver(post_delete, sender=ValorComida)
        def trigger_update_delete_valorcomida(sender, instance, **kwargs):
            return update_dashboard_comedores(sender, instance, **kwargs)


register_signals()
