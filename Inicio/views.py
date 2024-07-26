from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic import FormView ,DetailView ,CreateView ,UpdateView ,TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from Legajos.models import *
from Configuraciones.models import *
from datetime import date, timedelta
from django.utils import timezone


class BusquedaMenu(LoginRequiredMixin, FormView):
    def get(self, request, *args, **kwargs):
        menu = self.request.GET.get('punto_menu')
        puntos = [
            'dashboard',
            'secretarías',
            'secretarias',
            'subsecretarías',
            'subsecretarias',
            'programas',
            'organismos',
            'planes sociales',
            'agentes externos',
            'grupos de destinatarios',
            'tipos de alertas',
            'equipos',
            'acciones',
            'criterios',
            'índices',
            'indices',
            'usuarios',
            'grupos de usuario',
            'legajos',
            'derivaciones',
            'admisiones',
            'intervenciones',
        ]
        if menu and (menu.lower() in puntos):
            menu = menu.lower()
            if menu == "dashboard":
                return redirect('dashboard_listar')
            elif menu == 'secretarías' or menu == 'secretarias':
                return redirect('secretarias_listar')
            elif menu == 'subsecretarías' or menu == 'subsecretarias':
                return redirect('subsecretarias_listar')
            elif menu == 'programas':
                return redirect('programas_listar')
            elif menu == 'organismos':
                return redirect('organismos_listar')
            elif menu == 'equipos':
                return redirect('equipos_listar')
            elif menu == 'acciones':
                return redirect('acciones_listar')
            elif menu == 'criterios':
                return redirect('criterios_listar')
            elif menu == 'índices' or menu == 'indices':
                return redirect('índices_listar')
            elif menu == 'usuarios':
                return redirect('usuarios_listar')
            elif menu == 'legajos':
                return redirect('legajos_listar')
            elif menu == 'derivaciones':
                return redirect('legajosderivaciones_listar')
            elif menu == 'admisiones':
                return redirect('preadmisiones_listar')
            elif menu == 'intervenciones':
                return redirect('intervenciones_legajolistar')
            elif menu == 'planes sociales':
                return redirect('planes_sociales_listar')
            elif menu == 'agentes externos':
                return redirect('agentesexternos_listar')
            elif menu == 'grupos de usuario':
                return redirect('grupos_listar')
            elif menu == 'grupos de destinatarios':
                return redirect('gruposdestinatarios_listar')
            elif menu == 'categorias de alertas':
                return redirect('categoriaalertas_listar')
            elif menu == 'alertas':
                return redirect('alertas_listar')
        else:
            messages.error(self.request, ('No existen resultados.'))
            return redirect('legajos_listar')
        
def contar_legajos():
    # Cuenta la cantidad total de legajos
    cantidad_total_legajos = Legajos.objects.count()

    # Realiza el cálculo de la cantidad de legajos activos
    legajos_activos = Legajos.objects.filter(estado=True)
    cantidad_legajos_activos = legajos_activos.count()
    
    return  cantidad_total_legajos,cantidad_legajos_activos

def contar_legajos_entre_0_y_18_anios():
    # Obtiene la fecha actual
    today = date.today()

    # Calcula la fecha de hace 18 años
    fecha_hace_18_anios = today - timedelta(days=18 * 365)

    # Realiza una consulta para contar los legajos que tienen entre 0 y 18 años
    cantidad_legajos = Legajos.objects.filter(fecha_nacimiento__gte=fecha_hace_18_anios).count()
    return cantidad_legajos

def contar_adolescente_riesgo():
    # Obtiene la fecha actual
    today = date.today()

    # Calcula la fecha de hace 18 años
    fecha_hace_18_anios = today - timedelta(days=18 * 365)

    # Realiza el filtro de adolescentes
    adolescente = Legajos.objects.filter(fecha_nacimiento__gte=fecha_hace_18_anios)

    # Realiza el filtro de alarmas activas
    alarmas_activas = Alertas.objects.filter(gravedad='Critica')

    # Realiza la consulta para contar los adolescentes con alarmas activas
    cantidad_adolescente_riesgo = adolescente.filter(m2m_alertas__in=alarmas_activas).distinct().count()

    return cantidad_adolescente_riesgo


def contar_adolescente_sin_derivacion_aceptada():
    # Obtiene la fecha actual
    today = date.today()

    # Calcula la fecha de hace 18 años
    fecha_hace_18_anios = today - timedelta(days=18 * 365)

    # Realiza el filtro de adolescentes
    adolescente = Legajos.objects.filter(fecha_nacimiento__gte=fecha_hace_18_anios)

    # calculo de adolescente con estado de derivación diferente a "Aceptada"
    cantidad_adolescente_sin_derivacion_aceptada = adolescente.exclude(legajosderivaciones__estado='Aceptada').distinct().count()

    return cantidad_adolescente_sin_derivacion_aceptada


def contar_legajos_entre_0_y_40_dias():
    # Obtiene la fecha actual
    today = date.today()

    # Calcula la fecha de hace 40 días
    fecha_hace_40_dias = today - timedelta(days=40)

    # Realiza una consulta para contar los legajos que tienen entre 0 y 40 días
    cantidad_legajos_40_dias = Legajos.objects.filter(fecha_nacimiento__gte=fecha_hace_40_dias).distinct().count()
    return cantidad_legajos_40_dias

def contar_bb_riesgo():
    # Obtiene la fecha actual
    today = date.today()

    # Calcula la fecha de hace 40 días
    fecha_hace_40_dias = today - timedelta(days=40)

    # Realiza el filtro de bebés que tienen entre 0 y 40 días
    bb_40_dias = Legajos.objects.filter(fecha_nacimiento__gte=fecha_hace_40_dias)

    # Realiza el filtro de alarmas activas
    alarmas_activas = Alertas.objects.filter(gravedad='Critica')

    # Realiza la consulta para contar los bebés con alarmas activas
    cantidad_bb_riesgo = bb_40_dias.filter(m2m_alertas__in=alarmas_activas).distinct().count()

    return cantidad_bb_riesgo

def contar_bb_sin_derivacion_aceptada():
    # Obtiene la fecha actual
    today = date.today()

    # Calcula la fecha de hace 40 días
    fecha_hace_40_dias = today - timedelta(days=40)

    # Realiza el filtro de legajos que tienen entre 0 y 40 días
    bb_40_dias = Legajos.objects.filter(fecha_nacimiento__gte=fecha_hace_40_dias)

    # calculo de legajos con estado de derivación diferente a "Aceptada"
    cantidad_bb_sin_derivacion_aceptada = bb_40_dias.exclude(legajosderivaciones__estado='Aceptada').distinct().count()

    return cantidad_bb_sin_derivacion_aceptada





def contar_alarmas_activas():
    # Realiza el cálculo de la cantidad de legajos activos
    alarmas_activas = Alertas.objects.filter(gravedad='Critica')
    cantidad_alarmas_activas = alarmas_activas.count()
    
    return cantidad_alarmas_activas

def contar_legajos_con_alarmas_activas():
    # Obtener los IDs de los legajos con al menos una alerta crítica
    legajos_con_alarmas_activas_ids = LegajoAlertas.objects.filter(fk_alerta__gravedad='Critica').values_list('fk_legajo_id', flat=True).distinct().count()
    
    # Contar la cantidad de legajos
    cantidad_legajos_con_alarmas_activas = (legajos_con_alarmas_activas_ids)
    
    return cantidad_legajos_con_alarmas_activas

def contar_legajos_con_planes_sociales():
    # Utiliza una subconsulta para contar los Legajos con planes sociales a través de DimensionEconomia
    cantidad = Legajos.objects.filter(dimensioneconomia__m2m_planes__isnull=False).distinct().count()
    return cantidad

def calcular_porcentaje_respecto_a_poblacion(cantidad_legajos):
    poblacion_san_miguel = 327000  # Total de población de San Miguel (dato del censo)
    
    # Calcula el porcentaje de legajos en comparación con la población total
    if poblacion_san_miguel > 0:
        porcentaje = (cantidad_legajos / poblacion_san_miguel) * 100
    else:
        porcentaje = 0  # Evita la división por cero si no hay población registrada
    
    return porcentaje

def deriv_Pendientes():
    cantidad_deriv_Pendientes = LegajosDerivaciones.objects.filter(estado='Pendiente').distinct().count()
    return cantidad_deriv_Pendientes


def contar_legajos_embarazados():
    # Realiza el filtro de alertas que tienen nombre que comienza con 'embarazo'
    alertas_embarazo = Alertas.objects.filter(fk_categoria__nombre__istartswith='embarazo')
    # Realiza el filtro de legajos que tienen alertas de la categoría 'embarazo'
    legajos_con_alerta_embarazo = Legajos.objects.filter(m2m_alertas__in=alertas_embarazo)
    cantidad_legajos_embarazados = legajos_con_alerta_embarazo.count()
    return cantidad_legajos_embarazados

def contar_embarazos_sin_derivacion_aceptada():
    # Realiza el filtro de alertas que tienen nombre que comienza con 'embarazo'
    alertas_embarazo = Alertas.objects.filter(fk_categoria__nombre__istartswith='embarazo')
    # Realiza el filtro de legajos que tienen alertas de la categoría 'embarazo'
    legajos_con_alerta_embarazo = Legajos.objects.filter(m2m_alertas__in=alertas_embarazo)
    # Realiza el filtro de legajos con estado de derivación diferente a "Aceptada" prueba
    embarazos_sin_derivacion_aceptada = legajos_con_alerta_embarazo .exclude(legajosderivaciones__estado='Aceptada').count()
    return embarazos_sin_derivacion_aceptada

def contar_embarazos_en_riesgo():
    # Realiza el filtro de alertas que tienen nombre que comienza con 'embarazo'
    alertas_embarazo = Alertas.objects.filter(fk_categoria__nombre__istartswith='embarazo')
    # Realiza el filtro de legajos que tienen alertas de la categoría 'embarazo'
    legajos_con_alerta_embarazo = Legajos.objects.filter(m2m_alertas__in=alertas_embarazo)
    # Realiza el filtro de alarmas activas
    alarmas_activas = Alertas.objects.filter(gravedad='Critica')
    # Realiza la consulta para contar los legajos
    cantidad_embarazos_en_riesgo =legajos_con_alerta_embarazo.filter(m2m_alertas__in=alarmas_activas).distinct().count()

    return cantidad_embarazos_en_riesgo


    
        

class DashboardView(TemplateView):
    template_name = "dashboard.html"
    queryset = Legajos.objects.filter(estado=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Obtén las cantidades de legajos
        cantidad_total_legajos, cantidad_legajos_activos  = contar_legajos()
        cantidad_legajos_entre_0_y_18_anios = contar_legajos_entre_0_y_18_anios()
        cantidad_dv_Pendientes = deriv_Pendientes()
        cantidad_legajos_40_dias =  contar_legajos_entre_0_y_40_dias()
        cantidad_legajos_embarazados = contar_legajos_embarazados()
        cantidad_bb_riesgo = contar_bb_riesgo()
        cantidad_adolescente_riesgo = contar_adolescente_riesgo()
        cantidad_bb_sin_derivacion_aceptada = contar_bb_sin_derivacion_aceptada()
        cantidad_adolescente_sin_derivacion_aceptada = contar_adolescente_sin_derivacion_aceptada()
        embarazos_sin_derivacion_aceptada = contar_embarazos_sin_derivacion_aceptada()
        cantidad_embarazos_en_riesgo = contar_embarazos_en_riesgo()
        cantidad_legajos_con_alarmas_activas = contar_legajos_con_alarmas_activas()
        
        # Filtrar las alertas con gravedad "Critica" y estado "alarmas_activas"
        cantidad_alarmas_activas = Alertas.objects.filter(gravedad='Critica').count()

        # Agrega la cantidad de alarmas activas al contexto
        context['cantidad_alarmas_activas'] = cantidad_alarmas_activas

        # Obtén la cantidad de legajos con planes sociales utilizando la función
        cantidad_legajos_con_planes_sociales = contar_legajos_con_planes_sociales()

        # Agrega la cantidad al contexto
        context['cantidad_legajos_con_planes_sociales'] = cantidad_legajos_con_planes_sociales

        # Calcular el porcentaje de legajos en comparación con la población total
        porcentaje_legajos = calcular_porcentaje_respecto_a_poblacion(cantidad_total_legajos)
        
        # Agrega el porcentaje al contexto
        context['porcentaje_legajos'] = porcentaje_legajos
 
 

        # Agrega las cantidades al contexto
        context['cantidad_legajos'] = cantidad_legajos_entre_0_y_18_anios
        context['cantidad_total_legajos'] = cantidad_total_legajos
        context['cantidad_legajos_activos'] = cantidad_legajos_activos
        context['cantidad_dv_Pendientes'] = cantidad_dv_Pendientes
        context['cantidad_legajos_40_dias'] = cantidad_legajos_40_dias
        context['cantidad_legajos_embarazados'] = cantidad_legajos_embarazados
        context['cantidad_bb_riesgo'] = cantidad_bb_riesgo
        context['cantidad_adolescente_riesgo'] = cantidad_adolescente_riesgo
        context['cantidad_bb_sin_derivacion_aceptada'] = cantidad_bb_sin_derivacion_aceptada
        context['cantidad_adolescente_sin_derivacion_aceptada'] = cantidad_adolescente_sin_derivacion_aceptada
        context['embarazos_sin_derivacion_aceptada'] = embarazos_sin_derivacion_aceptada
        context['cantidad_embarazos_en_riesgo'] = cantidad_embarazos_en_riesgo
        context['cantidad_legajos_con_alarmas_activas'] = cantidad_legajos_con_alarmas_activas


        return context
    

        


