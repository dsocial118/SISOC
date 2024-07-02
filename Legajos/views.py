import os
from django.http import HttpResponseRedirect
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
from django.db.models import Q, Count, F, Case, When, Value, BooleanField,IntegerField
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import render, redirect
from django.core.files.base import ContentFile
from PIL import Image
from io import BytesIO  # Import BytesIO
from django.http import JsonResponse,HttpResponse
from datetime import datetime, timedelta,date, time
from collections import defaultdict
import calendar
from django.db.models.functions import ExtractYear,ExtractMonth
from Usuarios.mixins import PermisosMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404
from .models import *
from .forms import *
from .choices import *
from django.conf import settings
import json

# Configurar el locale para usar el idioma español
import locale
locale.setlocale(locale.LC_ALL, 'es_AR.UTF-8')
# guardado de log de usuarios
import logging
logger = logging.getLogger('django')


# region ############################################################### LEGAJOS

class LegajosReportesListView(ListView):
    template_name = "Legajos/legajos_reportes.html"
    model = LegajosDerivaciones
    
    
    def get_context_data(self, **kwargs):
        organismos = Organismos.objects.all()
        programas = Programas.objects.all()
        context = super().get_context_data(**kwargs)
        context['organismos'] = organismos
        context['programas'] = programas
        context['estados'] = CHOICE_ESTADO_DERIVACION
        return context   
    
    # Funcion de busqueda
    def get_queryset(self): 
        nombre_completo_legajo = self.request.GET.get("busqueda")
        data_organismo = self.request.GET.get("data_organismo")
        data_programa = self.request.GET.get("data_programa")
        data_estado = self.request.GET.get("data_estado")
        data_fecha_desde = self.request.GET.get("data_fecha_derivacion")
        object_list = LegajosDerivaciones.objects.all()
        
        if data_programa and data_organismo : object_list = object_list.filter(
                fk_programa=data_programa,
                fk_organismo=data_organismo
            )
        
        elif data_programa : object_list = object_list.filter(fk_programa=data_programa)
        elif data_organismo: object_list = object_list.filter(fk_organismo=data_organismo)
        
        if nombre_completo_legajo or nombre_completo_legajo == '':
            object_list = object_list.filter(
                Q(fk_legajo__nombre__icontains=nombre_completo_legajo) | 
                Q(fk_legajo__apellido__icontains=nombre_completo_legajo) | 
                Q(fk_legajo__documento__icontains=nombre_completo_legajo)
            )
        
        if data_estado : object_list = object_list.filter(estado=data_estado)
        if data_fecha_desde : object_list = object_list.filter(fecha_creado__gte=data_fecha_desde)
        if not object_list.exists():
                messages.warning(self.request, "La búsqueda no arrojó resultados.")
                return object_list
        
        return object_list.distinct()

class LegajosListView(TemplateView):
    template_name = "Legajos/legajos_list.html"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        object_list = Legajos.objects.none()
        mostrar_resultados = False
        mostrar_btn_resetear = False
        query = self.request.GET.get("busqueda")
        if query:
            object_list = Legajos.objects.filter(Q(apellido__icontains=query) | Q(documento__icontains=query)).distinct()
            if object_list and object_list.count() == 1:
                id = None
                for o in object_list:
                    pk = o.id
                return redirect("legajos_ver", pk)

            if not object_list:
                messages.warning(self.request, ("La búsqueda no arrojó resultados."))

            mostrar_btn_resetear = True
            mostrar_resultados = True

        
        context["mostrar_resultados"] = mostrar_resultados
        context["mostrar_btn_resetear"] = mostrar_btn_resetear
        context["object_list"] = object_list

        return self.render_to_response(context)


class LegajosDetailView(DetailView):
    model = Legajos

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        resto_alertas = 0
        # Obtener la fecha actual
        fecha_actual = fecha_actual = datetime.now().date()

        # Calcular la fecha hace 12 meses desde la fecha actual
        fecha_inicio = fecha_actual - timedelta(days=365)

        legajo_alertas = LegajoAlertas.objects.filter(fk_legajo=pk)        

        count_intervenciones = LegajosDerivaciones.objects.filter(fk_legajo_id=pk).count()
        
        
        derivaciones = LegajosDerivaciones.objects.filter(fk_legajo_id=pk)
        

        # Obtener todas las categorías con la cantidad de alertas en cada una
        categorias_con_alertas = legajo_alertas.values(
            'fk_alerta__fk_categoria'
        ).annotate(
            cantidad_alertas=Count('fk_alerta__fk_categoria')
        )

        # Obtener las IDs de las categorías con alertas
        ids_categorias = [item['fk_alerta__fk_categoria'] for item in categorias_con_alertas]

        # Obtener todas las categorías completas
        categorias_completas = CategoriaAlertas.objects.filter(id__in=ids_categorias).order_by('nombre')

        # Verificar si categorias_completas no es None antes de aplicar el slicing
        if categorias_completas is not None:
            # Obtener solo los primeros 8 nombres de categorías (o menos si hay menos de 8)
            nombres_categorias = categorias_completas.values_list('nombre', flat=True)[:8]
            if categorias_completas.count() > 8:
                resto_alertas = categorias_completas.count() - 8
        else:
            nombres_categorias = []


        # >>>>>>>>>>>>>>>>>>Comienzo de la query para el gráfico de evolución de riesgos>>>>>>>>>>>>>>>>
        if HistorialLegajoAlertas.objects.filter(fk_legajo=pk).exists():
            # Calcular la fecha de inicio hace doce meses
            fecha_inicio_doce_meses = fecha_actual - timedelta(days=365)

            # Calcular la fecha de inicio a partir del primer día del mes siguiente al mes actual
            primer_dia_siguiente_mes = datetime(fecha_actual.year, fecha_actual.month % 12 + 1, 1)

            # Calcular la fecha de inicio hace doce meses, excepto el mes del año anterior al mes actual
            fecha_inicio_doce_meses_excepto_mes_anterior = primer_dia_siguiente_mes - timedelta(days=365)

            alertas_ultimo_anio = HistorialLegajoAlertas.objects.filter(fk_legajo=pk).filter(
                Q(fecha_inicio__gt=fecha_inicio_doce_meses_excepto_mes_anterior) |
                Q(fecha_fin__gt=fecha_inicio_doce_meses_excepto_mes_anterior) |
                Q(fecha_fin__isnull=True)
            ).distinct()

            # Obtener todas las dimensiones existentes del CHOICE_DIMENSIONES
            todas_dimensiones = [dimension for dimension, _ in CHOICE_DIMENSIONES[1:]]

            # Definir el diccionario para almacenar los datos
            datos_por_dimension = {dimension: [0] * 12 for dimension in todas_dimensiones}

            for alerta in alertas_ultimo_anio:
                dimension = alerta.fk_alerta.fk_categoria.dimension
                fecha_inicio = alerta.fecha_inicio if datetime.combine(alerta.fecha_inicio, time.min)>= fecha_inicio_doce_meses_excepto_mes_anterior else fecha_inicio_doce_meses_excepto_mes_anterior.date()
                fecha_fin = alerta.fecha_fin if alerta.fecha_fin else date.today()

                # Calcular la lista de meses activos
                meses_activos = []
                while fecha_inicio <= fecha_fin:
                    meses_activos.append(fecha_inicio.month)
                    # Avanzamos al primer día del mes siguiente
                    fecha_inicio = fecha_inicio.replace(day=1) + timedelta(days=32)
                    fecha_inicio = fecha_inicio.replace(day=1)

                # Actualizar la lista de la dimensión con la cantidad de alertas por mes
                for mes in meses_activos:
                    datos_por_dimension[dimension][mes - 1] += 1  # Restamos 1 al mes para que sea el índice correcto en la lista

            # Convertir los números de meses a nombres de meses en el diccionario
            nombres_meses = [calendar.month_name[mes].capitalize() for mes in range(1, 13)]
            datos_por_dimension = {dimension: [datos_por_dimension[dimension][mes] for mes in range(12)] for dimension in todas_dimensiones}

            # Mover el último mes al final de la lista
            mes_actual = date.today().month
            datos_por_dimension = {dimension: datos_por_dimension[dimension][mes_actual:] + datos_por_dimension[dimension][:mes_actual] for dimension in todas_dimensiones}

            # Convertir los números de meses a nombres de meses en español y en orden ascendente
            nombres_meses = [calendar.month_name[mes].capitalize() for mes in range(1, 13)]
            nombres_meses_ordenados = nombres_meses[mes_actual:] + nombres_meses[:mes_actual]

            # Agregar los nombres de los meses al diccionario
            datos_por_dimension['meses'] = nombres_meses_ordenados
            # Convertir a JSON
            datos_json = json.dumps(datos_por_dimension)
        else:
            datos_json = {}
        # >>>>>>>>>>>>>>>>>>Fin de la query para el gráfico de evolución de riesgos>>>>>>>>>>>>>>>>

        context = super().get_context_data(**kwargs)
        emoji_nacionalidad = EMOJIS_BANDERAS.get(context['object'].nacionalidad, '')
        context['emoji_nacionalidad'] = emoji_nacionalidad
        context["familiares_fk1"] = LegajoGrupoFamiliar.objects.filter(fk_legajo_1=pk)
        context["familiares_fk2"] = LegajoGrupoFamiliar.objects.filter(fk_legajo_2=pk)
        context["count_familia"] = context["familiares_fk1"].count() + context["familiares_fk2"].count()
        context["hogar_familiares_fk1"] = LegajoGrupoHogar.objects.filter(fk_legajo_1Hogar=pk)
        context["hogar_familiares_fk2"] = LegajoGrupoHogar.objects.filter(fk_legajo_2Hogar=pk)
        context["hogar_count_familia"] = context["hogar_familiares_fk1"].count() + context["hogar_familiares_fk2"].count()
        context['files_img'] = LegajosArchivos.objects.filter(fk_legajo=pk, tipo="Imagen")
        context['files_docs'] = LegajosArchivos.objects.filter(fk_legajo=pk, tipo="Documento")
        context["nombres_categorias"] = nombres_categorias
        context["resto_alertas"] = resto_alertas
        context["count_alertas"] = legajo_alertas.count()
        context["alertas_alta"] = LegajoAlertas.objects.filter(fk_legajo=pk, fk_alerta__gravedad="Critica")
        context["alertas_media"] = LegajoAlertas.objects.filter(fk_legajo=pk, fk_alerta__gravedad="Importante")
        context["alertas_baja"] = LegajoAlertas.objects.filter(fk_legajo=pk, fk_alerta__gravedad="Precaución")
        context["count_alta"] = LegajoAlertas.objects.filter(fk_legajo=pk, fk_alerta__gravedad="Critica").count()
        context["count_media"] = LegajoAlertas.objects.filter(fk_legajo=pk, fk_alerta__gravedad="Importante").count()
        context["count_baja"] = LegajoAlertas.objects.filter(fk_legajo=pk, fk_alerta__gravedad="Precaución").count()
        context["historial_alertas"] = True if HistorialLegajoAlertas.objects.filter(fk_legajo=pk).exists() else False
        context["datos_json"] = datos_json
        context['count_intervenciones'] = count_intervenciones
        context['derivaciones'] = derivaciones
        return context


class LegajosDeleteView(PermisosMixin, DeleteView):
    permission_required = "Usuarios.rol_admin"
    model = Legajos
    success_url = reverse_lazy("legajos_listar")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        legajo = self.get_object()

        # Crear una lista para almacenar los nombres de las relaciones existentes
        relaciones_existentes = []

        # Agregar los nombres de las relaciones existentes a la lista
        if LegajosArchivos.objects.filter(fk_legajo=legajo).exists():
            relaciones_existentes.append('Archivos')

        if LegajosDerivaciones.objects.filter(fk_legajo=legajo).exists():
            relaciones_existentes.append('Derivaciones')

        if LegajoAlertas.objects.filter(fk_legajo=legajo).exists():
            relaciones_existentes.append('Alertas')

        if HistorialLegajoAlertas.objects.filter(fk_legajo=legajo).exists():
            relaciones_existentes.append('Historial de Alertas')

        if LegajoGrupoFamiliar.objects.filter(fk_legajo_1=legajo).exists() or LegajoGrupoFamiliar.objects.filter(fk_legajo_2=legajo).exists():
            relaciones_existentes.append('Grupo Familiar')

        # Agregar la lista de nombres de relaciones al contexto
        context['relaciones_existentes'] = relaciones_existentes
        return context
    
    def form_valid(self, form):
        # Obtener el usuario que realiza la eliminación
        legajo = self.get_object()
        # Eliminar las instancias relacionadas protegidas (LegajosDerivaciones en este caso)
        LegajosDerivaciones.objects.filter(fk_legajo=legajo).delete()
        LegajoAlertas.objects.filter(fk_legajo=legajo).delete()
        HistorialLegajoAlertas.objects.filter(fk_legajo=legajo).delete()

        #Preguntar por cual hay que buscar para eliminar o si es por ambos
        LegajoGrupoFamiliar.objects.filter(fk_legajo_1=legajo).delete()
        LegajoGrupoFamiliar.objects.filter(fk_legajo_2=legajo).delete()

        usuario_eliminacion = self.request.user
        legajo = self.get_object()        

        # Graba la data del usuario que realiza la eliminacion en el LOG
        mensaje = f"Legajo borrado - Nombre: {legajo.nombre}, Apellido: {legajo.apellido}, Tipo de documento: {legajo.tipo_doc}, Documento: {legajo.documento}"
        logger.info(f'Username: {usuario_eliminacion} - {mensaje}')
        return super().form_valid(form)


class LegajosCreateView(PermisosMixin, CreateView):
    permission_required = "Usuarios.rol_admin"
    model = Legajos
    form_class = LegajosForm

    def form_valid(self, form):
        legajo = form.save(commit=False)  # Guardamos sin persistir en la base de datos

        if legajo.foto:
            imagen = Image.open(legajo.foto)
            tamano_minimo = min(imagen.width, imagen.height)
            area = (0, 0, tamano_minimo, tamano_minimo)
            imagen_recortada = imagen.crop(area)

            buffer = BytesIO()
            imagen_recortada.save(buffer, format='PNG')
            legajo.foto.save(legajo.foto.name, ContentFile(buffer.getvalue()))

        self.object = form.save()  # Guardamos el objeto Legajos con la imagen recortada (si corresponde)

        try:
            ref = DimensionFamilia.objects.create(fk_legajo_id=self.object.id)
            DimensionVivienda.objects.create(fk_legajo_id=self.object.id)
            DimensionSalud.objects.create(fk_legajo_id=self.object.id)
            DimensionEconomia.objects.create(fk_legajo_id=self.object.id)
            DimensionEducacion.objects.create(fk_legajo_id=self.object.id)
            DimensionTrabajo.objects.create(fk_legajo_id=self.object.id)
            
            if "form_legajos" in self.request.POST:
                return redirect("legajos_ver", pk=int(self.object.id))

            if "form_step2" in self.request.POST:
                return redirect("legajosdimensiones_editar", pk=ref.id)

        except Exception as e:
            # Si ocurre un error durante la creación de dimensiones, borra el objeto Legajos previamente guardado
            legajo.delete()

            # Muestra un mensaje de error al usuario
            messages.error(self.request, "Se produjo un error al crear las dimensiones. Por favor, inténtalo de nuevo.")
            return redirect("legajos_crear")  # Reemplaza esto con la URL de la vista de creación


class LegajosUpdateView(PermisosMixin, UpdateView):
    permission_required = "Usuarios.rol_admin"
    model = Legajos
    form_class = LegajosUpdateForm

    def form_valid(self, form):
        legajo = form.save(commit=False)  # Guardamos sin persistir en la base de datos

        # Comprobamos si se ha cargado una nueva foto y si es diferente de la foto actual
        if legajo.foto and legajo.foto != self.get_object().foto:
            imagen = Image.open(legajo.foto)
            tamano_minimo = min(imagen.width, imagen.height)
            area = (0, 0, tamano_minimo, tamano_minimo)
            imagen_recortada = imagen.crop(area)

            buffer = BytesIO()
            imagen_recortada.save(buffer, format='PNG')
            legajo.foto.save(legajo.foto.name, ContentFile(buffer.getvalue()))

        self.object = form.save()  # Guardamos el objeto Legajos con la imagen recortada (si corresponde)
                     

        if "form_legajos" in self.request.POST:
            return redirect("legajos_ver", pk=self.object.id)

        if "form_step2" in self.request.POST:
            return redirect("legajosdimensiones_editar", pk=self.object.dimensionfamilia.id)

        self.object.save()
        


# endregion


# region ############################################################### GRUPO FAMILIAR


class LegajosGrupoFamiliarCreateView(CreateView):
    permission_required = "Usuarios.rol_admin"
    model = LegajoGrupoFamiliar
    form_class = NuevoLegajoFamiliarForm

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        legajo_principal = Legajos.objects.filter(pk=pk).first()
        # Calcula la edad utilizando la función 'edad' del modelo
        edad_calculada = legajo_principal.edad()

        # Verifica si tiene más de 18 años
        if isinstance(edad_calculada, str) and 'años' in edad_calculada:
            edad_num = int(edad_calculada.split()[0])
            if edad_num >= 18:
                es_menor_de_18 = False
        else:
            es_menor_de_18 = True

         # Verificar si tiene un cuidador principal asignado utilizando el método que agregaste al modelo
        tiene_cuidador_ppal = LegajoGrupoFamiliar.objects.filter(
            fk_legajo_1=legajo_principal,
            cuidador_principal=True
        ).exists()

        context = super().get_context_data(**kwargs)
        context["familiares_fk1"] = LegajoGrupoFamiliar.objects.filter(fk_legajo_1=pk)
        context["familiares_fk2"] = LegajoGrupoFamiliar.objects.filter(fk_legajo_2=pk)
        context["count_familia"] = context["familiares_fk1"].count() + context["familiares_fk2"].count()
        context["legajo_principal"] = legajo_principal
        context["es_menor_de_18"] = es_menor_de_18
        context["tiene_cuidador_ppal"] = tiene_cuidador_ppal
        context["pk"] = pk
        context["id_dimensionfamiliar"] = DimensionFamilia.objects.get(fk_legajo=pk).id
        return context

    def form_valid(self, form):
        pk = self.kwargs["pk"]
        vinculo = form.cleaned_data['vinculo']
        conviven = form.cleaned_data['conviven']
        estado_relacion = form.cleaned_data['estado_relacion']
        cuidador_principal = form.cleaned_data['cuidador_principal']

        # Crea el objeto Legajos
        try:
            nuevo_legajo = form.save()
            DimensionFamilia.objects.create(fk_legajo=nuevo_legajo)
            DimensionVivienda.objects.create(fk_legajo=nuevo_legajo)
            DimensionSalud.objects.create(fk_legajo=nuevo_legajo)
            DimensionEconomia.objects.create(fk_legajo=nuevo_legajo)
            DimensionEducacion.objects.create(fk_legajo=nuevo_legajo)
            DimensionTrabajo.objects.create(fk_legajo=nuevo_legajo)
        except:
            return messages.error(self.request, "Verifique que no exista un legajo con ese DNI y NÚMERO.")

        # Crea el objeto LegajoGrupoFamiliar con los valores del formulario
        vinculo_data = VINCULO_MAP.get(vinculo)
        if not vinculo_data:
            return messages.error(self.request, "Vinculo inválido.")

        # crea la relacion de grupo familiar
        legajo_principal = Legajos.objects.get(id=pk)
        try:
            legajo_grupo_familiar = LegajoGrupoFamiliar.objects.create(
                fk_legajo_1=legajo_principal,
                fk_legajo_2=nuevo_legajo,
                vinculo=vinculo_data["vinculo"],
                vinculo_inverso=vinculo_data["vinculo_inverso"],
                conviven=conviven,
                estado_relacion=estado_relacion,
                cuidador_principal=cuidador_principal,
            )

            familiar = {
                "id": legajo_grupo_familiar.id,
                "fk_legajo_1": legajo_grupo_familiar.fk_legajo_1.id,
                "fk_legajo_2": legajo_grupo_familiar.fk_legajo_2.id,
                "vinculo": legajo_grupo_familiar.vinculo,
                "nombre": legajo_grupo_familiar.fk_legajo_2.nombre,
                "apellido": legajo_grupo_familiar.fk_legajo_2.apellido,
                "foto": legajo_grupo_familiar.fk_legajo_2.foto.url if legajo_grupo_familiar.fk_legajo_2.foto else None,
                "cuidador_principal": legajo_grupo_familiar.cuidador_principal,
            }
        except:
            return messages.error(self.request, "Verifique que no exista un legajo con ese DNI y NÚMERO.")

        messages.success(self.request, "Familair agregado correctamente.")
        # Redireccionar a la misma página después de realizar la acción con éxito
        return HttpResponseRedirect(self.request.path_info)


def busqueda_familiares(request):
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        res = None
        busqueda = request.POST.get("busqueda")
        legajo_principal_id = request.POST.get("id")
        legajos_asociadosfk1 = LegajoGrupoFamiliar.objects.filter(fk_legajo_1_id=legajo_principal_id).values_list('fk_legajo_2_id', flat=True)
        legajos_asociadosfk2 = LegajoGrupoFamiliar.objects.filter(fk_legajo_2_id=legajo_principal_id).values_list('fk_legajo_1_id', flat=True)
        familiares = (
            Legajos.objects.filter(~Q(id=legajo_principal_id) & (Q(apellido__icontains=busqueda) | Q(documento__icontains=busqueda)))
            .exclude(id__in=legajos_asociadosfk1)
            .exclude(id__in=legajos_asociadosfk2)
        )

        if len(familiares) > 0 and busqueda:
            data = [
                {
                    'pk': familiar.pk,
                    'nombre': familiar.nombre,
                    'apellido': familiar.apellido,
                    'documento': familiar.documento,
                    'tipo_doc': familiar.tipo_doc,
                    'fecha_nacimiento': familiar.fecha_nacimiento,
                    'sexo': familiar.sexo,
                    # Otros campos que deseas incluir
                }
                for familiar in familiares
            ]
            res = data

        else:
            res = ""

        return JsonResponse({"data": res})

    return JsonResponse({"data": "this is data"})


class LegajoGrupoFamiliarList(ListView):
    model = LegajoGrupoFamiliar

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        context["familiares_fk1"] = LegajoGrupoFamiliar.objects.filter(fk_legajo_1=pk)
        context["familiares_fk2"] = LegajoGrupoFamiliar.objects.filter(fk_legajo_2=pk)
        context["count_familia"] = context["familiares_fk1"].count() + context["familiares_fk1"].count()
        context["nombre"] = Legajos.objects.filter(pk=pk).first()
        context["pk"] = pk
        return context


class CreateGrupoFamiliar(View):
    def get(self, request, **kwargs):
        fk_legajo_1 = request.GET.get("fk_legajo_1", None)
        fk_legajo_2 = request.GET.get("fk_legajo_2", None)
        vinculo = request.GET.get("vinculo", None)
        estado_relacion = request.GET.get("estado_relacion", None)
        conviven = request.GET.get("conviven", None)
        cuidador_principal = request.GET.get("cuidador_principal", None)
        obj = None
        vinculo_data = VINCULO_MAP.get(vinculo)

        if not vinculo_data:
            return messages.error(self.request, "Vinculo inválido.")

        obj = LegajoGrupoFamiliar.objects.create(
            fk_legajo_1_id=fk_legajo_1,
            fk_legajo_2_id=fk_legajo_2,
            vinculo=vinculo_data["vinculo"],
            vinculo_inverso=vinculo_data["vinculo_inverso"],
            estado_relacion=estado_relacion,
            conviven=conviven,
            cuidador_principal=cuidador_principal,
        )

        familiar = {
            "id": obj.id,
            "fk_legajo_1": obj.fk_legajo_1.id,
            "fk_legajo_2": obj.fk_legajo_2.id,
            "vinculo": obj.vinculo,
            "nombre": obj.fk_legajo_2.nombre,
            "apellido": obj.fk_legajo_2.apellido,
            "foto": obj.fk_legajo_2.foto.url if obj.fk_legajo_2.foto else None,
            "cuidador_principal": obj.cuidador_principal,
        }
        data = {  
                "tipo_mensaje": "success",             
                "mensaje" : "Vínculo familiar agregado correctamente."}  

        return JsonResponse({"familiar": familiar, "data": data})


class DeleteGrupoFamiliar(View):
    def get(self, request):
        pk = request.GET.get("id", None)
        try:
            familiar = get_object_or_404(LegajoGrupoFamiliar, pk=pk)
            familiar.delete()
            data = {"deleted": True,   
                "tipo_mensaje": "success",             
                "mensaje" : "Vínculo familiar eliminado correctamente."} 
        except:
            data = {"deleted": False,   
                "tipo_mensaje": "error",             
                "mensaje" : "No fue posible eliminar el archivo."}  

        return JsonResponse(data)

# endregion


# region ############################################################### DERIVACIONES


class LegajosDerivacionesBuscar(PermisosMixin, TemplateView):
    permission_required = "Usuarios.rol_admin"
    template_name = "Legajos/legajosderivaciones_buscar.html"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        legajos = Legajos.objects.all()
        derivaciones = LegajosDerivaciones.objects.all()
        con_derivaciones = LegajosDerivaciones.objects.none()
        sin_derivaciones = Legajos.objects.none()
        barrios = legajos.values_list("barrio")
        circuitos = CHOICE_CIRCUITOS
        localidad = CHOICE_NACIONALIDAD
        mostrar_resultados = False
        mostrar_btn_resetear = False
        query = self.request.GET.get("busqueda")
        if query:
            derivaciones_filtrado = derivaciones.filter(Q(fk_legajo__apellido__icontains=query) | Q(fk_legajo__documento__icontains=query)).values("fk_legajo").distinct()
            legajos_filtrado = legajos.filter(Q(apellido__icontains=query) | Q(documento__icontains=query)).distinct()

            if derivaciones_filtrado:
                sin_derivaciones = legajos_filtrado.exclude(id__in=derivaciones_filtrado)
                con_derivaciones = legajos_filtrado.filter(id__in=derivaciones_filtrado)

            else:
                sin_derivaciones = legajos_filtrado

            if not derivaciones_filtrado and not legajos_filtrado:
                messages.warning(self.request, "La búsqueda no arrojó resultados")

            mostrar_btn_resetear = True
            mostrar_resultados = True

        context["barrios"] = barrios
        context["circuitos"] = circuitos
        context["localidad"] = localidad
        context["mostrar_resultados"] = mostrar_resultados
        context["mostrar_btn_resetear"] = mostrar_btn_resetear
        context["sin_derivaciones"] = sin_derivaciones
        context["con_derivaciones"] = con_derivaciones
        return self.render_to_response(context)


class LegajosDerivacionesListView(PermisosMixin, ListView):
    permission_required = "Usuarios.rol_admin"
    model = LegajosDerivaciones
    paginate_by = 25

    def get_context_data(self, **kwargs):
        context = super(LegajosDerivacionesListView, self).get_context_data(**kwargs)

        model = LegajosDerivaciones.objects.all()  # TODO filtrar por programa

        context["pendientes"] = model.filter(estado="Pendiente")
        context["aceptadas"] = model.filter(estado="Aceptada")
        context["analisis"] = model.filter(estado="En análisis")
        context["asesoradas"] = model.filter(estado="Asesoramiento")
        context["enviadas"] = model.filter(fk_usuario=self.request.user)
        return context

    # Funcion de busqueda

    def get_queryset(self):
        model = LegajosDerivaciones.objects.all()
        query = self.request.GET.get("busqueda")

        if query:
            object_list = model.filter(Q(fk_legajo__apellido__icontains=query) | Q(fk_legajo__documento__icontains=query)).distinct()

        else:
            object_list = model.all()

        return object_list.order_by("-estado")


class LegajosDerivacionesCreateView(PermisosMixin, CreateView):
    permission_required = "Usuarios.rol_admin"
    model = LegajosDerivaciones
    form_class = LegajosDerivacionesForm
    success_message = "Derivación registrada con éxito"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        pk = self.kwargs.get("pk")

        if pk:
            # excluyo los programas que ya tienen derivaciones en curso para este legajo (solo dejo fuera las 'asesoradas')

            programas = Programas.objects.all().exclude(
                id__in=LegajosDerivaciones.objects.filter(fk_legajo=pk).exclude(estado__in=["Rechazada", "Finalizada"]).values_list("fk_programa", flat=True)
            )

            form.fields["fk_programa"].queryset = programas
            form.fields["fk_legajo"].initial = pk
            form.fields["fk_usuario"].initial = self.request.user
        return form

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        context["legajo"] = Legajos.objects.filter(id=pk).first()
        return context


class LegajosDerivacionesUpdateView(PermisosMixin, UpdateView):
    permission_required = "Usuarios.rol_admin"
    model = LegajosDerivaciones
    form_class = LegajosDerivacionesForm
    success_message = "Derivación editada con éxito"

    def get_initial(self):
        initial = super().get_initial()
        initial["fk_usuario"] = self.request.user
        return initial
        
    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        legajo = LegajosDerivaciones.objects.filter(id=pk).first()
        context["legajo"] = Legajos.objects.filter(id=legajo.fk_legajo.id).first()
        return context

class LegajosDerivacionesHistorial(PermisosMixin, ListView):
    permission_required = "Usuarios.rol_admin"
    model = LegajosDerivaciones
    template_name="Legajos/legajosderivaciones_historial.html"

    def get_context_data(self, **kwargs):
        context = super(LegajosDerivacionesHistorial, self).get_context_data(**kwargs)
        pk = self.kwargs.get("pk")

        legajo = Legajos.objects.filter(id=pk).first()
        historial = LegajosDerivaciones.objects.filter(fk_legajo_id=pk)

        context["historial"] = historial
        context["legajo"] = legajo
        context["pendientes"] = historial.filter(estado="Pendiente").count()
        context["admitidas"] = historial.filter(estado="Aceptada").count()
        context["rechazadas"] = historial.filter(estado="Rechazada").count()
        return context


class LegajosDerivacionesDeleteView(PermisosMixin, DeleteView):
    permission_required = "Usuarios.rol_admin"
    model = LegajosDerivaciones
    #success_url = reverse_lazy("legajosderivaciones_listar")

    def form_valid(self, form):
        if self.object.estado != "Pendiente":
            messages.error(
                self.request,
                "No es posible eliminar una solicitud en estado " + self.object.estado,
            )

            return redirect("legajosderivaciones_ver", pk=int(self.object.id))

        if self.request.user != self.object.fk_usuario:
            messages.error(
                self.request,
                "Solo el usuario que generó esta derivación puede eliminarla.",
            )

            return redirect("legajosderivaciones_ver", pk=int(self.object.id))

        else:
            legajo = LegajosDerivaciones.objects.filter(pk=self.object.id).first()
            self.object.delete()

            return redirect("legajosderivaciones_historial", pk=legajo.fk_legajo_id)


class LegajosDerivacionesDetailView(PermisosMixin, DetailView):
    permission_required = "Usuarios.rol_admin"
    model = LegajosDerivaciones


# endregion


# region ############################################################### ALERTAS


class LegajosAlertasListView(PermisosMixin, ListView):
    permission_required = "Usuarios.rol_admin"
    model = HistorialLegajoAlertas
    template_name="Legajos/legajoalertas_list.html"

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        context["legajo_alertas"] = HistorialLegajoAlertas.objects.filter(fk_legajo=pk)
        context["legajo"] = Legajos.objects.filter(id=pk).first()
        return context


class LegajosAlertasCreateView(PermisosMixin, SuccessMessageMixin, CreateView):
    permission_required = "Usuarios.rol_admin"
    model = LegajoAlertas
    form_class = LegajosAlertasForm
    success_message = "Alerta asignada correctamente."

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        alertas = LegajoAlertas.objects.filter(fk_legajo=pk)
        legajo = Legajos.objects.filter(pk=pk).first()
        context["alertas"] = alertas
        context["legajo"] = legajo
        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        pk = self.kwargs.get("pk")
        if pk:
            form.fields["fk_legajo"].initial = pk
            form.fields["creada_por"].initial = self.request.user.usuarios.id
        return form

    def get_success_url(self):
        # Redirige a la misma página después de agregar la alerta
        return self.request.path


class DeleteAlerta(PermisosMixin, View):
    permission_required = "Usuarios.rol_admin"

    def get(self, request):
        data = {"deleted": False,   
                "tipo_mensaje": "error",             
                "mensaje" : "No fue posible eliminar el alerta."}  
        try:
            pk = request.GET.get("id", None)
            legajo_alerta = get_object_or_404(LegajoAlertas, pk=pk)
            legajo = legajo_alerta.fk_legajo
            alerta = legajo_alerta.fk_alerta
            legajo_alerta.delete()

            # Filtrar el registro activo actualmente (sin fecha_fin)
            registro_historial = HistorialLegajoAlertas.objects.filter(
                Q(fk_alerta=alerta) & Q(fk_legajo=legajo) & Q(fecha_fin__isnull=True)
            ).first()

            if registro_historial:
                registro_historial.eliminada_por = request.user.usuarios
                registro_historial.fecha_fin = date.today()
                registro_historial.save()
        
                data = {"deleted": True,   
                "tipo_mensaje": "success",             
                "mensaje" : "Alerta eliminada correctamente."} 
            else:
                data = {"deleted": True,   
                "tipo_mensaje": "warning",             
                "mensaje" : "Alerta eliminada, con errores en el historial."}
        except:
            pass

        return JsonResponse(data)
    

class CategoriasSelectView(View):
    def get(self, request, *args, **kwargs):
        alerta_id = request.GET.get('alerta_id')
        if alerta_id:
            categorias = CategoriaAlertas.objects.filter(alertas__id=alerta_id)
        else:
            categorias = CategoriaAlertas.objects.all()

        data = [{'id': categoria.id, 'text': categoria.nombre} for categoria in categorias]
        return JsonResponse(data, safe=False)


class AlertasSelectView(View):
    def get(self, request, *args, **kwargs):
        categoria_id = request.GET.get('categoria_id')
        if categoria_id:
            alertas = Alertas.objects.filter(fk_categoria_id=categoria_id)
        else:
            alertas = Alertas.objects.all()

        data = [{'id': alerta.id, 'text': alerta.nombre} for alerta in alertas]
        return JsonResponse(data, safe=False)


# endregion


# region ############################################################### DIMENSIONES


class DimensionesUpdateView(PermisosMixin, SuccessMessageMixin, UpdateView):
    permission_required = "Usuarios.rol_admin"
    template_name = "Legajos/legajosdimensiones_form.html"
    model = DimensionFamilia
    form_class = DimensionFamiliaForm
    form_vivienda = DimensionViviendaForm
    form_salud = DimensionSaludForm
    form_educacion = DimensionEducacionForm
    form_economia = DimensionEconomiaForm
    form_trabajo = DimensionTrabajoForm
    success_message = "Editado correctamente"

    def get_context_data(self, **kwargs):
        context = super(DimensionesUpdateView, self).get_context_data(**kwargs)

        pk = self.get_object().fk_legajo.id
        legajo = Legajos.objects.filter(id=pk).first()
        dimension_vivienda = DimensionVivienda.objects.filter(fk_legajo__id=pk).first()
        dimension_salud = DimensionSalud.objects.filter(fk_legajo__id=pk).first()
        dimension_educacion = DimensionEducacion.objects.filter(fk_legajo__id=pk).first()
        dimension_economia = DimensionEconomia.objects.filter(fk_legajo__id=pk).first()
        dimension_trabajo = DimensionTrabajo.objects.filter(fk_legajo__id=pk).first()

        context["legajo"] = legajo
        context["form_vivienda"] = self.form_vivienda(instance=dimension_vivienda)
        context["form_salud"] = self.form_salud(instance=dimension_salud)
        context["form_educacion"] = self.form_educacion(instance=dimension_educacion)
        context["form_economia"] = self.form_economia(instance=dimension_economia)
        context["form_trabajo"] = self.form_trabajo(instance=dimension_trabajo)

        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)

        pk = self.get_object().fk_legajo.id

        legajo_dim_vivienda = DimensionVivienda.objects.get(fk_legajo__id=pk)
        legajo_dim_salud = DimensionSalud.objects.get(fk_legajo__id=pk)
        legajo_dim_educacion = DimensionEducacion.objects.get(fk_legajo__id=pk)
        legajo_dim_economia = DimensionEconomia.objects.get(fk_legajo__id=pk)
        legajo_dim_trabajo = DimensionTrabajo.objects.get(fk_legajo__id=pk)
        form_multiple = self.form_class(self.request.POST).data.copy()

        # cambio el valor 'on' y 'off' por True/False
        for clave, valor in form_multiple.items():
            if valor == "on":
                form_multiple[clave] = True

            elif valor == "off":
                form_multiple[clave] = False

        # dimension vivienda

        fields_mapping_vivienda = {
            "tipo": "tipo",
            "material": "material",
            "pisos": "pisos",
            "posesion": "posesion",
            "cant_ambientes": "cant_ambientes",
            "cant_convivientes": "cant_convivientes",
            "cant_menores": "cant_menores",
            "cant_camas": "cant_camas",
            "cant_hogares": "cant_hogares",
            "hay_agua_caliente": "hay_agua_caliente",
            "hay_desmoronamiento": "hay_desmoronamiento",
            "hay_banio": "hay_banio",
            "PoseenCeludar":"PoseenCeludar",
            "PoseenPC":"PoseenPC",
            "Poseeninternet":"Poseeninternet",
            "ContextoCasa":"ContextoCasa",
            "CondicionDe":"CondicionDe",
            "CantidadAmbientes":"CantidadAmbientes",
            "gas":"gas",
            "obs_vivienda": "obs_vivienda",
        }

        for field in fields_mapping_vivienda:
            value = form_multiple.get(field)

            if value:
                setattr(
                    legajo_dim_vivienda,
                    fields_mapping_vivienda.get(field, field),
                    value,
                )

            else:
                setattr(legajo_dim_vivienda, field, None)

        legajo_dim_vivienda.save()

        # dimension salud

        fields_mapping_salud = {
            "lugares_atencion": "lugares_atencion",
            "frec_controles": "frec_controles",
            "hay_obra_social": "hay_obra_social",
            "hay_enfermedad": "hay_enfermedad",
            "hay_discapacidad": "hay_discapacidad",
            "hay_cud": "hay_cud",
            "obs_salud": "obs_salud",
        }

        for field in fields_mapping_salud:
            value = form_multiple.get(field)

            if value:
                setattr(
                    legajo_dim_salud,
                    fields_mapping_salud.get(field, field),
                    value,
                )

            else:
                setattr(legajo_dim_salud, field, None)

        legajo_dim_salud.save()

        # dimension educacion

        fields_mapping_educacion = {
            "max_nivel": "max_nivel",
            "estado_nivel": "estado_nivel",
            "asiste_escuela": "asiste_escuela",
            "institucion": "institucion",
            "gestion": "gestion",
            "ciclo": "ciclo",
            "grado": "grado",
            "turno": "turno",
            "obs_educacion": "obs_educacion",
            "provinciaInstitucion": "provinciaInstitucion",
            "localidadInstitucion": "localidadInstitucion",
            "municipioInstitucion": "municipioInstitucion",
            "barrioInstitucion": "barrioInstitucion",
            "calleInstitucion": "calleInstitucion",
            "numeroInstitucion": "numeroInstitucion",
            "interesEstudio": "interesEstudio",
            "interesCurso": "interesCurso",
            "nivelIncompleto": "nivelIncompleto",
            "sinEduFormal": "sinEduFormal",
            "realizandoCurso": "realizandoCurso",
            "areaCurso": "areaCurso",
            "interesCapLab": "interesCapLab",
            "areaOficio": "areaOficio",
            "oficio":"oficio"
            
        }

        for field in fields_mapping_educacion:
            value = form_multiple.get(field)

            if value:
                setattr(
                    legajo_dim_educacion,
                    fields_mapping_educacion.get(field, field),
                    value,
                )

            else:
                setattr(legajo_dim_educacion, field, None)

        legajo_dim_educacion.save()

        # dimension economia

        fields_mapping_economia = {
            "ingresos": "ingresos",
            "recibe_plan": "recibe_plan",
            "m2m_planes": "m2m_planes",
            "cant_aportantes": "cant_aportantes",
            "obs_economia": "obs_economia",
        }

        for field in fields_mapping_economia:
            value = form_multiple.get(field)

            if field == "m2m_planes":
                lista = form_multiple.getlist("m2m_planes")

                legajo_dim_economia.m2m_planes.set(lista)

            else:
                if value:
                    setattr(
                        legajo_dim_economia,
                        fields_mapping_economia.get(field, field),
                        value,
                    )

                else:
                    setattr(legajo_dim_economia, field, None)

        legajo_dim_economia.save()

        # dimension trabajo

        fields_mapping_trabajo = {
            "tiene_trabajo": "tiene_trabajo",
            "modo_contratacion": "modo_contratacion",
            "ocupacion": "ocupacion",
            "conviviente_trabaja": "conviviente_trabaja",
            "obs_trabajo": "obs_trabajo",
            "horasSemanales": "horasSemanales",
            "actividadRealizadaComo": "actividadRealizadaComo",
            "duracionTrabajo": "duracionTrabajo",
            "aportesJubilacion": "aportesJubilacion",
            "TiempoBusquedaLaboral": "TiempoBusquedaLaboral",
            "busquedaLaboral": "busquedaLaboral",
            "noBusquedaLaboral": "noBusquedaLaboral"

        }

        for field in fields_mapping_trabajo:
            value = form_multiple.get(field)

            if value:
                setattr(
                    legajo_dim_trabajo,
                    fields_mapping_trabajo.get(field, field),
                    value,
                )

            else:
                setattr(legajo_dim_trabajo, field, None)

        legajo_dim_trabajo.save()

        if "form_step1" in self.request.POST:
            self.object.save()

            return redirect("legajos_editar", pk=pk)

        if "form_step2" in self.request.POST:
            self.object.save()

            return redirect("legajos_ver", pk=pk)

        if "form_step3" in self.request.POST:
            self.object.save()

            return redirect("grupofamiliar_crear", pk=pk)

        self.object = form.save()

        return super().form_valid(form)


class DimensionesDetailView(PermisosMixin, DetailView):
    permission_required = "Usuarios.rol_admin"
    model = Legajos
    template_name = "Legajos/legajosdimensiones_detail.html"


# endregion


#region ################################################################ ARCHIVOS
class LegajosArchivosListView(PermisosMixin, ListView):
    permission_required = "Usuarios.rol_admin"
    model = LegajosArchivos
    template_name="Legajos/legajosarchivos_list.html"

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        context["legajo_archivos"] = LegajosArchivos.objects.filter(fk_legajo=pk)
        context["legajo"] = Legajos.objects.filter(id=pk).first()
        return context

class LegajosArchivosCreateView(PermisosMixin, SuccessMessageMixin, CreateView):
    permission_required = "Usuarios.rol_admin"
    model = LegajosArchivos
    form_class = LegajosArchivosForm
    success_message = "Archivo actualizado correctamente."

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        archivos = LegajosArchivos.objects.filter(fk_legajo=pk)
        imagenes = archivos.filter(tipo="Imagen")
        documentos = archivos.filter(tipo="Documento")
        legajo = Legajos.objects.filter(pk=pk).first()
        context["imagenes"] = imagenes
        context["documentos"] = documentos
        context["legajo"] = legajo
        return context


class CreateArchivo(TemplateView):
    def post(self, request):
        pk = request.POST.get("pk") 
        legajo = Legajos.objects.get(id=pk)
        response_data_list = []  # Lista para almacenar las respuestas de los archivos

        files = request.FILES.getlist('file')  # Acceder a los archivos enviados desde Dropzone

        for f in files:
            if f:
                file_extension = f.name.split('.')[-1].lower()
                if file_extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
                    tipo = 'Imagen'
                else:
                    tipo = 'Documento'

                legajo_archivo = LegajosArchivos.objects.create(
                    fk_legajo=legajo,
                    archivo=f,
                    tipo=tipo
                )

                response_data = {
                    'id': legajo_archivo.id,
                    'tipo': legajo_archivo.tipo,
                    'archivo_url': legajo_archivo.archivo.url,
                }

                response_data_list.append(response_data)  # Agregar la respuesta actual a la lista

        return JsonResponse(response_data_list, safe=False)  # Devolver la lista completa de respuestas como JSON


class DeleteArchivo(PermisosMixin, View):
    permission_required = "Usuarios.rol_admin"

    def get(self, request):
        try:
            pk = request.GET.get("id", None)
            legajo_archivo = get_object_or_404(LegajosArchivos, pk=pk)
            legajo_archivo.delete()

            data = {"deleted": True,   
                "tipo_mensaje": "success",             
                "mensaje" : "Archivo eliminado correctamente."} 
        except:
            data = {"deleted": False,   
                "tipo_mensaje": "error",             
                "mensaje" : "No fue posible eliminar el archivo."}  

        return JsonResponse(data)
    

class programasIntervencionesView(TemplateView):
    template_name = "Legajos/programas_intervencion.html"
    model = Legajos


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        legajo = Legajos.objects.filter(pk=self.kwargs["pk"]).first()

        context["legajo"] = legajo
        
        return context

class accionesSocialesView(TemplateView):
    template_name = "Legajos/acciones_sociales.html"
    model = Legajos


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        legajo = Legajos.objects.filter(pk=self.kwargs["pk"]).first()

        context["legajo"] = legajo
        
        return context

class intervencionesSaludView(TemplateView):
    template_name = "Legajos/intervenciones_salud.html"
    model = Legajos


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        legajo = Legajos.objects.filter(pk=self.kwargs["pk"]).first()

        context["legajo"] = legajo
        
        return context

class indicesView(TemplateView):
    template_name = "Legajos/indices.html"
    model = Legajos


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        legajo = Legajos.objects.filter(pk=self.kwargs["pk"]).first()

        context["legajo"] = legajo
        
        return context      

class indicesDetalleView(TemplateView):
    template_name = "Legajos/indices_detalle.html"
    model = Legajos


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        legajo = Legajos.objects.filter(pk=self.kwargs["pk"]).first()

        context["legajo"] = legajo
        
        return context    


# endregion ###########################################################

# region ############################################################### GRUPO Hogar


class LegajosGrupoHogarCreateView(CreateView):
    permission_required = "Usuarios.rol_admin"
    model = LegajoGrupoHogar
    form_class = LegajoGrupoHogarForm
    

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        legajo_principal = Legajos.objects.filter(pk=pk).first()
        # Calcula la edad utilizando la función 'edad' del modelo
             

        context = super().get_context_data(**kwargs)
        context["hogar_1"] = LegajoGrupoHogar.objects.filter(fk_legajo_1Hogar=pk)
        context["hogar_2"] = LegajoGrupoHogar.objects.filter(fk_legajo_2Hogar=pk)
        context["count_hogar"] = context["hogar_1"].count() + context["hogar_2"].count()
        context["legajo_principal"] = legajo_principal
        context["pk"] = pk
        #context["hogar_fk"] = LegajoGrupoHogar.objects.get(fk_legajo=pk).id
        #context["hogar_fk"] = LegajoGrupoHogar.objects.filter(fk_legajo=pk).id
        return context
        

    def form_valid(self, form):
        pk = self.kwargs["pk"]
        estado_relacion = form.cleaned_data['estado_relacion']


        # Crea el objeto Legajos
        try:
            nuevo_legajo = form.save()
            DimensionFamilia.objects.create(fk_legajo=nuevo_legajo)
            DimensionVivienda.objects.create(fk_legajo=nuevo_legajo)
            DimensionSalud.objects.create(fk_legajo=nuevo_legajo)
            DimensionEconomia.objects.create(fk_legajo=nuevo_legajo)
            DimensionEducacion.objects.create(fk_legajo=nuevo_legajo)
            DimensionTrabajo.objects.create(fk_legajo=nuevo_legajo)
            LegajoGrupoHogar.objects.create(fk_legajo=nuevo_legajo)
        except:
            return messages.error(self.request, "Verifique que no exista un legajo con ese DNI y NÚMERO.")

        # Crea el objeto LegajoGrupoFamiliar con los valores del formulario
         # vinculo_data = VINCULO_MAP.get(vinculo)
         # if not vinculo_data:
           #   return messages.error(self.request, "Vinculo inválido.")

        # crea la relacion de grupo familiar
        legajo_principal = Legajos.objects.get(id=pk)
        try:
            legajo_grupo_familiar = LegajoGrupoFamiliar.objects.create(
                fk_legajo_1=legajo_principal,
                fk_legajo_2=nuevo_legajo,
                #  vinculo=vinculo_data["vinculo"],
                 # vinculo_inverso=vinculo_data["vinculo_inverso"],
                estado_relacion=estado_relacion
            )
        except:
            return messages.error(self.request, "Verifique que no exista un legajo con ese DNI y NÚMERO.")

        messages.success(self.request, "Familair agregado correctamente.")
        # Redireccionar a la misma página después de realizar la acción con éxito
        return HttpResponseRedirect(self.request.path_info)
    
def busqueda_hogar(request):
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        res = None
        busqueda = request.POST.get("busqueda")
        legajo_principal_id = request.POST.get("id")
        legajos_asociadosfk1 = LegajoGrupoHogar.objects.filter(fk_legajo_1Hogar_id=legajo_principal_id).values_list('fk_legajo_2Hogar_id', flat=True)
        legajos_asociadosfk2 = LegajoGrupoHogar.objects.filter(fk_legajo_2Hogar_id=legajo_principal_id).values_list('fk_legajo_1Hogar_id', flat=True)
        hogares = (
            Legajos.objects.filter(~Q(id=legajo_principal_id) & (Q(apellido__icontains=busqueda) | Q(documento__icontains=busqueda)))
            .exclude(id__in=legajos_asociadosfk1)
            .exclude(id__in=legajos_asociadosfk2)
        )

        if len(hogares) > 0 and busqueda:
            data = [
                {
                    'pk': hogar.pk,
                    'nombre': hogar.nombre,
                    'apellido': hogar.apellido,
                    'documento': hogar.documento,
                    'tipo_doc': hogar.tipo_doc,
                    'fecha_nacimiento': hogar.fecha_nacimiento,
                    'sexo': hogar.sexo,
                    # Otros campos que deseas incluir
                }
                for hogar in hogares
            ]
            res = data
        else:
            res = ""

        return JsonResponse({"data": res})

    return JsonResponse({"data": "this is data"})


class LegajoGrupoHogarList(ListView):
    model = LegajoGrupoFamiliar

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        context["familiares_fk1"] = LegajoGrupoFamiliar.objects.filter(fk_legajo_1=pk)
        context["familiares_fk2"] = LegajoGrupoFamiliar.objects.filter(fk_legajo_2=pk)
        context["count_familia"] = context["familiares_fk1"].count() + context["familiares_fk1"].count()
        context["nombre"] = Legajos.objects.filter(pk=pk).first()
        context["pk"] = pk
        return context


class CreateGrupoHogar(View):
    def get(self, request, **kwargs):
        fk_legajo_1 = request.GET.get("fk_legajo_1", None)
        fk_legajo_2 = request.GET.get("fk_legajo_2", None)
        estado_relacion = request.GET.get("estado_relacion", None)
        obj = None

        obj = LegajoGrupoHogar.objects.create(
            fk_legajo_1Hogar_id=fk_legajo_1,
            fk_legajo_2Hogar_id=fk_legajo_2,
            estado_relacion=estado_relacion,
        )

        familiar = {
            "id": obj.id,
            "fk_legajo_1": obj.fk_legajo_1Hogar.id,
            "fk_legajo_2": obj.fk_legajo_2Hogar.id,
            "nombre": obj.fk_legajo_2Hogar.nombre,
            "apellido": obj.fk_legajo_2Hogar.apellido,
            "foto": obj.fk_legajo_2Hogar.foto.url if obj.fk_legajo_2Hogar.foto else None,
        }
        data = {  
                "tipo_mensaje": "success",             
                "mensaje" : "Vínculo hogar agregado correctamente."}  

        return JsonResponse({"hogar": familiar, "data": data})


class DeleteGrupoHogar(View):
    def get(self, request):
        pk = request.GET.get("id", None)
        try:
            familiar = get_object_or_404(LegajoGrupoHogar, pk=pk)
            familiar.delete()
            data = {"deleted": True,   
                "tipo_mensaje": "success",             
                "mensaje" : "Vínculo del hogar eliminado correctamente."} 
        except:
            data = {"deleted": False,   
                "tipo_mensaje": "error",             
                "mensaje" : "No fue posible eliminar el vinculo."}  

        return JsonResponse(data)