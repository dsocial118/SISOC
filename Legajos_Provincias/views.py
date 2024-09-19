from django.shortcuts import render
from django.views.generic import (
    CreateView,
    ListView,
    DetailView,
    UpdateView,
    DeleteView,
    TemplateView,
    View,
    FormView,
)
from Usuarios.mixins import PermisosMixin
from .models import *
from .forms import *
from .choices import *
from django.conf import settings
import json
from django.http import JsonResponse, HttpResponseRedirect
#Paginacion
from django.views.generic import ListView
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.cache import cache

# Configurar el locale para usar el idioma español
import locale
locale.setlocale(locale.LC_ALL, 'es_AR.UTF-8')
# guardado de log de usuarios
import logging
logger = logging.getLogger('django')

admin_role = "Usuarios.rol_admin"

class LegajosProvinciasCreateView(CreateView):
    template_name = "Legajos_Provincias/legajosprovincias_form.html"
    model=Provincias_Datos
    form_class = Provincias_DatosForm
    def form_valid(self, form):
        self.object = form.save()
        return HttpResponseRedirect(reverse('legajosprovincias_crear'))
    
class LegajosProvinciasListView(ListView):
    model = Provincias
    template_name = "Legajos_Provincias/legajosprovincias_list.html"
    context_object_name = "legajos"
    paginate_by = 10  # Número de objetos por página

class ProvinciaDatosView(View):
    def get(self, request, provincia_id):
        try:
            prov = Provincias.objects.get(id=provincia_id)
            datos = Provincias_Datos.objects.filter(provincia_id=prov.id).last()
            if datos:
                response_data = {
                    'provincia': prov.nombre,
                    'poblacion': datos.poblacion,
                    'pobreza': datos.pobreza,
                    'PEA': datos.PEA,
                    'ocupada': datos.ocupada,
                    'subocupada': datos.subocupada,
                    'desocupada': datos.desocupada,
                    'educ_incompleta_obligatoria': datos.educ_incompleta_obligatoria,
                    'primara_incompleta_PAS': datos.primara_incompleta_PAS,
                    'secundaria_incompleta_PAS': datos.secundaria_incompleta_PAS,
                    'beneficiarios_PAS': datos.beneficiarios_PAS,
                    'porcentaje_PAS': datos.porcentaje_PAS,
                    'q_expedientes': datos.q_expedientes,
                    'alimentos': datos.alimentos,
                    'ganaderia': datos.ganaderia,
                    'agricultura_familiar': datos.agricultura_familiar,
                    'pesca': datos.pesca,
                    'forestal': datos.forestal,
                    'manufacturera': datos.manufacturera,
                    'textil': datos.textil,
                    'carpinteria': datos.carpinteria,
                    'herreria': datos.herreria,
                    'mecanica': datos.mecanica,
                    'matriceria': datos.matriceria,
                    'otras_matriceria': datos.otras_matriceria,
                    'artesania_manufactureria': datos.artesania_manufactureria,
                    'albanileria': datos.albanileria,
                    'otras_actividades_construccion': datos.otras_actividades_construccion,
                    'reciclaje': datos.reciclaje,
                    'energia_renovable': datos.energia_renovable,
                    'soporte_tecnico': datos.soporte_tecnico,
                    'infraestructura_tecnologica': datos.infraestructura_tecnologica,
                    'desarrollo_software': datos.desarrollo_software,
                    'estetica_pedicuria_etc': datos.estetica_pedicuria_etc,
                    'limpieza': datos.limpieza,
                    'jardineria': datos.jardineria,
                    'gastronomico': datos.gastronomico,
                    'logistica': datos.logistica,
                    'turismo': datos.turismo,
                    'comercializacion': datos.comercializacion,
                    'cuidados': datos.cuidados,
                    'salud': datos.salud,
                    'energia': datos.energia,
                    'mineria': datos.mineria,
                    'petroquimica': datos.petroquimica,
                }
            else:
                response_data = {
                    'provincia': prov.nombre,
                    'error': "No se encontraros datos."
                }
            return JsonResponse(response_data)
        except Provincias_Datos.DoesNotExist:
            return JsonResponse({'error': 'Datos de la provincia no encontrados'}, status=404)