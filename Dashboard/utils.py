from datetime import date, timedelta

from Configuraciones.models import Alertas
from Legajos.models import LegajoAlertas, Legajos, LegajosDerivaciones

#FIXME: Este modulo puede ser optimizado mas aun

today = date.today()
fecha_hace_18_anios = today - timedelta(days=18 * 365)
fecha_hace_40_dias = today - timedelta(days=40)

total_legajos = Legajos.objects.select_related('dimensioneconomia').prefetch_related('m2m_alertas').values(
    'estado',
    'fecha_nacimiento',
    'dimensioneconomia__m2m_planes'
)

alertas_embarazo_ids = Alertas.objects.filter(fk_categoria__nombre__istartswith='embarazo').values_list('id', flat=True)
legajos_con_alerta_embarazo = total_legajos.filter(m2m_alertas__id__in=alertas_embarazo_ids)
alarmas_activas = Alertas.objects.filter(gravedad='Critica').values_list('id')

legajos_mayores_de_edad = total_legajos.filter(fecha_nacimiento__gte=fecha_hace_18_anios)

legajos_40_dias = total_legajos.filter(fecha_nacimiento__gte=fecha_hace_40_dias)        

def contar_legajos():
    cantidad_total_legajos = total_legajos.count()
    legajos_activos = total_legajos.filter(estado=True)    
    cantidad_legajos_activos = legajos_activos.count()
    
    return  cantidad_total_legajos, cantidad_legajos_activos

def contar_legajos_entre_0_y_18_anios():
    # Realiza una consulta para contar los legajos que tienen entre 0 y 18 años
    return legajos_mayores_de_edad.count()

def contar_adolescente_riesgo():
    # FIXME: Los adolescentes son todos los mayores de edad?
    return legajos_mayores_de_edad.filter(m2m_alertas__in=alarmas_activas).distinct().count()

def contar_adolescente_sin_derivacion_aceptada():
    # calculo de adolescente con estado de derivación diferente a "Aceptada"
    return legajos_mayores_de_edad.exclude(legajosderivaciones__estado='Aceptada').distinct().count()

def contar_legajos_entre_0_y_40_dias():
    # Realiza una consulta para contar los legajos que tienen entre 0 y 40 días
    return legajos_40_dias.distinct().count()

def contar_bb_riesgo():
    # Realiza la consulta para contar los bebés con alarmas activas
    return legajos_40_dias.filter(m2m_alertas__in=alarmas_activas).distinct().count()

def contar_bb_sin_derivacion_aceptada():
    # calculo de legajos con estado de derivación diferente a "Aceptada"
    return legajos_40_dias.exclude(legajosderivaciones__estado='Aceptada').distinct().count()

def contar_legajos_con_alarmas_activas():
    return LegajoAlertas.objects.filter(fk_alerta__gravedad='Critica').values_list('fk_legajo_id', flat=True).distinct().count()

def contar_legajos_con_planes_sociales():
    # Utiliza una subconsulta para contar los Legajos con planes sociales a través de DimensionEconomia
    return total_legajos.filter(dimensioneconomia__m2m_planes__isnull=False).distinct().count()

def calcular_porcentaje_respecto_a_poblacion(cantidad_legajos):
    # Calcula el porcentaje de legajos en comparación con la población total
    poblacion_san_miguel = 327000  # FIXME: Cual es la poblacion que hay que poner????
    
    if poblacion_san_miguel > 0:
        return (cantidad_legajos / poblacion_san_miguel) * 100
    else:
        return 0  # Evita la división por cero si no hay población registrada
    

def deriv_pendientes():
    return LegajosDerivaciones.objects.filter(estado='Pendiente').distinct().count()

def contar_legajos_embarazados():
    # Si no está en caché, calcula el valor y lo guarda en el caché
    return legajos_con_alerta_embarazo.count()

def contar_embarazos_sin_derivacion_aceptada():
    return legajos_con_alerta_embarazo.exclude(legajosderivaciones__estado='Aceptada').count() # Realiza el filtro de legajos con estado de derivación diferente a "Aceptada" prueba

def contar_embarazos_en_riesgo():
    # Realiza la consulta para contar los legajos
    return legajos_con_alerta_embarazo.filter(m2m_alertas__in=alarmas_activas).distinct().count()