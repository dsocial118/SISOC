from datetime import date, timedelta

from Configuraciones.models import Alertas
from Legajos.models import LegajoAlertas, Legajos, LegajosDerivaciones
from django.db.models import Count, Q

#FIXME: Este modulo puede ser optimizado mas aun

today = date.today()
fecha_hace_18_anios = today - timedelta(days=18 * 365)
fecha_hace_40_dias = today - timedelta(days=40)

legajos_total = Legajos.objects.select_related('dimensioneconomia').prefetch_related('m2m_alertas').values(
    'estado',
    'fecha_nacimiento',
    'dimensioneconomia__m2m_planes'
)

alarmas_activas = Alertas.objects.filter(gravedad='Critica').values_list('id')

legajos_counts = Legajos.objects.select_related('dimensioneconomia').prefetch_related('m2m_alertas').aggregate(
    total_legajos=Count('id'),
    legajos_activos=Count('id', filter=Q(estado=True)),
    legajos_mayores_de_edad=Count('id', filter=Q(fecha_nacimiento__gte=fecha_hace_18_anios)),
    total_40_dias=Count('id', distinct=True),
    con_alertas_activas=Count('id', filter=Q(m2m_alertas__in=alarmas_activas), distinct=True),
    sin_aceptadas=Count('id', filter=~Q(legajosderivaciones__estado='Aceptada'), distinct=True),
    adolescente_riesgo=Count('id', filter=Q(m2m_alertas__in=alarmas_activas), distinct=True),
    adolescente_sin_derivacion_aceptada=Count('id', filter=~Q(legajosderivaciones__estado='Aceptada'), distinct=True)
    
)

alertas_embarazo_ids = Alertas.objects.filter(fk_categoria__nombre__istartswith='embarazo').values_list('id', flat=True)
legajos_con_alerta_embarazo = legajos_total.filter(m2m_alertas__id__in=alertas_embarazo_ids)

legajos_mayores_de_edad = legajos_total.filter(fecha_nacimiento__gte=fecha_hace_18_anios)

legajos_40_dias = legajos_total.filter(fecha_nacimiento__gte=fecha_hace_40_dias)        

def contar_legajos():    
    cantidad_total_legajos = legajos_counts['total_legajos']
    cantidad_legajos_activos = legajos_counts['legajos_activos']
    
    return  cantidad_total_legajos, cantidad_legajos_activos

def contar_legajos_entre_0_y_18_anios():
    # Realiza una consulta para contar los legajos que tienen entre 0 y 18 años
    return legajos_counts['legajos_mayores_de_edad']

def contar_adolescente_riesgo():
    # FIXME: Los adolescentes son todos los mayores de edad?
    return legajos_counts['adolescente_riesgo']

def contar_adolescente_sin_derivacion_aceptada():
    # calculo de adolescente con estado de derivación diferente a "Aceptada"
    return legajos_counts['adolescente_sin_derivacion_aceptada']

def contar_legajos_entre_0_y_40_dias():
    # Realiza una consulta para contar los legajos que tienen entre 0 y 40 días
    return legajos_counts['total_40_dias']

def contar_bb_riesgo():
    # Realiza la consulta para contar los bebés con alarmas activas
    return legajos_counts['con_alertas_activas']

def contar_bb_sin_derivacion_aceptada():
    # calculo de legajos con estado de derivación diferente a "Aceptada"
    return legajos_counts['sin_aceptadas']

def contar_legajos_con_alarmas_activas():
    return LegajoAlertas.objects.filter(fk_alerta__gravedad='Critica').values_list('fk_legajo_id', flat=True).distinct().count()

def contar_legajos_con_planes_sociales():
    # Utiliza una subconsulta para contar los Legajos con planes sociales a través de DimensionEconomia
    return legajos_total.filter(dimensioneconomia__m2m_planes__isnull=False).distinct().count()

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