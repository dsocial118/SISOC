import calendar  # pylint: disable=too-many-lines
import json

import locale
import logging
from datetime import date, datetime, timedelta

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import models, transaction
from django.db.models import Case, IntegerField, Q, Value, When
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.messages import get_messages

from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
    View,
)

from configuraciones.models import (
    Municipio,
    Provincia,
)
from ciudadanos.constants import EMOJIS_BANDERAS
from ciudadanos.forms import (
    DimensionEconomiaForm,
    DimensionEducacionForm,
    DimensionFamiliaForm,
    DimensionSaludForm,
    DimensionTrabajoForm,
    DimensionViviendaForm,
    IntervencionForm,
    GrupoHogarForm,
    AlertaForm,
    ArchivoForm,
    DerivacionForm,
    CiudadanoForm,
    CiudadanoUpdateForm,
    LlamadoForm,
    FamiliarForm,
    ProgramaForm,
)
from ciudadanos.models import (
    ActividadRealizada,
    Agua,
    AportesJubilacion,
    AreaCurso,
    AsisteEscuela,
    CantidadAmbientes,
    CentrosSalud,
    Condicion,
    Organismo,
    Programa,
    UbicacionVivienda,
    Desague,
    DimensionEconomia,
    DimensionEducacion,
    DimensionFamilia,
    DimensionSalud,
    DimensionTrabajo,
    DimensionVivienda,
    DuracionTrabajo,
    EstadoDerivacion,
    EstadoNivelEducativo,
    EstadoRelacion,
    Frecuencia,
    Gas,
    Grado,
    HistorialAlerta,
    Inodoro,
    InstitucionEducativas,
    Intervencion,
    Alerta,
    GrupoFamiliar,
    GrupoHogar,
    Localidad,
    Ciudadano,
    Archivo,
    Derivacion,
    Llamado,
    ModoContratacion,
    MotivoNivelIncompleto,
    Nacionalidad,
    NivelEducativo,
    NobusquedaLaboral,
    SubIntervencion,
    SubtipoLlamado,
    TiempoBusquedaLaboral,
    TipoConstruccionVivienda,
    TipoGestion,
    TipoLlamado,
    TipoPisosVivienda,
    TipoPosesionVivienda,
    TipoTechoVivienda,
    TipoVivienda,
    Turno,
    VinculoFamiliar,
    CiudadanoPrograma,
    Circuito,
    CategoriaAlerta,
    Dimension,
)
from ciudadanos.utils import recortar_imagen

locale.setlocale(locale.LC_ALL, "es_AR.UTF-8")

logger = logging.getLogger("django")

ROL_ADMIN = "usuarios.rol_admin"


@csrf_exempt
@require_POST
def actualizar_programas(request, ciudadano_id):
    ciudadano = get_object_or_404(Ciudadano, id=ciudadano_id)
    form = ProgramaForm(request.POST)
    if request.POST:
        programas_ids = request.POST.getlist("programas")
        programas_duplicados = []
        nuevos_programas = []

        for programa_id in programas_ids:
            programa = Programa.objects.get(id=programa_id)
            if CiudadanoPrograma.objects.filter(
                ciudadano=ciudadano, programas=programa
            ).exists():
                programas_duplicados.append(programa.nombre)
            else:
                ciudadano_programa = CiudadanoPrograma.objects.create(
                    ciudadano=ciudadano,
                    programas=programa,
                    creado_por=request.user,
                )
                nuevos_programas.append(
                    {
                        "id": ciudadano_programa.id,
                        "programa_id": programa.id,
                        "nombre": programa.nombre,
                        "ciudadano_id": ciudadano.id,
                    }
                )

        # Enviar mensajes en caso de programas duplicados
        if programas_duplicados:
            messages.error(
                request,
                f"Programa duplicado: {', '.join(programas_duplicados)}",
            )

        if nuevos_programas:
            messages.success(request, "Programa agregado.")

        # Recuperar mensajes almacenados
        storage = get_messages(request)
        mensajes = [
            {"level": m.level, "message": m.message, "tags": m.tags} for m in storage
        ]

        return JsonResponse({"programas": nuevos_programas, "messages": mensajes})

    else:
        messages.error(
            request,
            "Se produjo un error al procesar el formulario. Por favor, inténtalo de nuevo.",
        )
        storage = get_messages(request)
        mensajes = [
            {"level": m.level, "message": m.message, "tags": m.tags} for m in storage
        ]
        return JsonResponse({"errors": form.errors, "messages": mensajes}, status=400)


def eliminar_programa(request):
    if request.method == "POST":
        program_id = request.POST.get("program_id")

        if not program_id:
            return JsonResponse(
                {"success": False, "message": "ID del programa no proporcionado"},
                status=400,
            )

        try:
            # Intentamos eliminar el programa específico de la tabla CiudadanoPrograma
            programa = CiudadanoPrograma.objects.get(id=program_id)
            programa.delete()

            return JsonResponse(
                {"success": True, "message": "Programa eliminado correctamente."}
            )

        except CiudadanoPrograma.DoesNotExist:
            return JsonResponse(
                {"success": False, "message": "No se encontró el programa."}, status=404
            )

        except Exception as e:
            logging.error(f"An error occurred: {str(e)}")
            return JsonResponse(
                {
                    "success": False,
                    "message": "Ocurrió un error interno. Por favor, inténtalo de nuevo más tarde.",
                },
                status=500,
            )

    return JsonResponse(
        {"success": False, "message": "Método no permitido"}, status=405
    )


class CiudadanosReportesListView(ListView):
    template_name = "ciudadanos/ciudadanos_reportes.html"
    model = Derivacion

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        organismos = cache.get("organismos")
        if not organismos:
            organismos = Organismo.objects.all().values("id", "nombre")
            cache.set("organismos", organismos, 60)

        programas = cache.get("programas")
        if not programas:
            programas = Programa.objects.all().values("id", "nombre")
            cache.set("programas", programas, 60)

        estados = cache.get("estados_derivacion")
        if not estados:
            estados = EstadoDerivacion.objects.all().values("id", "estado")
            cache.set("estados_derivacion", estados, 60)

        context["organismos"] = organismos
        context["programas"] = programas
        context["estados"] = estados
        return context

    def get_queryset(self):
        nombre_completo_ciudadano = self.request.GET.get("busqueda")
        data_organismo = self.request.GET.get("data_organismo")
        data_programa = self.request.GET.get("data_programa")
        data_estado = self.request.GET.get("data_estado")
        data_fecha_desde = self.request.GET.get("data_fecha_derivacion")

        filters = Q()

        if data_programa:
            filters &= Q(programa=data_programa)
        if data_organismo:
            filters &= Q(organismo=data_organismo)
        if nombre_completo_ciudadano:
            filters &= (
                Q(ciudadano__nombre__icontains=nombre_completo_ciudadano)
                | Q(ciudadano__apellido__icontains=nombre_completo_ciudadano)
                | Q(ciudadano__documento__icontains=nombre_completo_ciudadano)
            )
        if data_estado:
            filters &= Q(estado=data_estado)
        if data_fecha_desde:
            filters &= Q(fecha_creado__gte=data_fecha_desde)

        object_list = (
            Derivacion.objects.filter(filters)
            .select_related("programa", "organismo", "ciudadano")
            .distinct()
        )

        if not object_list.exists():
            messages.warning(self.request, "La búsqueda no arrojó resultados.")

        return object_list


class CiudadanosListView(ListView):
    model = Ciudadano
    template_name = "ciudadanos/ciudadanos_list.html"
    context_object_name = "ciudadanos"
    paginate_by = 10  # Número de objetos por página

    def get_queryset(self):
        if not hasattr(self, "_cached_queryset"):
            queryset = (
                super()
                .get_queryset()
                .only(
                    "id",
                    "apellido",
                    "nombre",
                    "documento",
                    "tipo_documento",
                    "sexo",
                    "estado",
                )
            )
            query = self.request.GET.get("busqueda", "")

            if query:
                filter_condition = Q(apellido__icontains=query)
                if query.isnumeric():
                    filter_condition |= Q(documento__contains=query)
                queryset = queryset.filter(filter_condition)
            self._cached_queryset = (
                queryset  # pylint: disable=attribute-defined-outside-init
            )

        return self._cached_queryset

    def get(self, request, *args, **kwargs):
        query = self.request.GET.get("busqueda")
        if query:
            self.object_list = (
                self.get_queryset()
            )  # pylint: disable=attribute-defined-outside-init
            size_queryset = self.object_list.count()
            if size_queryset == 1:
                pk = self.object_list.first().id
                return redirect("ciudadanos_ver", pk=pk)
            elif size_queryset == 0:
                messages.warning(self.request, "La búsqueda no arrojó resultados.")

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get("busqueda")
        mostrar_resultados = bool(query)
        page_obj = context.get("page_obj")

        if page_obj:
            context["page_range"] = page_obj.paginator.get_elided_page_range(
                number=page_obj.number
            )

        context.update(
            {
                "mostrar_resultados": mostrar_resultados,
                "query": query,
            }
        )

        return context


class CiudadanosDetailView(DetailView):
    model = Ciudadano
    template_name = "ciudadanos/ciudadano_detail.html"

    def get_context_data(
        self, **kwargs
    ):  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        pk = self.kwargs["pk"]
        context = super().get_context_data(**kwargs)

        ciudadano = context["object"]

        fecha_actual = datetime.now().date()

        ciudadano_alertas = cache.get("ciudadano_alertas")
        alertas = cache.get("alertas")
        familiares = cache.get("familiares")
        hogar_familiares = cache.get("hogar_familiares")
        files = cache.get("files")
        ciudadano_alertas_organizadas = cache.get("ciudadano_alertas_organizadas")
        count_alertas = cache.get("count_alertas")
        count_alta = cache.get("count_alta")
        count_media = cache.get("count_media")
        count_baja = cache.get("count_baja")
        alertas_alta = cache.get("alertas_alta")
        alertas_media = cache.get("alertas_media")
        alertas_baja = cache.get("alertas_baja")
        historial_alertas = cache.get("historial_alertas")
        count_intervenciones = cache.get("count_intervenciones")
        dimensionfamilia = cache.get("dimensionfamilia")
        dimensionvivienda = cache.get("dimensionvivienda")
        dimensionsalud = cache.get("dimensionsalud")
        dimensiontrabajo = cache.get("dimensiontrabajo")
        datos_json = cache.get("datos_json")
        emoji_nacionalidad = cache.get("emoji_nacionalidad")

        if not ciudadano_alertas:
            ciudadano_alertas = Alerta.objects.filter(ciudadano=pk).select_related(
                "categoria"
            )
            cache.set("ciudadano_alertas", ciudadano_alertas, 60)
        if not alertas:
            alertas = HistorialAlerta.objects.filter(ciudadano=pk).values(
                "fecha_inicio", "fecha_fin", "alerta__categoria__dimension"
            )
            cache.set("alertas", alertas, 60)
        if not familiares:
            familiares = GrupoFamiliar.objects.filter(
                Q(ciudadano_1=pk) | Q(ciudadano_2=pk)
            ).values(
                "ciudadano_1__nombre",
                "ciudadano_1__apellido",
                "ciudadano_1__id",
                "ciudadano_1__foto",
                "ciudadano_2__nombre",
                "ciudadano_2__apellido",
                "ciudadano_2__id",
                "ciudadano_2__foto",
                "vinculo",
                "vinculo_inverso",
            )
            cache.set("familiares", familiares, 60)
        if not hogar_familiares:
            hogar_familiares = GrupoHogar.objects.filter(
                Q(ciudadano_1Hogar=pk) | Q(ciudadano_2Hogar=pk)
            ).values(
                "ciudadano_2Hogar_id",
                "ciudadano_2Hogar",
                "ciudadano_1Hogar_id",
                "ciudadano_1Hogar",
                "ciudadano_1Hogar__nombre",
                "ciudadano_2Hogar__nombre",
                "ciudadano_1Hogar__foto",
                "ciudadano_2Hogar__foto",
                "estado_relacion",
            )
            cache.set("hogar_familiares", hogar_familiares, 60)
        if not files:
            files = Archivo.objects.filter(
                Q(tipo="Imagen") | Q(tipo="Documento"), ciudadano=pk
            )
            cache.set("files", files, 60)
        if not ciudadano_alertas_organizadas:
            ciudadano_alertas_organizadas = ciudadano_alertas.annotate(
                es_critica=Case(
                    When(gravedad="Critica", then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                ),
                es_importante=Case(
                    When(gravedad="Importante", then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                ),
                es_precaucion=Case(
                    When(gravedad="Precaución", then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                ),
            )
            cache.set(
                "ciudadano_alertas_organizadas", ciudadano_alertas_organizadas, 60
            )
        if not count_alertas:
            count_alertas = ciudadano_alertas.count()
            cache.set("count_alertas", count_alertas, 60)
        if not count_alta:
            count_alta = ciudadano_alertas_organizadas.filter(es_critica=True).count()
            cache.set("count_alta", count_alta, 60)
        if not count_media:
            count_media = ciudadano_alertas_organizadas.filter(
                es_importante=True
            ).count()
            cache.set("count_media", count_media, 60)
        if not count_baja:
            count_baja = ciudadano_alertas_organizadas.filter(
                es_precaucion=True
            ).count()
            cache.set("count_baja", count_baja, 60)
        if not alertas_alta:
            alertas_alta = ciudadano_alertas_organizadas.filter(es_critica=True)
            cache.set("alertas_alta", alertas_alta, 60)
        if not alertas_media:
            alertas_media = ciudadano_alertas_organizadas.filter(es_importante=True)
            cache.set("alertas_media", alertas_media, 60)
        if not alertas_baja:
            alertas_baja = ciudadano_alertas_organizadas.filter(es_precaucion=True)
            cache.set("alertas_baja", alertas_baja, 60)
        if not historial_alertas:
            historial_alertas = alertas.exists()
            cache.set("historial_alertas", historial_alertas, 60)
        if not count_intervenciones:
            count_intervenciones = Derivacion.objects.filter(ciudadano=pk).count()
            cache.set("count_intervenciones", count_intervenciones, 60)
        if not dimensionfamilia:
            dimensionfamilia = (
                DimensionFamilia.objects.filter(ciudadano=pk)
                .values(
                    "cant_hijos",
                    "otro_responsable",
                    "hay_embarazadas",
                    "hay_priv_libertad",
                    "hay_prbl_smental",
                    "hay_enf_cronica",
                    "obs_familia",
                    "hay_fam_discapacidad",
                )
                .first()
            )
            cache.set("dimensionfamilia", dimensionfamilia, 60)
        if not dimensionvivienda:
            dimensionvivienda = (
                DimensionVivienda.objects.filter(ciudadano=pk)
                .values(
                    "posesion",
                    "tipo",
                    "material",
                    "pisos",
                    "cant_ambientes",
                    "cant_camas",
                    "cant_hogares",
                    "cant_convivientes",
                    "cant_menores",
                    "hay_banio",
                    "hay_agua_caliente",
                    "hay_desmoronamiento",
                    "ubicacion_vivienda",
                    "PoseenPC",
                    "Poseeninternet",
                    "PoseenCelular",
                    "obs_vivienda",
                )
                .first()
            )
            cache.set("dimensionvivienda", dimensionvivienda, 60)

        if not dimensionsalud:
            dimensionsalud = (
                DimensionSalud.objects.filter(ciudadano=pk)
                .values(
                    "lugares_atencion",
                    "frecuencia_controles_medicos",
                    "hay_enfermedad",
                    "hay_obra_social",
                    "hay_discapacidad",
                    "hay_cud",
                    "obs_salud",
                )
                .first()
            )
            cache.set("dimensionsalud", dimensionsalud, 60)
        if not dimensiontrabajo:
            dimensiontrabajo = (
                DimensionTrabajo.objects.filter(ciudadano=pk)
                .values(
                    "tiene_trabajo",
                    "ocupacion",
                    "modo_contratacion",
                    "conviviente_trabaja",
                    "obs_trabajo",
                )
                .first()
            )
            cache.set("dimensiontrabajo", dimensiontrabajo, 60)
        if not datos_json:
            datos_json = self.grafico_evolucion_de_riesgo(fecha_actual, alertas)
            cache.set("datos_json", datos_json, 60)
        if not emoji_nacionalidad:
            emoji_nacionalidad = EMOJIS_BANDERAS.get(ciudadano.nacionalidad, "")
            cache.set("emoji_nacionalidad", emoji_nacionalidad, 60)

        context["familiares_fk1"] = [
            familiar
            for familiar in familiares
            if familiar["ciudadano_1__id"] == int(pk)
        ]
        context["familiares_fk2"] = [
            familiar
            for familiar in familiares
            if familiar["ciudadano_2__id"] == int(pk)
        ]
        context["count_familia"] = len(familiares)

        context["hogar_familiares_fk1"] = [
            familiar
            for familiar in hogar_familiares
            if familiar["ciudadano_1Hogar"] == int(pk)
        ]
        context["hogar_familiares_fk2"] = [
            familiar
            for familiar in hogar_familiares
            if familiar["ciudadano_2Hogar"] == int(pk)
        ]
        context["hogar_count_familia"] = len(hogar_familiares)

        context["files_img"] = files.filter(tipo="Imagen")
        context["files_docs"] = files.filter(tipo="Documento")

        context["count_alertas"] = count_alertas
        context["count_alta"] = count_alta
        context["count_media"] = count_media
        context["count_baja"] = count_baja

        context["alertas_alta"] = alertas_alta
        context["alertas_media"] = alertas_media
        context["alertas_baja"] = alertas_baja

        context["historial_alertas"] = historial_alertas

        context["count_intervenciones"] = count_intervenciones

        context["dimensionfamilia"] = dimensionfamilia

        context["dimensionvivienda"] = dimensionvivienda

        context["dimensionsalud"] = dimensionsalud

        context["dimensiontrabajo"] = dimensiontrabajo

        context["datos_json"] = datos_json

        context["emoji_nacionalidad"] = emoji_nacionalidad

        # PROGRAMAS
        context["form_prog"] = ProgramaForm()
        ciudadano_programas = CiudadanoPrograma.objects.filter(ciudadano=pk)
        if ciudadano_programas.exists():
            context["ciudadanos_programas"] = ciudadano_programas

        return context

    def grafico_evolucion_de_riesgo(
        self, fecha_actual, alertas
    ):  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        if alertas.exists():
            primer_dia_siguiente_mes = datetime(
                fecha_actual.year, fecha_actual.month % 12 + 1, 1
            )
            fecha_inicio_doce_meses_excepto_mes_anterior = (
                primer_dia_siguiente_mes - timedelta(days=365)
            )

            alertas_ultimo_anio = alertas.filter(
                Q(fecha_inicio__gt=fecha_inicio_doce_meses_excepto_mes_anterior)
                | Q(fecha_fin__gt=fecha_inicio_doce_meses_excepto_mes_anterior)
                | Q(fecha_fin__isnull=True)
            ).distinct()

            dimensiones = {
                str(dimension.id).strip(): dimension.dimension
                for dimension in Dimension.objects.all()
                if dimension.id is not None
            }
            todas_dimensiones = list(dimensiones.keys())
            datos_por_dimension = {
                dimension: [0] * 12 for dimension in todas_dimensiones
            }

            for alerta in alertas_ultimo_anio:
                dimension = alerta["alerta__categoria__dimension"]
                fecha_inicio = alerta["fecha_inicio"]
                fecha_fin = alerta["fecha_fin"] or fecha_actual

                meses_activos = []
                while fecha_inicio <= fecha_fin:
                    meses_activos.append(fecha_inicio.month)
                    fecha_inicio = fecha_inicio.replace(day=1) + timedelta(days=32)
                    fecha_inicio = fecha_inicio.replace(day=1)

                for mes in meses_activos:
                    datos_por_dimension[dimension][mes - 1] += 1

            mes_actual = fecha_actual.month
            datos_por_dimension = {
                dimension: datos_por_dimension[dimension][mes_actual:]
                + datos_por_dimension[dimension][:mes_actual]
                for dimension in todas_dimensiones
            }

            nombres_meses = [
                calendar.month_name[mes].capitalize() for mes in range(1, 13)
            ]
            nombres_meses_ordenados = (
                nombres_meses[mes_actual:] + nombres_meses[:mes_actual]
            )

            datos_por_dimension["meses"] = nombres_meses_ordenados

            datos_json = json.dumps(datos_por_dimension)
        else:
            datos_json = {}

        return datos_json


class CiudadanosDeleteView(DeleteView):
    model = Ciudadano
    success_url = reverse_lazy("ciudadanos")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ciudadano = self.get_object()

        # Crear una lista para almacenar los nombres de las relaciones existentes
        relaciones_existentes = []

        # Agregar los nombres de las relaciones existentes a la lista
        if Archivo.objects.filter(ciudadano=ciudadano).exists():
            relaciones_existentes.append("Archivo")

        if Derivacion.objects.filter(ciudadano=ciudadano).exists():
            relaciones_existentes.append("Derivacion")

        if Alerta.objects.filter(ciudadano=ciudadano).exists():
            relaciones_existentes.append("Alerta")

        if HistorialAlerta.objects.filter(ciudadano=ciudadano).exists():
            relaciones_existentes.append("Historial de Alerta")

        if (
            GrupoFamiliar.objects.filter(ciudadano_1=ciudadano).exists()
            or GrupoFamiliar.objects.filter(ciudadano_2=ciudadano).exists()
        ):
            relaciones_existentes.append("Grupo Familiar")

        # Agregar la lista de nombres de relaciones al contexto
        context["relaciones_existentes"] = relaciones_existentes
        return context

    def form_valid(self, form):
        usuario_eliminacion = self.request.user
        ciudadano = self.get_object()

        # Graba la data del usuario que realiza la eliminacion en el LOG
        mensaje = (
            f"Ciudadano borrado - Nombre: {ciudadano.nombre}, Apellido: {ciudadano.apellido}, "
            f"Tipo de documento: {ciudadano.tipo_documento}, Documento: {ciudadano.documento}"
        )
        logger.info(f"Username: {usuario_eliminacion} - {mensaje}")
        return super().form_valid(form)


class CiudadanosCreateView(CreateView):
    model = Ciudadano
    form_class = CiudadanoForm
    template_name = "ciudadanos/ciudadano_form.html"

    def form_invalid(self, form):
        messages.error(
            self.request,
            "Se produjo un error al crear el ciudadano. Por favor, verifique los datos ingresados.",
        )
        return super().form_invalid(form)

    def form_valid(self, form):
        ciudadano = form.save(commit=False)

        if ciudadano.foto:
            buffer = recortar_imagen(ciudadano.foto)
            ciudadano.foto.save(ciudadano.foto.name, ContentFile(buffer.getvalue()))

        try:
            with transaction.atomic():
                ciudadano.save()

                # Crear las dimensiones
                dimensionfamilia = DimensionFamilia.objects.create(
                    ciudadano_id=ciudadano.id
                )
                print("dimensionfamilia", dimensionfamilia)
                dimensionvivienda = DimensionVivienda.objects.create(
                    ciudadano_id=ciudadano.id
                )
                print("dimensionvivienda", dimensionvivienda)
                dimensiosalud = DimensionSalud.objects.create(ciudadano_id=ciudadano.id)
                print("dimensiosalud", dimensiosalud)
                dimensioneconomia = DimensionEconomia.objects.create(
                    ciudadano_id=ciudadano.id
                )
                print("dimensioneconomia", dimensioneconomia)
                dimensioneducacion = DimensionEducacion.objects.create(
                    ciudadano_id=ciudadano.id
                )
                print("dimensioneducacion", dimensioneducacion)
                dimensiontrabajo = DimensionTrabajo.objects.create(
                    ciudadano_id=ciudadano.id
                )
                print("dimensiontrabajo", dimensiontrabajo)

            # Redireccionar según el botón presionado
            if "form_ciudadanos" in self.request.POST:
                return redirect("ciudadanos_ver", pk=int(ciudadano.id))
            elif "form_step2" in self.request.POST:
                return redirect("ciudadanosdimensiones_editar", pk=int(ciudadano.id))
            return None

        except Exception as e:
            messages.error(
                self.request,
                f"Se produjo un error al crear las dimensiones. Por favor, inténtalo de nuevo. Error: {e}",
            )
            return redirect("ciudadanos_crear")


class CiudadanosUpdateView(UpdateView):
    model = Ciudadano
    form_class = CiudadanoUpdateForm

    def form_valid(self, form):
        ciudadano = form.save(
            commit=False
        )  # Guardamos sin persistir en la base de datos
        current_ciudadano = self.get_object()

        with transaction.atomic():
            # Comprobamos si se ha cargado una nueva foto y si es diferente de la foto actual
            if ciudadano.foto and ciudadano.foto != current_ciudadano.foto:
                buffer = recortar_imagen(ciudadano.foto)
                ciudadano.foto.save(ciudadano.foto.name, ContentFile(buffer.getvalue()))

            self.object = (
                form.save()
            )  # Guardamos el objeto Ciudadano con la imagen recortada (si corresponde)

        if "form_ciudadanos" in self.request.POST:
            return redirect("ciudadanos_ver", pk=self.object.id)

        if "form_step2" in self.request.POST:
            return redirect("ciudadanosdimensiones_editar", pk=ciudadano.id)

        return super().form_valid(form)


class CiudadanosGrupoFamiliarCreateView(CreateView):
    model = GrupoFamiliar
    form_class = FamiliarForm
    paginate_by = 8  # Número de elementos por página

    def get_context_data(self, **kwargs):
        # Paginación

        context = super().get_context_data(**kwargs)
        pk = self.kwargs["pk"]
        ciudadano_principal = Ciudadano.objects.get(pk=pk)
        # Calcula la edad utilizando la función 'edad' del modelo
        edad_calculada = ciudadano_principal.edad()

        # Verifica si tiene más de 18 años
        es_menor_de_18 = True
        if isinstance(edad_calculada, str) and "años" in edad_calculada:
            edad_num = int(edad_calculada.split()[0])
            if edad_num >= 18:
                es_menor_de_18 = False

        # Verificar si tiene un cuidador principal asignado utilizando el método que agregaste al modelo
        tiene_cuidador_ppal = GrupoFamiliar.objects.filter(
            ciudadano_1=ciudadano_principal, cuidador_principal=True
        ).exists()

        # Obtiene los familiares asociados al ciudadano principal
        familiares = GrupoFamiliar.objects.filter(
            Q(ciudadano_1=pk) | Q(ciudadano_2=pk)
        ).values(
            "id",
            "ciudadano_1__nombre",
            "ciudadano_1__apellido",
            "ciudadano_1__id",
            "ciudadano_1__foto",
            "ciudadano_2__nombre",
            "ciudadano_2__apellido",
            "ciudadano_2__id",
            "ciudadano_2__foto",
            "vinculo",
            "vinculo_inverso",
        )

        paginator = Paginator(familiares, self.paginate_by)
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context["familiares_fk1"] = [
            familiar for familiar in page_obj if familiar["ciudadano_1__id"] == int(pk)
        ]
        context["familiares_fk2"] = [
            familiar for familiar in page_obj if familiar["ciudadano_2__id"] == int(pk)
        ]

        context["familiares"] = page_obj
        context["count_familia"] = familiares.count()
        context["ciudadano_principal"] = ciudadano_principal
        context.update(
            {
                "es_menor_de_18": es_menor_de_18,
                "tiene_cuidador_ppal": tiene_cuidador_ppal,
                "pk": pk,
                "id_dimensionfamiliar": DimensionFamilia.objects.get(ciudadano=pk).id,
            }
        )
        return context

    def form_valid(self, form):
        pk = self.kwargs["pk"]
        vinculo = form.cleaned_data["vinculo"]
        conviven = form.cleaned_data["conviven"]
        estado_relacion = form.cleaned_data["estado_relacion"].id
        cuidador_principal = form.cleaned_data["cuidador_principal"]

        # Crea el objeto Ciudadano
        try:
            nuevo_ciudadano = form.save()
            DimensionFamilia.objects.create(ciudadano=nuevo_ciudadano)
            DimensionVivienda.objects.create(ciudadano=nuevo_ciudadano)
            DimensionSalud.objects.create(ciudadano=nuevo_ciudadano)
            DimensionEconomia.objects.create(ciudadano=nuevo_ciudadano)
            DimensionEducacion.objects.create(ciudadano=nuevo_ciudadano)
            DimensionTrabajo.objects.create(ciudadano=nuevo_ciudadano)
        except Exception as e:
            return messages.error(
                self.request,
                f"Verifique que no exista un ciudadano con ese DNI y NÚMERO. Error: {e}",
            )

        # Crea el objeto GrupoFamiliar con los valores del formulario

        try:
            vinculo_instance = VinculoFamiliar.objects.get(vinculo=vinculo)
            estado_relacion_instance = EstadoRelacion.objects.get(pk=estado_relacion)
            ciudadano_principal = Ciudadano.objects.get(id=pk)
            GrupoFamiliar.objects.create(
                ciudadano_1=ciudadano_principal,
                ciudadano_2=nuevo_ciudadano,
                vinculo=vinculo_instance,
                vinculo_inverso=vinculo_instance.inverso,
                estado_relacion=estado_relacion_instance,
                conviven=conviven,
                cuidador_principal=cuidador_principal,
            )

        except Exception as e:
            messages.error(self.request, f"Error al crear el familiar. Error: {e}")
            allowed_hosts = ["example.com", "another-trusted-site.com"]
            full_url = self.request.build_absolute_uri(self.request.path_info)
            if url_has_allowed_host_and_scheme(full_url, allowed_hosts=allowed_hosts):
                return redirect(full_url)
            else:
                return redirect("/")

        messages.success(self.request, "Familiar agregado correctamente.")
        return HttpResponseRedirect(self.request.path_info)


def busqueda_familiares(request):

    res = None
    busqueda = request.POST.get("busqueda", "")
    ciudadano_principal_id = request.POST.get("id")
    page_number = request.POST.get("page", 1)

    if not ciudadano_principal_id:
        return JsonResponse(
            {"error": "ID del ciudadano principal no proporcionado"}, status=400
        )

    ciudadanos_asociados = GrupoFamiliar.objects.filter(
        Q(ciudadano_1_id=ciudadano_principal_id)
        | Q(ciudadano_2_id=ciudadano_principal_id)
    ).values_list("ciudadano_1_id", "ciudadano_2_id")

    ciudadanos_asociados_ids = set()
    for ciudadano_1_id, ciudadano_2_id in ciudadanos_asociados:
        if ciudadano_1_id != ciudadano_principal_id:
            ciudadanos_asociados_ids.add(ciudadano_1_id)
        if ciudadano_2_id != ciudadano_principal_id:
            ciudadanos_asociados_ids.add(ciudadano_2_id)

    paginate_by = 10
    familiares = Ciudadano.objects.filter(
        ~Q(id=ciudadano_principal_id)
        & (Q(apellido__icontains=busqueda) | Q(documento__icontains=busqueda))
    ).exclude(id__in=ciudadanos_asociados_ids)

    if familiares.exists() and busqueda:
        paginator = Paginator(familiares, paginate_by)
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        data = [
            {
                "pk": familiar.pk,
                "nombre": familiar.nombre,
                "apellido": familiar.apellido,
                "documento": familiar.documento,
                "tipo_documento": (
                    familiar.tipo_documento.tipo if familiar.tipo_documento else None
                ),
                "fecha_nacimiento": familiar.fecha_nacimiento,
                "sexo": familiar.sexo.sexo if familiar.sexo else None,
                # Otros campos
            }
            for familiar in page_obj
        ]
        res = {
            "familiares": data,
            "page": page_number,
            "num_pages": paginator.num_pages,
            "has_next": page_obj.has_next(),
            "has_previous": page_obj.has_previous(),
        }
    else:
        res = ""

    return JsonResponse({"data": res})


class GrupoFamiliarList(ListView):
    model = GrupoFamiliar

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        context["familiares_fk1"] = GrupoFamiliar.objects.filter(ciudadano_1=pk)
        context["familiares_fk2"] = GrupoFamiliar.objects.filter(ciudadano_2=pk)
        context["count_familia"] = (
            context["familiares_fk1"].count() + context["familiares_fk1"].count()
        )
        context["nombre"] = Ciudadano.objects.filter(pk=pk).first()
        context["pk"] = pk
        return context


class CreateGrupoFamiliar(View):
    def get(self, request, **kwargs):
        ciudadano_1 = request.GET.get("ciudadano_1", None)
        ciudadano_2 = request.GET.get("ciudadano_2", None)
        vinculo = request.GET.get("vinculo", None)
        estado_relacion = request.GET.get("estado_relacion", None)
        conviven = request.GET.get("conviven", None)
        cuidador_principal = request.GET.get("cuidador_principal", None)
        obj = None
        vinculo_instance = VinculoFamiliar.objects.get(pk=vinculo)

        if not vinculo_instance:
            return messages.error(self.request, "Vinculo inválido.")
        try:
            estado_relacion_instance = EstadoRelacion.objects.get(pk=estado_relacion)
        except EstadoRelacion.DoesNotExist:
            return JsonResponse({"error": "EstadoRelacion no encontrado"}, status=400)

        obj = GrupoFamiliar.objects.create(
            ciudadano_1_id=ciudadano_1,
            ciudadano_2_id=ciudadano_2,
            vinculo=vinculo_instance,
            vinculo_inverso=vinculo_instance.inverso,
            estado_relacion=estado_relacion_instance,
            conviven=conviven,
            cuidador_principal=cuidador_principal,
        )

        familiar = {
            "id": obj.id,
            "ciudadano_1": obj.ciudadano_1.id,
            "ciudadano_2": obj.ciudadano_2.id,
            "vinculo": obj.vinculo.vinculo,
            "nombre": obj.ciudadano_2.nombre,
            "apellido": obj.ciudadano_2.apellido,
            "foto": obj.ciudadano_2.foto.url if obj.ciudadano_2.foto else None,
            "cuidador_principal": obj.cuidador_principal,
        }
        data = {
            "tipo_mensaje": "success",
            "mensaje": "Vínculo familiar agregado correctamente.",
        }

        return JsonResponse({"familiar": familiar, "data": data})


class DeleteGrupoFamiliar(View):
    def get(self, request):
        pk = request.GET.get("id", None)
        try:
            familiar = get_object_or_404(GrupoFamiliar, pk=pk)
            familiar.delete()
            data = {
                "deleted": True,
                "tipo_mensaje": "success",
                "mensaje": "Vínculo familiar eliminado correctamente.",
            }
        except Exception as e:
            data = {
                "deleted": False,
                "tipo_mensaje": "error",
                "mensaje": f"No fue posible eliminar el archivo. Error: {e}",
            }

        return JsonResponse(data)


class DerivacionBuscar(TemplateView):
    template_name = "ciudadanos/derivacion_buscar.html"

    def get(self, request, *args, **kwargs):  # pylint: disable=too-many-locals
        context = self.get_context_data(**kwargs)
        ciudadanos = cache.get("ciudadanos")
        derivaciones = cache.get("derivaciones")
        con_derivaciones = cache.get("con_derivaciones")
        sin_derivaciones = cache.get("sin_derivaciones")

        if not ciudadanos:
            ciudadanos = Ciudadano.objects.all()
            cache.set("ciudadanos", ciudadanos, 60)
        if not derivaciones:
            derivaciones = Derivacion.objects.all()
            cache.set("derivaciones", derivaciones, 60)
        if not con_derivaciones:
            con_derivaciones = Derivacion.objects.none()
            cache.set("con_derivaciones", con_derivaciones, 60)
        if not sin_derivaciones:
            sin_derivaciones = Ciudadano.objects.none()
            cache.set("sin_derivaciones", sin_derivaciones, 60)

        barrios = ciudadanos.values_list("barrio")
        circuitos = Circuito.objects.all().values_list("id", "circuito")
        localidad = Nacionalidad.objects.all().values_list("id", "nacionalidad")
        mostrar_resultados = False
        mostrar_btn_resetear = False
        query = self.request.GET.get("busqueda")
        if query:
            derivaciones_filtrado = (
                derivaciones.filter(
                    Q(ciudadano__apellido__icontains=query)
                    | Q(ciudadano__documento__icontains=query)
                )
                .values("ciudadano")
                .distinct()
            )
            ciudadanos_filtrado = ciudadanos.filter(
                Q(apellido__icontains=query) | Q(documento__icontains=query)
            ).distinct()

            if derivaciones_filtrado:
                sin_derivaciones = ciudadanos_filtrado.exclude(
                    id__in=derivaciones_filtrado
                )
                con_derivaciones = ciudadanos_filtrado.filter(
                    id__in=derivaciones_filtrado
                )

            else:
                sin_derivaciones = ciudadanos_filtrado

            if not derivaciones_filtrado and not ciudadanos_filtrado:
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


class DerivacionListView(ListView):
    model = Derivacion
    paginate_by = 25

    def get_context_data(self, **kwargs):
        context = super(DerivacionListView, self).get_context_data(**kwargs)

        model = cache.get("model")
        if not model:
            model = Derivacion.objects.all()
            cache.set("model", model, 60)

        context["pendientes"] = model.filter(
            estado=EstadoDerivacion.objects.filter(estado="Pendiente").first()
        )
        context["aceptadas"] = model.filter(
            estado=EstadoDerivacion.objects.filter(estado="Aceptada").first()
        )
        context["analisis"] = model.filter(
            estado=EstadoDerivacion.objects.filter(estado="En análisis").first()
        )
        context["asesoradas"] = model.filter(
            estado=EstadoDerivacion.objects.filter(estado="Asesoramiento").first()
        )
        context["enviadas"] = model.filter(usuario=self.request.user)
        return context

    # Funcion de busqueda

    def get_queryset(self):
        model = cache.get("model")
        if model is None:
            model = Derivacion.objects.all()
            cache.set("model", model, 60)

        query = self.request.GET.get("busqueda")

        if query:
            object_list = model.filter(
                Q(ciudadano__apellido__icontains=query)
                | Q(ciudadano__documento__icontains=query)
            ).distinct()

        else:
            object_list = model.all()

        return object_list.order_by("-estado")


class DerivacionCreateView(CreateView):
    model = Derivacion
    form_class = DerivacionForm
    success_message = "Derivación registrada con éxito"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        pk = self.kwargs.get("pk")

        if pk:
            # excluyo los programas que ya tienen derivaciones en curso para este ciudadano (solo dejo fuera las 'asesoradas')

            programas = Programa.objects.all().exclude(
                id__in=Derivacion.objects.filter(ciudadano=pk)
                .exclude(
                    estado__in=[
                        EstadoDerivacion.objects.filter(estado="Rechazada").first(),
                        EstadoDerivacion.objects.filter(estado="Finalizada").first(),
                    ]
                )
                .values_list("programa", flat=True)
            )

            form.fields["programa"].queryset = programas
            form.fields["ciudadano"].initial = pk
            form.fields["usuario"].initial = self.request.user
        return form

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        context["ciudadano"] = Ciudadano.objects.filter(id=pk).first()
        return context


class DerivacionUpdateView(UpdateView):
    model = Derivacion
    form_class = DerivacionForm
    success_message = "Derivación editada con éxito"

    def get_initial(self):
        initial = super().get_initial()
        initial["usuario"] = self.request.user
        return initial

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        ciudadano = Derivacion.objects.filter(id=pk).first()
        context["ciudadano"] = Ciudadano.objects.filter(
            id=ciudadano.ciudadano.id
        ).first()
        return context


class DerivacionHistorial(ListView):
    model = Derivacion
    template_name = "ciudadanos/derivacion_historial.html"

    def get_context_data(self, **kwargs):
        context = super(DerivacionHistorial, self).get_context_data(**kwargs)
        pk = self.kwargs.get("pk")

        ciudadano = Ciudadano.objects.filter(id=pk).first()
        historial = Derivacion.objects.filter(ciudadano_id=pk)

        context["historial"] = historial
        context["ciudadano"] = ciudadano
        context["pendientes"] = historial.filter(
            estado=EstadoDerivacion.objects.filter(estado="Pendiente").first()
        ).count()
        context["admitidas"] = historial.filter(
            estado=EstadoDerivacion.objects.filter(estado="Aceptada").first()
        ).count()
        context["rechazadas"] = historial.filter(
            estado=EstadoDerivacion.objects.filter(estado="Rechazada").first()
        ).count()
        return context


class DerivacionDeleteView(DeleteView):
    model = Derivacion

    def form_valid(self, form):
        if (
            self.object.estado
            != EstadoDerivacion.objects.filter(estado="Pendiente").first()
        ):
            messages.error(
                self.request,
                "No es posible eliminar una solicitud en estado " + self.object.estado,
            )

            return redirect("ciudadanosderivaciones_ver", pk=int(self.object.id))

        if self.request.user != self.object.usuario:
            messages.error(
                self.request,
                "Solo el usuario que generó esta derivación puede eliminarla.",
            )

            return redirect("ciudadanosderivaciones_ver", pk=int(self.object.id))

        else:
            ciudadano = Derivacion.objects.filter(pk=self.object.id).first()
            self.object.delete()

            return redirect(
                "ciudadanosderivaciones_historial", pk=ciudadano.ciudadano_id
            )


class DerivacionDetailView(DetailView):
    model = Derivacion


class AlertaListView(ListView):
    model = HistorialAlerta
    template_name = "ciudadanos/alerta_list.html"

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        context["ciudadano_alertas"] = HistorialAlerta.objects.filter(ciudadano=pk)
        context["ciudadano"] = (
            Ciudadano.objects.filter(id=pk).values("apellido", "nombre", "id").first()
        )
        return context


class AlertaCreateView(SuccessMessageMixin, CreateView):
    model = Alerta
    form_class = AlertaForm
    success_message = "Alerta asignada correctamente."

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        context = super().get_context_data(**kwargs)

        alertas = Alerta.objects.filter(ciudadano=pk)

        ciudadano = Ciudadano.objects.values(
            "pk", "dimensionfamilia__id", "nombre", "apellido"
        ).get(pk=pk)

        context["alertas"] = alertas
        context["ciudadano"] = ciudadano
        return context

    def get_success_url(self):
        # Redirige a la misma página después de agregar la alerta
        return self.request.path


class DeleteAlerta(View):

    def get(self, request):
        try:
            pk = request.GET.get("id", None)
            ciudadano_alerta = get_object_or_404(Alerta, pk=pk)
            ciudadano = ciudadano_alerta.ciudadano
            alerta = ciudadano_alerta.alerta
            ciudadano_alerta.delete()

            # Filtrar el registro activo actualmente (sin fecha_fin)
            registro_historial = HistorialAlerta.objects.filter(
                Q(alerta=alerta) & Q(ciudadano=ciudadano) & Q(fecha_fin__isnull=True)
            ).first()

            if registro_historial:
                registro_historial.eliminada_por = request.user.usuarios
                registro_historial.fecha_fin = date.today()
                registro_historial.save()

                data = {
                    "deleted": True,
                    "tipo_mensaje": "success",
                    "mensaje": "Alerta eliminada correctamente.",
                }
            else:
                data = {
                    "deleted": True,
                    "tipo_mensaje": "warning",
                    "mensaje": "Alerta eliminada, con errores en el historial.",
                }
        except Exception as e:
            data = {
                "deleted": False,
                "tipo_mensaje": "error",
                "mensaje": f"No fue posible eliminar el alerta. Error: {e}",
            }

        return JsonResponse(data)


class CategoriasSelectView(View):
    def get(self, request, *args, **kwargs):
        alerta_id = request.GET.get("alerta_id")
        if alerta_id:
            categorias = CategoriaAlerta.objects.filter(alertas__id=alerta_id)
        else:
            categorias = CategoriaAlerta.objects.all()

        data = [
            {"id": categoria.id, "text": categoria.nombre} for categoria in categorias
        ]
        return JsonResponse(data, safe=False)


class AlertaSelectView(View):
    def get(self, request, *args, **kwargs):
        categoria_id = request.GET.get("categoria_id")
        if categoria_id:
            alertas = Alerta.objects.filter(categoria_id=categoria_id)
        else:
            alertas = Alerta.objects.all()

        data = [{"id": alerta.id, "text": alerta.nombre} for alerta in alertas]
        return JsonResponse(data, safe=False)


class DimensionesUpdateView(SuccessMessageMixin, UpdateView):
    # FIXME: Crear updateView por cada formulario
    template_name = "ciudadanos/dimension_form.html"
    model = DimensionFamilia
    form_class = DimensionFamiliaForm
    form_vivienda = DimensionViviendaForm
    form_salud = DimensionSaludForm
    form_educacion = DimensionEducacionForm
    form_economia = DimensionEconomiaForm
    form_trabajo = DimensionTrabajoForm
    success_message = "Editado correctamente"

    def get_object(self, queryset=None):
        pk = self.kwargs["pk"]
        ciudadano = Ciudadano.objects.only("id").get(id=pk)
        return DimensionFamilia.objects.get(ciudadano=ciudadano.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        pk = self.kwargs["pk"]
        ciudadano = (
            Ciudadano.objects.select_related(
                "dimensionvivienda",
                "dimensionsalud",
                "dimensioneducacion",
                "dimensioneconomia",
                "dimensiontrabajo",
            )
            .only(
                "id",
                "apellido",
                "nombre",
                "dimensionvivienda__ciudadano",
                "dimensionvivienda__obs_vivienda",
                "dimensionsalud__ciudadano",
                "dimensionsalud__obs_salud",
                "dimensionsalud__hay_obra_social",
                "dimensionsalud__hay_enfermedad",
                "dimensionsalud__hay_discapacidad",
                "dimensionsalud__hay_cud",
                "dimensioneducacion__ciudadano",
                "dimensioneducacion__observaciones",
                "dimensioneducacion__area_curso",
                "dimensioneducacion__area_oficio",
                "dimensioneconomia__ciudadano",
                "dimensioneconomia__obs_economia",
                "dimensioneconomia__planes",
                "dimensiontrabajo__ciudadano",
                "dimensiontrabajo__obs_trabajo",
            )
            .get(id=pk)
        )

        # TODO: Modificar logica para no utilizar los siguientes "None' y crear la dimension segun haga falta
        context.update(
            {
                "ciudadano": ciudadano,
                "form_vivienda": self.form_vivienda(
                    instance=getattr(ciudadano, "dimensionvivienda", None)
                ),
                "form_salud": self.form_salud(
                    instance=getattr(ciudadano, "dimensionsalud", None)
                ),
                "form_educacion": self.form_educacion(
                    instance=getattr(ciudadano, "dimensioneducacion", None)
                ),
                "form_economia": self.form_economia(
                    instance=getattr(ciudadano, "dimensioneconomia", None)
                ),
                "form_trabajo": self.form_trabajo(
                    instance=getattr(ciudadano, "dimensiontrabajo", None)
                ),
            }
        )

        return context

    def form_valid(
        self, form
    ):  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        # TODO: Esto sera refactorizado
        self.object = form.save(commit=False)

        pk = self.kwargs["pk"]

        ciudadano_dim_vivienda = DimensionVivienda.objects.get(ciudadano__id=pk)
        ciudadano_dim_salud = DimensionSalud.objects.get(ciudadano__id=pk)
        ciudadano_dim_educacion = DimensionEducacion.objects.get(ciudadano__id=pk)
        ciudadano_dim_economia = DimensionEconomia.objects.get(ciudadano__id=pk)
        ciudadano_dim_trabajo = DimensionTrabajo.objects.get(ciudadano__id=pk)
        form_multiple = self.form_class(self.request.POST).data.copy()

        # cambio el valor 'on' y 'off' por True/False
        for clave, valor in form_multiple.items():
            if valor == "on":
                form_multiple[clave] = True

            elif valor == "off":
                form_multiple[clave] = False

        # dimension vivienda

        fields_mapping_vivienda = {
            "tipo": TipoVivienda,
            "material": TipoConstruccionVivienda,
            "pisos": TipoPisosVivienda,
            "posesion": TipoPosesionVivienda,
            "cant_ambientes": CantidadAmbientes,
            "cant_convivientes": "cant_convivientes",
            "cant_menores": "cant_menores",
            "cant_camas": "cant_camas",
            "cant_hogares": "cant_hogares",
            "hay_agua_caliente": "hay_agua_caliente",
            "hay_desmoronamiento": "hay_desmoronamiento",
            "hay_banio": Inodoro,
            "PoseenCelular": "PoseenCelular",
            "PoseenPC": "PoseenPC",
            "Poseeninternet": "Poseeninternet",
            "ubicacion_vivienda": UbicacionVivienda,
            "Condicion": Condicion,
            "CantidadAmbientes": "CantidadAmbientes",
            "gas": Gas,
            "techos": TipoTechoVivienda,
            "agua": Agua,
            "desague": Desague,
            "obs_vivienda": "obs_vivienda",
        }

        for field, model in fields_mapping_vivienda.items():
            value = form_multiple.get(field)

            if value:
                # Verifica si el valor del campo es una instancia de un modelo o una ForeignKey
                if isinstance(model, type) and issubclass(model, models.Model):
                    instance = model.objects.get(pk=value)
                    setattr(ciudadano_dim_vivienda, field, instance)
                else:
                    setattr(ciudadano_dim_vivienda, field, value)
            else:
                setattr(ciudadano_dim_vivienda, field, None)

        ciudadano_dim_vivienda.save()

        # dimension salud

        fields_mapping_salud = {
            "lugares_atencion": CentrosSalud,
            "frecuencia_controles_medicos": Frecuencia,
            "hay_obra_social": "hay_obra_social",
            "hay_enfermedad": "hay_enfermedad",
            "hay_discapacidad": "hay_discapacidad",
            "hay_cud": "hay_cud",
            "obs_salud": "obs_salud",
        }

        for field in fields_mapping_salud:
            value = form_multiple.get(field)

            if value:
                # Verifica si el valor del campo es una instancia de un modelo o una ForeignKey
                if isinstance(fields_mapping_salud.get(field), type) and issubclass(
                    fields_mapping_salud.get(field), models.Model
                ):
                    instance = fields_mapping_salud.get(field).objects.get(pk=value)
                    setattr(ciudadano_dim_salud, field, instance)
                else:
                    setattr(ciudadano_dim_salud, field, value)

            else:
                setattr(ciudadano_dim_salud, field, None)

        ciudadano_dim_salud.save()

        # dimension educacion

        fields_mapping_educacion = {
            "max_nivel": NivelEducativo,
            "estado_nivel": EstadoNivelEducativo,
            "asiste_escuela": AsisteEscuela,
            "institucion": InstitucionEducativas,
            "gestion": TipoGestion,
            "ciclo": NivelEducativo,
            "grado": Grado,
            "turno": Turno,
            "observaciones": "observaciones",
            "provinciaInstitucion": Provincia,
            "localidadInstitucion": Localidad,
            "municipioInstitucion": Municipio,
            "barrio_institucion": "barrio_institucion",
            "calle_institucion": "calle_institucion",
            "numero_institucion": "numero_institucion",
            "interes_estudio": "interes_estudio",
            "interes_curso": "interes_curso",
            "nivel_incompleto": MotivoNivelIncompleto,
            "sin_educacion_formal": MotivoNivelIncompleto,
            "realizando_curso": "realizando_curso",
            "area_curso": AreaCurso,
            "interes_capacitacion_laboral": "interes_capacitacion_laboral",
            "area_oficio": AreaCurso,
            "oficio": "oficio",
        }

        for field, model in fields_mapping_educacion.items():
            value = form_multiple.get(field)

            if value:
                # Verifica si el valor del campo es una instancia de un modelo o una ForeignKey
                if isinstance(model, type) and issubclass(model, models.Model):
                    instance = model.objects.get(pk=value)
                    setattr(ciudadano_dim_educacion, field, instance)
                else:
                    setattr(ciudadano_dim_educacion, field, value)
            else:
                setattr(ciudadano_dim_educacion, field, None)

        ciudadano_dim_educacion.save()

        # dimension economia

        fields_mapping_economia = {
            "ingresos": "ingresos",
            "recibe_plan": "recibe_plan",
            "planes": "planes",
            "cant_aportantes": "cant_aportantes",
            "obs_economia": "obs_economia",
        }

        for field in fields_mapping_economia:
            value = form_multiple.get(field)

            if field == "planes":
                lista = form_multiple.getlist("planes")

                ciudadano_dim_economia.planes.set(lista)

            else:
                if value:
                    setattr(
                        ciudadano_dim_economia,
                        fields_mapping_economia.get(field, field),
                        value,
                    )

                else:
                    setattr(ciudadano_dim_economia, field, None)

        ciudadano_dim_economia.save()

        # dimension trabajo

        fields_mapping_trabajo = {
            "tiene_trabajo": "tiene_trabajo",
            "modo_contratacion": ModoContratacion,
            "ocupacion": "ocupacion",
            "conviviente_trabaja": "conviviente_trabaja",
            "obs_trabajo": "obs_trabajo",
            "horasSemanales": "horasSemanales",
            "actividadRealizadaComo": ActividadRealizada,
            "duracionTrabajo": DuracionTrabajo,
            "aportesJubilacion": AportesJubilacion,
            "Tiempobusqueda_laboral": TiempoBusquedaLaboral,
            "busqueda_laboral": "busqueda_laboral",
            "nobusqueda_laboral": NobusquedaLaboral,
        }

        for field, model in fields_mapping_trabajo.items():
            value = form_multiple.get(field)

            if value:
                if isinstance(model, type) and issubclass(model, models.Model):
                    instance = model.objects.get(pk=value)
                    setattr(ciudadano_dim_trabajo, field, instance)
                else:
                    setattr(ciudadano_dim_trabajo, field, value)
            else:
                setattr(ciudadano_dim_trabajo, field, None)

        ciudadano_dim_trabajo.save()

        if "form_step1" in self.request.POST:
            self.object.save()

            return redirect("ciudadanos_editar", pk=pk)

        if "form_step2" in self.request.POST:
            self.object.save()

            return redirect("ciudadanos_ver", pk=pk)

        if "form_step3" in self.request.POST:
            self.object.save()

            return redirect("grupofamiliar_crear", pk=pk)

        self.object = form.save()

        return super().form_valid(form)


class DimensionesDetailView(DetailView):
    model = Ciudadano
    template_name = "ciudadanos/dimensiones_detail.html"


class ArchivosListView(ListView):
    model = Archivo
    template_name = "ciudadanos/archivos_list.html"

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        context["ciudadano_archivos"] = Archivo.objects.filter(ciudadano=pk)
        context["ciudadano"] = Ciudadano.objects.filter(id=pk).first()
        return context


class ArchivosCreateView(SuccessMessageMixin, CreateView):
    model = Archivo
    form_class = ArchivoForm
    success_message = "Archivo actualizado correctamente."

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        archivos = Archivo.objects.filter(ciudadano=pk)
        imagenes = archivos.filter(tipo="Imagen")
        documentos = archivos.filter(tipo="Documento")
        ciudadano = Ciudadano.objects.filter(pk=pk).first()
        context["imagenes"] = imagenes
        context["documentos"] = documentos
        context["ciudadano"] = ciudadano
        return context


class CreateArchivo(TemplateView):
    def post(self, request):
        pk = request.POST.get("pk")
        ciudadano = Ciudadano.objects.get(id=pk)
        response_data_list = []  # Lista para almacenar las respuestas de los archivos

        files = request.FILES.getlist(
            "file"
        )  # Acceder a los archivos enviados desde Dropzone

        for f in files:
            if f:
                file_extension = f.name.split(".")[-1].lower()
                if file_extension in ["jpg", "jpeg", "png", "gif", "bmp"]:
                    tipo = "Imagen"
                else:
                    tipo = "Documento"

                ciudadano_archivo = Archivo.objects.create(
                    ciudadano=ciudadano, archivo=f, tipo=tipo
                )

                response_data = {
                    "id": ciudadano_archivo.id,
                    "tipo": ciudadano_archivo.tipo,
                    "archivo_url": ciudadano_archivo.archivo.url,
                }

                response_data_list.append(
                    response_data
                )  # Agregar la respuesta actual a la lista

        return JsonResponse(
            response_data_list, safe=False
        )  # Devolver la lista completa de respuestas como JSON


class DeleteArchivo(View):

    def get(self, request):
        try:
            pk = request.GET.get("id", None)
            ciudadano_archivo = get_object_or_404(Archivo, pk=pk)
            ciudadano_archivo.delete()

            data = {
                "deleted": True,
                "tipo_mensaje": "success",
                "mensaje": "Archivo eliminado correctamente.",
            }
        except Exception as e:
            data = {
                "deleted": False,
                "tipo_mensaje": "error",
                "mensaje": f"No fue posible eliminar el archivo. Error: {e}",
            }

        return JsonResponse(data)


class ProgramaIntervencionesView(TemplateView):
    template_name = "intervencion/programas_intervencion.html"
    model = Ciudadano

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        ciudadano = Ciudadano.objects.filter(pk=self.kwargs["pk"]).first()

        context["ciudadano"] = ciudadano

        return context


class AccionesSocialesView(TemplateView):
    template_name = "acciones_sociales/acciones_sociales.html"
    model = Ciudadano

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ciudadano_id = self.kwargs["pk"]

        ciudadano = Ciudadano.objects.only(
            "apellido",
            "nombre",
            "id",
            "tipo_documento",
            "documento",
            "fecha_nacimiento",
            "sexo",
        ).get(pk=ciudadano_id)

        context["ciudadano"] = ciudadano

        return context


class IntervencionesSaludView(TemplateView):
    template_name = "intervencion/intervenciones_salud.html"
    model = Ciudadano

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        ciudadano = Ciudadano.objects.filter(pk=self.kwargs["pk"]).first()

        context["ciudadano"] = ciudadano

        return context


class IndicesView(TemplateView):
    template_name = "indices/indices.html"
    model = Ciudadano

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        ciudadano = Ciudadano.objects.filter(pk=self.kwargs["pk"]).first()

        context["ciudadano"] = ciudadano

        return context


class IndicesDetalleView(TemplateView):
    template_name = "indices/indices_detalle.html"
    model = Ciudadano

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        ciudadano = Ciudadano.objects.filter(pk=self.kwargs["pk"]).first()

        context["ciudadano"] = ciudadano

        return context


class CiudadanosGrupoHogarCreateView(CreateView):
    model = GrupoHogar
    form_class = GrupoHogarForm
    paginate_by = 8

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        ciudadano_principal = Ciudadano.objects.filter(pk=pk).first()

        context = super().get_context_data(**kwargs)

        hogares = GrupoHogar.objects.filter(
            Q(ciudadano_1Hogar=pk) | Q(ciudadano_2Hogar=pk)
        ).values(
            "id",
            "ciudadano_1Hogar__nombre",
            "ciudadano_2Hogar__nombre",
            "ciudadano_1Hogar__apellido",
            "ciudadano_2Hogar__apellido",
            "ciudadano_1Hogar__foto",
            "ciudadano_2Hogar__foto",
            "ciudadano_1Hogar__id",
            "ciudadano_2Hogar__id",
        )

        # Paginacion

        paginator = Paginator(hogares, self.paginate_by)
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context["hogar_1"] = [
            familiar
            for familiar in page_obj
            if familiar["ciudadano_1Hogar__id"] == int(pk)
        ]
        context["hogar_2"] = [
            familiar
            for familiar in page_obj
            if familiar["ciudadano_2Hogar__id"] == int(pk)
        ]
        print(context["hogar_1"])

        context["hogares"] = page_obj
        context["count_hogar"] = hogares.count()
        context["ciudadano_principal"] = ciudadano_principal
        context["pk"] = pk

        return context

    def form_valid(self, form):
        pk = self.kwargs["pk"]
        estado_relacion = form.cleaned_data["estado_relacion"]

        # Crea el objeto Ciudadano
        try:
            nuevo_ciudadano = form.save()
            DimensionFamilia.objects.create(ciudadano=nuevo_ciudadano)
            DimensionVivienda.objects.create(ciudadano=nuevo_ciudadano)
            DimensionSalud.objects.create(ciudadano=nuevo_ciudadano)
            DimensionEconomia.objects.create(ciudadano=nuevo_ciudadano)
            DimensionEducacion.objects.create(ciudadano=nuevo_ciudadano)
            DimensionTrabajo.objects.create(ciudadano=nuevo_ciudadano)
            GrupoHogar.objects.create(ciudadano=nuevo_ciudadano)
        except Exception as e:
            return messages.error(
                self.request,
                f"Verifique que no exista un ciudadano con ese DNI y NÚMERO. Error: {e}",
            )

        # crea la relacion de grupo familiar
        estado_relacion_instance = EstadoRelacion.objects.get(pk=estado_relacion)

        ciudadano_principal = Ciudadano.objects.get(id=pk)
        try:
            GrupoFamiliar.objects.create(
                ciudadano_1=ciudadano_principal,
                ciudadano_2=nuevo_ciudadano,
                #  vinculo=vinculo_data["vinculo"],
                # vinculo_inverso=vinculo_data["vinculo_inverso"],
                estado_relacion=estado_relacion_instance,
            )
        except Exception as e:
            return messages.error(
                self.request,
                f"Verifique que no exista un ciudadano con ese DNI y NÚMERO. {e}",
            )

        messages.success(self.request, "Familair agregado correctamente.")
        # Redireccionar a la misma página después de realizar la acción con éxito
        return HttpResponseRedirect(self.request.path_info)


def busqueda_hogar(request):

    res = None
    busqueda = request.POST.get("busqueda", "")
    ciudadano_principal_id = request.POST.get("id")
    page_number = request.POST.get("page", 1)

    ciudadanos_asociados = GrupoHogar.objects.filter(
        Q(ciudadano_1Hogar_id=ciudadano_principal_id)
        | Q(ciudadano_2Hogar_id=ciudadano_principal_id)
    ).values_list("ciudadano_1Hogar_id", "ciudadano_2Hogar_id")

    ciudadanos_asociados_ids = set()
    for ciudadano_1, ciudadano_2 in ciudadanos_asociados:
        if ciudadano_1 != ciudadano_principal_id:
            ciudadanos_asociados_ids.add(ciudadano_1)
        if ciudadano_2 != ciudadano_principal_id:
            ciudadanos_asociados_ids.add(ciudadano_2)

    paginate_by = 10
    hogares = Ciudadano.objects.filter(
        ~Q(id=ciudadano_principal_id)
        & (Q(apellido__icontains=busqueda) | Q(documento__icontains=busqueda))
    ).exclude(id__in=ciudadanos_asociados_ids)

    if hogares.exists() and busqueda:
        paginator = Paginator(hogares, paginate_by)
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        data = [
            {
                "pk": hogar.pk,
                "nombre": hogar.nombre,
                "apellido": hogar.apellido,
                "documento": hogar.documento,
                "tipo_documento": (
                    hogar.tipo_documento.tipo if hogar.tipo_documento else None
                ),
                "fecha_nacimiento": hogar.fecha_nacimiento,
                "sexo": hogar.sexo.sexo if hogar.sexo else None,
            }
            for hogar in page_obj
        ]
        res = {
            "hogares": data,
            "page": page_number,
            "num_pages": paginator.num_pages,
            "has_next": page_obj.has_next(),
            "has_previous": page_obj.has_previous(),
        }
    else:
        res = ""

    return JsonResponse({"data": res})


class GrupoHogarList(ListView):
    model = GrupoFamiliar

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        context = super().get_context_data(**kwargs)

        # FIXME: Esta query optimizada de "familiares" no se termino de implementar
        familiares = GrupoFamiliar.objects.filter(
            Q(ciudadano_1=pk) | Q(ciudadano_2=pk)
        ).values(
            "ciudadano2__id",
            "ciudadano1__id",
            "ciudadano_2__nombre",
            "ciudadano_2__apellido",
            "ciudadano_2__calle",
            "ciudadano_2__telefono",
            "estado_relacion",
            "conviven",
            "cuidado_principal",
            "ciudadano_2__foto",
            "ciudadano_1__nombre",
            "ciudadano_1__apellido",
            "ciudadano_1__calle",
            "ciudadano_1__telefono",
            "estado_relacion",
            "conviven",
            "cuidado_principal",
            "ciudadano_1__foto",
            "vinculo",
        )
        context["familiares_fk1"] = [
            familiar
            for familiar in familiares
            if familiar["ciudadano_1__id"] == int(pk)
        ]
        context["familiares_fk2"] = [
            familiar
            for familiar in familiares
            if familiar["ciudadano_1__id"] == int(pk)
        ]
        context["count_familia"] = (
            context["familiares_fk1"].count() + context["familiares_fk1"].count()
        )
        context["nombre"] = Ciudadano.objects.filter(pk=pk).values("nombre").first()
        context["pk"] = pk
        return context


class CreateGrupoHogar(View):
    def get(self, request, **kwargs):
        ciudadano_1 = request.GET.get("ciudadano_1", None)
        ciudadano_2 = request.GET.get("ciudadano_2", None)
        estado_relacion = request.GET.get("estado_relacion", None)

        obj = None

        try:
            estado_relacion_instance = EstadoRelacion.objects.get(pk=estado_relacion)
        except EstadoRelacion.DoesNotExist:
            return JsonResponse({"error": "EstadoRelacion no encontrado"}, status=400)

        obj = GrupoHogar.objects.create(
            ciudadano_1Hogar_id=ciudadano_1,
            ciudadano_2Hogar_id=ciudadano_2,
            estado_relacion=estado_relacion_instance,
        )

        familiar = {
            "id": obj.id,
            "ciudadano_1": obj.ciudadano_1Hogar.id,
            "ciudadano_2": obj.ciudadano_2Hogar.id,
            "estado_relacion": obj.estado_relacion.estado,
            "nombre": obj.ciudadano_2Hogar.nombre,
            "apellido": obj.ciudadano_2Hogar.apellido,
            "foto": (
                obj.ciudadano_2Hogar.foto.url if obj.ciudadano_2Hogar.foto else None
            ),
        }
        data = {
            "tipo_mensaje": "success",
            "mensaje": "Vínculo hogar agregado correctamente.",
        }

        return JsonResponse({"hogar": familiar, "data": data})


class DeleteGrupoHogar(View):
    def get(self, request):
        pk = request.GET.get("id", None)
        try:
            familiar = get_object_or_404(GrupoHogar, pk=pk)
            familiar.delete()
            data = {
                "deleted": True,
                "tipo_mensaje": "success",
                "mensaje": "Vínculo del hogar eliminado correctamente.",
            }
        except Exception as e:
            data = {
                "deleted": False,
                "tipo_mensaje": "error",
                "mensaje": f"No fue posible eliminar el vinculo. Error: {e}",
            }

        return JsonResponse(data)


class IntervencionDetail(TemplateView):
    template_name = "intervencion/intervencion_detail.html"
    model = Intervencion

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ciudadano = Ciudadano.objects.values(
            "id", "nombre", "apellido", "documento", "fecha_nacimiento", "sexo"
        ).get(pk=self.kwargs["pk"])
        intervenciones = Intervencion.objects.filter(ciudadano=self.kwargs["pk"])
        cantidad_intervenciones = Intervencion.objects.filter(
            ciudadano=self.kwargs["pk"]
        ).count()
        context["intervenciones"] = intervenciones
        context["object"] = ciudadano
        context["cantidad_intervenciones"] = cantidad_intervenciones

        return context


class IntervencionCreateView(CreateView):
    model = Intervencion
    template_name = "intervencion/intervencion_form.html"
    form_class = IntervencionForm

    def form_valid(self, form):
        pk = self.kwargs["pk"]
        form.save()
        return redirect("ciudadano_intervencion_ver", pk=pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ciudadano = Ciudadano.objects.values(
            "id", "nombre", "apellido", "documento", "fecha_nacimiento", "sexo"
        ).get(pk=self.kwargs["pk"])

        context["form"] = self.get_form()
        context["object"] = ciudadano

        return context


class IntervencionDeleteView(DeleteView):
    model = Intervencion
    template_name = "intervencion/intervencion_confirm_delete.html"

    def form_valid(self, form):
        self.object.delete()
        return redirect("ciudadano_intervencion_ver", pk=self.kwargs["pk2"])


class IntervencionUpdateView(UpdateView):
    model = Intervencion
    form_class = IntervencionForm
    template_name = "intervencion/intervencion_form.html"

    def form_valid(self, form):
        pk = self.kwargs["pk2"]
        form.save()
        return redirect("ciudadano_intervencion_ver", pk=pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ciudadano = Ciudadano.objects.values(
            "id", "nombre", "apellido", "documento", "fecha_nacimiento", "sexo"
        ).get(pk=self.kwargs["pk2"])
        context["form"] = self.get_form()
        context["object"] = ciudadano
        return context


class LlamadoDetail(TemplateView):
    template_name = "llamado/llamado_detail.html"
    model = Llamado

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ciudadano = Ciudadano.objects.values(
            "id", "nombre", "apellido", "documento", "fecha_nacimiento", "sexo"
        ).get(pk=self.kwargs["pk"])
        llamados = Llamado.objects.filter(ciudadano=self.kwargs["pk"])
        cantidad_llamados = Llamado.objects.filter(ciudadano=self.kwargs["pk"]).count()
        context["object"] = ciudadano
        context["llamados"] = llamados
        context["cantidad_llamados"] = cantidad_llamados
        return context


class LlamadoDeleteView(DeleteView):
    model = Llamado

    def form_valid(self, form):
        self.object.delete()
        return redirect("llamados_ver", pk=self.kwargs["pk2"])


class LlamadoCreateView(CreateView):
    model = Llamado
    template_name = "llamado/llamado_form.html"
    form_class = LlamadoForm

    def form_valid(self, form):
        pk = self.kwargs["pk"]
        form.save()
        return redirect("llamados_ver", pk=pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ciudadano = Ciudadano.objects.values(
            "id", "nombre", "apellido", "documento", "fecha_nacimiento", "sexo"
        ).get(pk=self.kwargs["pk"])
        context["form"] = self.get_form()
        context["object"] = ciudadano
        return context


class LlamadoUpdateView(UpdateView):
    model = Llamado
    form_class = LlamadoForm
    template_name = "llamado/llamado_form.html"

    def form_valid(self, form):
        pk = self.kwargs["pk2"]
        form.save()
        return redirect("llamados_ver", pk=pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ciudadano = Ciudadano.objects.values(
            "id", "nombre", "apellido", "documento", "fecha_nacimiento", "sexo"
        ).get(pk=self.kwargs["pk2"])
        context["form"] = self.get_form()
        context["object"] = ciudadano
        return context


class SubEstadosIntervencionesAJax(View):
    def get(self, request):
        request_id = request.GET.get("id", None)
        if request_id:
            sub_estados = SubIntervencion.objects.filter(subintervencion=request_id)
        else:
            sub_estados = SubIntervencion.objects.all()
        data = [
            {"id": sub_estado.id, "text": sub_estado.nombre}
            for sub_estado in sub_estados
        ]
        return JsonResponse(data, safe=False)


class SubEstadosLlamadosAjax(View):
    def get(self, request):
        request_id = request.GET.get("id", None)
        if request_id:
            sub_estados = SubtipoLlamado.objects.filter(tipo_llamado=request_id)
        else:
            sub_estados = SubtipoLlamado.objects.all()
        data = [
            {"id": sub_estado.id, "text": sub_estado.nombre}
            for sub_estado in sub_estados
        ]
        return JsonResponse(data, safe=False)


class TipoEstadosLlamadosAjax(View):
    def get(self, request):
        request_id = request.GET.get("id", None)
        if request_id:
            sub_estados = TipoLlamado.objects.filter(programas_llamados=request_id)
        else:
            sub_estados = TipoLlamado.objects.all()
        data = [
            {"id": sub_estado.id, "text": sub_estado.nombre}
            for sub_estado in sub_estados
        ]
        return JsonResponse(data, safe=False)
