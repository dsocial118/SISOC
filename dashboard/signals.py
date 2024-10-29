from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from configuraciones.models import Alertas
from dashboard.models import Dashboard
from dashboard.utils import (
    contar_legajos_con_alarmas_activas,
    contar_legajos_con_planes_sociales,
    contar_legajos,
    contar_legajos_entre_0_y_18_anios,
    contar_legajos_entre_0_y_40_dias,
    contar_legajos_embarazados,
    contar_bb_riesgo,
    contar_adolescente_riesgo,
    contar_bb_sin_derivacion_aceptada,
    contar_adolescente_sin_derivacion_aceptada,
    contar_embarazos_sin_derivacion_aceptada,
    contar_embarazos_en_riesgo,
    deriv_pendientes,
)
from legajos.models import LegajoAlertas, Legajos, LegajosDerivaciones

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


def update_dashboard_legajos(sender, instance, **kwargs):
    """
    Ejecuta todas las operaciones para que el Dashboard tenga informacion en tiempo real.
    Guarda el resultado de dichas operaciones en el modelo Dashboard.
    """
    update_dashboard_key(
        "cantidad_legajos_con_alarmas_activas", contar_legajos_con_alarmas_activas()
    )
    update_dashboard_key(
        "cantidad_legajos_con_planes_sociales", contar_legajos_con_planes_sociales()
    )
    cantidad_total_legajos, cantidad_legajos_activos = contar_legajos()
    update_dashboard_key("cantidad_total_legajos", cantidad_total_legajos)
    update_dashboard_key("cantidad_legajos_activos", cantidad_legajos_activos)
    update_dashboard_key(
        "cantidad_legajos_entre_0_y_18_anios", contar_legajos_entre_0_y_18_anios()
    )
    update_dashboard_key("cantidad_legajos_40_dias", contar_legajos_entre_0_y_40_dias())
    update_dashboard_key("cantidad_legajos_embarazados", contar_legajos_embarazados())
    update_dashboard_key("cantidad_bb_riesgo", contar_bb_riesgo())
    update_dashboard_key("cantidad_adolescente_riesgo", contar_adolescente_riesgo())
    update_dashboard_key(
        "cantidad_bb_sin_derivacion_aceptada", contar_bb_sin_derivacion_aceptada()
    )
    update_dashboard_key(
        "cantidad_adolescente_sin_derivacion_aceptada",
        contar_adolescente_sin_derivacion_aceptada(),
    )
    update_dashboard_key(
        "embarazos_sin_derivacion_aceptada", contar_embarazos_sin_derivacion_aceptada()
    )
    update_dashboard_key("cantidad_embarazos_en_riesgo", contar_embarazos_en_riesgo())
    update_dashboard_key("cantidad_dv_pendientes", deriv_pendientes())


def register_signals():
    if (
        table_exists("legajos_legajos")
        and table_exists("legajos_legajoalertas")
        and table_exists("legajos_legajosderivaciones")
        and table_exists("configuraciones_alertas")
    ):

        @receiver(post_save, sender=Legajos)
        def trigger_update_legajo(sender, instance, **kwargs):
            return update_dashboard_legajos(sender, instance, **kwargs)

        @receiver(post_save, sender=LegajoAlertas)
        def trigger_update_legajoalertas(sender, instance, **kwargs):
            return update_dashboard_legajos(sender, instance, **kwargs)

        @receiver(post_save, sender=LegajosDerivaciones)
        def trigger_update_legajoderivaciones(sender, instance, **kwargs):
            return update_dashboard_legajos(sender, instance, **kwargs)

        @receiver(post_save, sender=Alertas)
        def trigger_update_alertas(sender, instance, **kwargs):
            return update_dashboard_legajos(sender, instance, **kwargs)

        @receiver(post_delete, sender=Legajos)
        def trigger_update_delete_legajo(sender, instance, **kwargs):
            return update_dashboard_legajos(sender, instance, **kwargs)

        @receiver(post_delete, sender=LegajoAlertas)
        def trigger_update_delete_legajoalertas(sender, instance, **kwargs):
            return update_dashboard_legajos(sender, instance, **kwargs)

        @receiver(post_delete, sender=LegajosDerivaciones)
        def trigger_update_delete_legajoderivaciones(sender, instance, **kwargs):
            return update_dashboard_legajos(sender, instance, **kwargs)

        @receiver(post_delete, sender=Alertas)
        def trigger_update_delete_alertas(sender, instance, **kwargs):
            return update_dashboard_legajos(sender, instance, **kwargs)


register_signals()
