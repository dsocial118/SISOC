from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction

from Configuraciones.models import Alertas
from Dashboard.models import Dashboard
from Dashboard.utils import *
from Legajos.models import LegajoAlertas, Legajos, LegajosDerivaciones


def actualizar_dashboard(llave, cantidad):
    """
    Actualiza o crea un elemento del Dashboard para el concepto deseado con la cantidad recibida
    
    :param llave: Concepto en el Dashboard
    :param cantidad: Cantidad a definir del concepto en el Dashboard
    """
    dashboard = Dashboard.objects.update_or_create(
        llave=llave,
        defaults={'cantidad': cantidad},
    )
    return dashboard


def actualizar_todo_dashboard():
    """
    Ejecuta todas las operaciones para que el Dashboard tenga informacion en tiempo real.
    Guarda el resultado de dichas operaciones en el modelo Dashboard.
    """
    with transaction.atomic():
        actualizar_dashboard('cantidad_legajos_con_alarmas_activas', contar_legajos_con_alarmas_activas())
        actualizar_dashboard('cantidad_legajos_con_planes_sociales', contar_legajos_con_planes_sociales())
        cantidad_total_legajos, cantidad_legajos_activos = contar_legajos()
        actualizar_dashboard('cantidad_total_legajos', cantidad_total_legajos)
        actualizar_dashboard('cantidad_legajos_activos', cantidad_legajos_activos)
        actualizar_dashboard('cantidad_legajos_entre_0_y_18_anios', contar_legajos_entre_0_y_18_anios())
        actualizar_dashboard('cantidad_legajos_40_dias', contar_legajos_entre_0_y_40_dias())
        actualizar_dashboard('cantidad_legajos_embarazados', contar_legajos_embarazados())
        actualizar_dashboard('cantidad_bb_riesgo', contar_bb_riesgo())
        actualizar_dashboard('cantidad_adolescente_riesgo', contar_adolescente_riesgo())
        actualizar_dashboard('cantidad_bb_sin_derivacion_aceptada', contar_bb_sin_derivacion_aceptada())
        actualizar_dashboard('cantidad_adolescente_sin_derivacion_aceptada', contar_adolescente_sin_derivacion_aceptada())
        actualizar_dashboard('embarazos_sin_derivacion_aceptada', contar_embarazos_sin_derivacion_aceptada())
        actualizar_dashboard('cantidad_embarazos_en_riesgo', contar_embarazos_en_riesgo())
        actualizar_dashboard('cantidad_dv_pendientes', deriv_pendientes())

@receiver(post_save, sender=Legajos)
@receiver(post_save, sender=LegajoAlertas)
@receiver(post_save, sender=LegajosDerivaciones)
@receiver(post_save, sender=Alertas)
@receiver(post_delete, sender=Legajos)
@receiver(post_delete, sender=LegajoAlertas)
@receiver(post_delete, sender=LegajosDerivaciones)
@receiver(post_delete, sender=Alertas)
def actualizar_valores_dashboard(sender, instance, **kwargs):
    actualizar_todo_dashboard()