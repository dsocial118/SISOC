# pylint: disable=too-many-lines
import calendar
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
from django.db.models import (
    Case,
    Q,
    When,
    CharField,
    TextField,
    Prefetch,
    Count,
)
from django.db.models.functions import Cast
from django.http import HttpResponseRedirect, JsonResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django.conf import settings
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

from core.models import (
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
            cache.set("organismos", organismos, settings.DEFAULT_CACHE_TIMEOUT)

        programas = cache.get("programas")
        if not programas:
            programas = Programa.objects.all().values("id", "nombre")
            cache.set("programas", programas, settings.DEFAULT_CACHE_TIMEOUT)

        estados = cache.get("estados_derivacion")
        if not estados:
            estados = EstadoDerivacion.objects.all().values("id", "estado")
            cache.set("estados_derivacion", estados, settings.DEFAULT_CACHE_TIMEOUT)

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
            filters &= Q(ciudadano__nombre__icontains=nombre_completo_ciudadano) | Q(
                ciudadano__apellido__icontains=nombre_completo_ciudadano
            )
        if data_estado:
            filters &= Q(estado=data_estado)
        if data_fecha_desde:
            filters &= Q(fecha_creado__gte=data_fecha_desde)

        object_list = Derivacion.objects.annotate(
            doc_str=Cast("ciudadano__documento", CharField())
        ).filter(filters)
        if nombre_completo_ciudadano:
            if nombre_completo_ciudadano.isnumeric():
                object_list = object_list.filter(
                    doc_str__startswith=nombre_completo_ciudadano
                )
            else:
                object_list = object_list.filter(
                    doc_str__icontains=nombre_completo_ciudadano
                )
        object_list = object_list.select_related(
            "programa", "organismo", "ciudadano"
        ).distinct()

        if not object_list.exists():
            messages.warning(self.request, "La búsqueda no arrojó resultados.")

        return object_list


class CiudadanosListView(ListView):
    model = Ciudadano
    template_name = "ciudadanos/ciudadanos_list.html"
    context_object_name = "ciudadanos"
    paginate_by = 20  # Aumentado para mejor UX

    def get_queryset(self):
        if not hasattr(self, "_cached_queryset"):
            # Optimización: Solo cargar campos necesarios para la lista
            queryset = (
                super()
                .get_queryset()
                .select_related("tipo_documento", "sexo", "localidad")  # Evitar N+1
                .only(
                    "id",
                    "apellido",
                    "nombre",
                    "documento",
                    "tipo_documento__tipo",
                    "sexo__sexo",
                    "localidad__nombre",
                    "estado",
                )
                .order_by("-id")  # Orden consistente para paginación
            )
            query = self.request.GET.get("busqueda", "")
            if query:
                filter_condition = Q(apellido__icontains=query)
                if query.isnumeric():
                    queryset = queryset.annotate(doc_str=Cast("documento", TextField()))
                    filter_condition |= Q(doc_str__startswith=query)
                queryset = queryset.filter(filter_condition)
            self._cached_queryset = queryset

        return self._cached_queryset

    def get(self, request, *args, **kwargs):
        query = self.request.GET.get("busqueda")
        if query:
            self.object_list = self.get_queryset()

            # Optimización: Evitar count() costoso y usar exists() + slice para verificar resultados
            # Solo verificar si hay 0, 1 o más resultados
            first_two = list(self.object_list[:2])

            if len(first_two) == 1:
                pk = first_two[0].id
                return redirect("ciudadanos_ver", pk=pk)
            elif len(first_two) == 0:
                messages.warning(self.request, "La búsqueda no arrojó resultados.")

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get("busqueda")
        mostrar_resultados = bool(query)
        page_obj = context.get("page_obj")

        if page_obj:
            # Optimización: Usar get_elided_page_range solo si es necesario
            try:
                context["page_range"] = page_obj.paginator.get_elided_page_range(
                    number=page_obj.number, on_each_side=2, on_ends=1
                )
            except AttributeError:
                # Fallback para versiones anteriores de Django
                context["page_range"] = page_obj.paginator.page_range

        # Breadcrumb
        context["breadcrumb_items"] = [
            {"url": reverse_lazy("dashboard"), "text": "Dashboard"},
            {"url": reverse_lazy("ciudadanos"), "text": "Ciudadanos"},
        ]

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

    def get_object(self, queryset=None):
        """Optimiza la carga del ciudadano con todas sus relaciones"""
        if queryset is None:
            queryset = self.get_queryset()

        pk = self.kwargs.get(self.pk_url_kwarg)
        if pk is not None:
            queryset = queryset.filter(pk=pk)

        # Optimizar la carga del ciudadano con prefetch_related
        try:
            self.object = (
                queryset.select_related(
                    "nacionalidad",
                    "sexo",
                    "tipo_documento",
                    "estado_civil",
                    "provincia",
                    "municipio",
                    "localidad",
                )
                .prefetch_related(
                    Prefetch(
                        "alertas",
                        queryset=Alerta.objects.select_related("categoria__dimension"),
                        to_attr="alertas_optimized",
                    ),
                    Prefetch(
                        "hist_ciudadano_alerta",
                        queryset=HistorialAlerta.objects.select_related(
                            "alerta__categoria__dimension"
                        ).order_by("-fecha_inicio"),
                        to_attr="historial_optimized",
                    ),
                    Prefetch(
                        "ciudadano1",
                        queryset=GrupoFamiliar.objects.select_related(
                            "ciudadano_2", "vinculo"
                        ).only(
                            "id",
                            "vinculo",
                            "vinculo_inverso",
                            "ciudadano_2__nombre",
                            "ciudadano_2__apellido",
                            "ciudadano_2__id",
                            "ciudadano_2__foto",
                            "vinculo__vinculo",
                        ),
                        to_attr="familia_1_optimized",
                    ),
                    Prefetch(
                        "ciudadano2",
                        queryset=GrupoFamiliar.objects.select_related(
                            "ciudadano_1", "vinculo"
                        ).only(
                            "id",
                            "vinculo",
                            "vinculo_inverso",
                            "ciudadano_1__nombre",
                            "ciudadano_1__apellido",
                            "ciudadano_1__id",
                            "ciudadano_1__foto",
                            "vinculo__vinculo",
                        ),
                        to_attr="familia_2_optimized",
                    ),
                    Prefetch(
                        "archivo_set",
                        queryset=Archivo.objects.filter(
                            Q(tipo="Imagen") | Q(tipo="Documento")
                        ).only("id", "archivo", "fecha", "tipo", "ciudadano_id"),
                        to_attr="archivos_optimized",
                    ),
                    Prefetch(
                        "ciudadano_programa",
                        queryset=CiudadanoPrograma.objects.select_related("programas")
                        .only(
                            "id",
                            "programas__nombre",
                            "programas__id",
                            "fecha_creado",
                            "ciudadano_id",
                        )
                        .order_by("-fecha_creado"),
                        to_attr="programas_optimized",
                    ),
                )
                .get()
            )
            return self.object
        except Ciudadano.DoesNotExist as exc:
            raise Http404("Ciudadano no encontrado") from exc

    def get_context_data(
        self, **kwargs
    ):  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        pk = self.kwargs["pk"]
        context = super().get_context_data(**kwargs)

        ciudadano = context["object"]
        fecha_actual = datetime.now().date()

        # Usar los datos ya prefetched en lugar de hacer queries adicionales
        ciudadano_alertas = getattr(ciudadano, "alertas_optimized", [])
        alertas = getattr(ciudadano, "historial_optimized", [])

        # Usar datos prefetched para familiares
        familiares_1 = (
            [
                {
                    "ciudadano_1__id": pk,
                    "ciudadano_1__nombre": ciudadano.nombre,
                    "ciudadano_1__apellido": ciudadano.apellido,
                    "ciudadano_1__foto": ciudadano.foto,
                    "ciudadano_2__id": rel.ciudadano_2.id,
                    "ciudadano_2__nombre": rel.ciudadano_2.nombre,
                    "ciudadano_2__apellido": rel.ciudadano_2.apellido,
                    "ciudadano_2__foto": rel.ciudadano_2.foto,
                    "vinculo": rel.vinculo.vinculo if rel.vinculo else "",
                    "vinculo_inverso": rel.vinculo_inverso,
                }
                for rel in ciudadano.familia_1_optimized
            ]
            if hasattr(ciudadano, "familia_1_optimized")
            else []
        )

        familiares_2 = (
            [
                {
                    "ciudadano_2__id": pk,
                    "ciudadano_2__nombre": ciudadano.nombre,
                    "ciudadano_2__apellido": ciudadano.apellido,
                    "ciudadano_2__foto": ciudadano.foto,
                    "ciudadano_1__id": rel.ciudadano_1.id,
                    "ciudadano_1__nombre": rel.ciudadano_1.nombre,
                    "ciudadano_1__apellido": rel.ciudadano_1.apellido,
                    "ciudadano_1__foto": rel.ciudadano_1.foto,
                    "vinculo": rel.vinculo.vinculo if rel.vinculo else "",
                    "vinculo_inverso": rel.vinculo_inverso,
                }
                for rel in ciudadano.familia_2_optimized
            ]
            if hasattr(ciudadano, "familia_2_optimized")
            else []
        )

        # Organizacion de alertas optimizada
        alertas_criticas = [
            alerta for alerta in ciudadano_alertas if alerta.gravedad == "Critica"
        ]
        alertas_importantes = [
            alerta for alerta in ciudadano_alertas if alerta.gravedad == "Importante"
        ]
        alertas_precaucion = [
            alerta for alerta in ciudadano_alertas if alerta.gravedad == "Precaución"
        ]

        # Cargar dimensiones de manera eficiente usando cache
        cache_key_dims = f"ciudadano_dimensions_{pk}"
        dimensiones = cache.get(cache_key_dims)
        if not dimensiones:
            try:
                dimensionfamilia = DimensionFamilia.objects.get(ciudadano_id=pk)
            except DimensionFamilia.DoesNotExist:
                dimensionfamilia = None

            try:
                dimensionvivienda = DimensionVivienda.objects.get(ciudadano_id=pk)
            except DimensionVivienda.DoesNotExist:
                dimensionvivienda = None

            try:
                dimensionsalud = DimensionSalud.objects.get(ciudadano_id=pk)
            except DimensionSalud.DoesNotExist:
                dimensionsalud = None

            try:
                dimensiontrabajo = DimensionTrabajo.objects.get(ciudadano_id=pk)
            except DimensionTrabajo.DoesNotExist:
                dimensiontrabajo = None

            dimensiones = {
                "familia": dimensionfamilia,
                "vivienda": dimensionvivienda,
                "salud": dimensionsalud,
                "trabajo": dimensiontrabajo,
            }
            cache.set(
                cache_key_dims, dimensiones, settings.DEFAULT_CACHE_TIMEOUT
            )  # Cache por 5 minutos

        # Archivos usando datos prefetched
        files = getattr(ciudadano, "archivos_optimized", [])

        # Programas usando datos prefetched
        ciudadanos_programas = getattr(ciudadano, "programas_optimized", [])

        # Cache solo los cálculos pesados
        cache_key = f"ciudadano_context_{pk}"
        cached_data = cache.get(cache_key)
        if not cached_data:
            # Solo contar derivaciones, no cargar todas
            count_intervenciones = Derivacion.objects.filter(ciudadano=pk).count()
            count_programas = len(ciudadanos_programas)
            datos_json = self.grafico_evolucion_de_riesgo(fecha_actual, alertas)
            emoji_nacionalidad = (
                EMOJIS_BANDERAS.get(str(ciudadano.nacionalidad), "")
                if ciudadano.nacionalidad
                else ""
            )

            cached_data = {
                "count_intervenciones": count_intervenciones,
                "count_programas": count_programas,
                "datos_json": datos_json,
                "emoji_nacionalidad": emoji_nacionalidad,
            }
            cache.set(
                cache_key, cached_data, settings.DEFAULT_CACHE_TIMEOUT
            )  # Cache por 5 minutos

        # Obtener hogar familiares (si es necesario)
        hogar_familiares = cache.get_or_set(
            f"hogar_familiares_{pk}",
            GrupoHogar.objects.filter(Q(ciudadano_1Hogar=pk) | Q(ciudadano_2Hogar=pk))
            .select_related("ciudadano_1Hogar", "ciudadano_2Hogar")
            .values(
                "ciudadano_2Hogar_id",
                "ciudadano_2Hogar",
                "ciudadano_1Hogar_id",
                "ciudadano_1Hogar",
                "ciudadano_1Hogar__nombre",
                "ciudadano_2Hogar__nombre",
                "ciudadano_1Hogar__foto",
                "ciudadano_2Hogar__foto",
                "estado_relacion",
            ),
            60,
        )

        context.update(
            {
                "familiares_fk1": familiares_1,
                "familiares_fk2": familiares_2,
                "count_familia": len(familiares_1) + len(familiares_2),
                "hogar_familiares_fk1": [
                    f for f in hogar_familiares if f["ciudadano_1Hogar"] == int(pk)
                ],
                "hogar_familiares_fk2": [
                    f for f in hogar_familiares if f["ciudadano_2Hogar"] == int(pk)
                ],
                "hogar_count_familia": len(hogar_familiares),
                "files_img": [f for f in files if f.tipo == "Imagen"],
                "files_docs": [f for f in files if f.tipo == "Documento"],
                "count_alertas": len(ciudadano_alertas),
                "count_alta": len(alertas_criticas),
                "count_media": len(alertas_importantes),
                "count_baja": len(alertas_precaucion),
                "alertas_alta": alertas_criticas,
                "alertas_media": alertas_importantes,
                "alertas_baja": alertas_precaucion,
                "historial_alertas": len(alertas) > 0,
                "dimensionfamilia": dimensiones["familia"],
                "dimensionvivienda": dimensiones["vivienda"],
                "dimensionsalud": dimensiones["salud"],
                "dimensiontrabajo": dimensiones["trabajo"],
                "form_prog": ProgramaForm(),
                "ciudadanos_programas": (
                    ciudadanos_programas if ciudadanos_programas else None
                ),
                **cached_data,
            }
        )

        return context

    def grafico_evolucion_de_riesgo(
        self, fecha_actual, alertas
    ):  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        if alertas:  # Changed from alertas.exists() to check if list is not empty
            primer_dia_siguiente_mes = datetime(
                fecha_actual.year, fecha_actual.month % 12 + 1, 1
            )
            fecha_inicio_doce_meses_excepto_mes_anterior = (
                primer_dia_siguiente_mes - timedelta(days=365)
            )

            # Filter alertas list instead of using queryset filter
            alertas_ultimo_anio = []
            for alerta in alertas:
                if (
                    (
                        alerta.fecha_inicio
                        and alerta.fecha_inicio
                        > fecha_inicio_doce_meses_excepto_mes_anterior
                    )
                    or (
                        alerta.fecha_fin
                        and alerta.fecha_fin
                        > fecha_inicio_doce_meses_excepto_mes_anterior
                    )
                    or alerta.fecha_fin is None
                ):
                    alertas_ultimo_anio.append(alerta)

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
                # Access object attributes instead of dict keys
                dimension = str(alerta.alerta.categoria.dimension.id)
                fecha_inicio = alerta.fecha_inicio
                fecha_fin = alerta.fecha_fin or fecha_actual

                meses_activos = []
                while fecha_inicio <= fecha_fin:
                    meses_activos.append(fecha_inicio.month)
                    fecha_inicio = fecha_inicio.replace(day=1) + timedelta(days=32)
                    fecha_inicio = fecha_inicio.replace(day=1)

                for mes in meses_activos:
                    if dimension in datos_por_dimension:
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
    """
    View refactorizada para crear ciudadanos usando componentes
    """

    model = Ciudadano
    form_class = CiudadanoForm
    template_name = "ciudadanos/ciudadano_form.html"
    success_message = "Ciudadano creado exitosamente"

    def get_context_data(self, **kwargs):
        """Contexto para el template con breadcrumbs"""
        context = super().get_context_data(**kwargs)

        # Breadcrumbs para crear
        context["breadcrumb_items"] = [
            {"url": reverse_lazy("dashboard"), "text": "Dashboard"},
            {"url": reverse_lazy("ciudadanos"), "text": "Ciudadanos"},
        ]
        context["current_breadcrumb"] = "Agregar"

        return context

    def form_invalid(self, form):
        """Manejo de errores en el formulario"""
        messages.error(
            self.request,
            "Se produjo un error al crear el ciudadano. Por favor, verifique los datos ingresados.",
        )
        return super().form_invalid(form)

    def form_valid(self, form):
        """Procesamiento cuando el formulario es válido"""
        ciudadano = form.save(commit=False)

        # Procesar la foto si se subió una
        if ciudadano.foto:
            try:
                buffer = recortar_imagen(ciudadano.foto)
                ciudadano.foto.save(ciudadano.foto.name, ContentFile(buffer.getvalue()))
            except Exception as e:
                messages.warning(
                    self.request,
                    f"La foto se subió pero hubo un problema al procesarla: {e}",
                )

        try:
            with transaction.atomic():
                # Guardar el ciudadano
                ciudadano.save()

                # Crear automáticamente todas las dimensiones
                self._crear_dimensiones(ciudadano)

                messages.success(self.request, self.success_message)

                # Redireccionar según el botón presionado
                return self._handle_form_navigation(ciudadano.id)

        except Exception as e:
            messages.error(
                self.request,
                f"Se produjo un error al crear el ciudadano y sus dimensiones: {e}",
            )
            return redirect("ciudadanos_crear")

    def _crear_dimensiones(self, ciudadano):
        """Crea automáticamente todas las dimensiones para el ciudadano"""
        try:
            DimensionFamilia.objects.create(ciudadano=ciudadano)
            DimensionVivienda.objects.create(ciudadano=ciudadano)
            DimensionSalud.objects.create(ciudadano=ciudadano)
            DimensionEconomia.objects.create(ciudadano=ciudadano)
            DimensionEducacion.objects.create(ciudadano=ciudadano)
            DimensionTrabajo.objects.create(ciudadano=ciudadano)
        except Exception as e:
            raise Exception(f"Error al crear dimensiones: {e}")

    def _handle_form_navigation(self, ciudadano_id):
        """Maneja la navegación según el botón presionado"""
        if "form_step2" in self.request.POST:
            # Continuar al paso 2 (dimensiones)
            return redirect("ciudadanosdimensiones_editar", pk=ciudadano_id)
        else:
            # Por defecto, ir al detalle
            return redirect("ciudadanos_ver", pk=ciudadano_id)


class CiudadanosUpdateView(UpdateView):
    """
    View refactorizada para editar ciudadanos usando componentes
    """

    model = Ciudadano
    form_class = CiudadanoUpdateForm
    template_name = "ciudadanos/ciudadano_form.html"
    success_message = "Ciudadano actualizado exitosamente"

    def get_context_data(self, **kwargs):
        """Contexto para el template con breadcrumbs"""
        context = super().get_context_data(**kwargs)

        # Breadcrumbs para editar
        context["breadcrumb_items"] = [
            {"url": reverse_lazy("dashboard"), "text": "Dashboard"},
            {"url": reverse_lazy("ciudadanos"), "text": "Ciudadanos"},
            {
                "url": reverse_lazy("ciudadanos_ver", kwargs={"pk": self.object.id}),
                "text": str(self.object),
            },
        ]
        context["current_breadcrumb"] = "Editar"

        return context

    def form_valid(self, form):
        """Procesamiento cuando el formulario es válido"""
        ciudadano = form.save(commit=False)
        current_ciudadano = self.get_object()

        try:
            with transaction.atomic():
                # Manejar eliminación de foto si se solicitó
                if self.request.POST.get("delete_foto") == "true":
                    if current_ciudadano.foto:
                        current_ciudadano.foto.delete(save=False)
                    ciudadano.foto = None

                # Procesar nueva foto si se subió
                elif ciudadano.foto and ciudadano.foto != current_ciudadano.foto:
                    try:
                        buffer = recortar_imagen(ciudadano.foto)
                        ciudadano.foto.save(
                            ciudadano.foto.name, ContentFile(buffer.getvalue())
                        )
                    except Exception as e:
                        messages.warning(
                            self.request,
                            f"La foto se subió pero hubo un problema al procesarla: {e}",
                        )

                # Guardar el ciudadano actualizado
                self.object = ciudadano
                self.object.save()

                messages.success(self.request, self.success_message)

                # Redireccionar según el botón presionado
                return self._handle_form_navigation()

        except Exception as e:
            messages.error(
                self.request, f"Se produjo un error al actualizar el ciudadano: {e}"
            )
            return self.form_invalid(form)

    def _handle_form_navigation(self):
        """Maneja la navegación según el botón presionado"""
        if "form_ciudadanos" in self.request.POST:
            # Guardar y ir al detalle
            return redirect("ciudadanos_ver", pk=self.object.id)
        elif "form_step2" in self.request.POST:
            # Continuar al paso 2 (dimensiones)
            return redirect("ciudadanosdimensiones_editar", pk=self.object.id)
        else:
            # Por defecto, ir al detalle
            return redirect("ciudadanos_ver", pk=self.object.id)

    def form_invalid(self, form):
        """Manejo de errores en el formulario"""
        messages.error(
            self.request,
            "Se produjo un error al actualizar el ciudadano. Por favor, verifique los datos ingresados.",
        )
        return super().form_invalid(form)


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

        # Preparar datos para familiares_grid.html
        familiares_display = []

        # Convertir familiares_fk1 para el componente
        for familiar in context.get("familiares_fk1", []):
            familiares_display.append(
                {
                    "id": familiar["id"],
                    "nombre": familiar["ciudadano_2__nombre"],
                    "apellido": familiar["ciudadano_2__apellido"],
                    "documento": f"DNI {familiar.get('documento', 'N/A')}",  # Si tienes documento
                    "foto": familiar["ciudadano_2__foto"],
                    "vinculo": familiar["vinculo"],
                    "telefono": familiar.get("telefono", ""),
                    "fecha_nacimiento": familiar.get("fecha_nacimiento", ""),
                    "convive": familiar.get("conviven", None),
                    "cuidador_principal": familiar.get("cuidador_principal", False),
                }
            )

        # Convertir familiares_fk2 para el componente
        for familiar in context.get("familiares_fk2", []):
            familiares_display.append(
                {
                    "id": familiar["id"],
                    "nombre": familiar["ciudadano_1__nombre"],
                    "apellido": familiar["ciudadano_1__apellido"],
                    "documento": f"DNI {familiar.get('documento', 'N/A')}",  # Si tienes documento
                    "foto": familiar["ciudadano_1__foto"],
                    "vinculo": familiar["vinculo_inverso"],
                    "telefono": familiar.get("telefono", ""),
                    "fecha_nacimiento": familiar.get("fecha_nacimiento", ""),
                    "convive": familiar.get("conviven", None),
                    "cuidador_principal": familiar.get("cuidador_principal", False),
                }
            )

        context.update(
            {
                "es_menor_de_18": es_menor_de_18,
                "tiene_cuidador_ppal": tiene_cuidador_ppal,
                "pk": pk,
                "id_dimensionfamiliar": DimensionFamilia.objects.get(ciudadano=pk).id,
                "familiares_display": familiares_display,  # Para el componente familiares_grid
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
    familiares = (
        Ciudadano.objects.annotate(doc_str=Cast("documento", TextField()))
        .filter(
            ~Q(id=ciudadano_principal_id)
            & (Q(apellido__icontains=busqueda) | Q(doc_str__startswith=busqueda))
        )
        .exclude(id__in=ciudadanos_asociados_ids)
    )

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

        # Solo cargar datos cuando se haga una búsqueda específica
        barrios = cache.get_or_set(
            "ciudadanos_barrios",
            Ciudadano.objects.values_list("barrio", flat=True).distinct(),
            300,
        )
        circuitos = cache.get_or_set(
            "circuitos_list", Circuito.objects.all().values_list("id", "circuito"), 300
        )
        localidad = cache.get_or_set(
            "nacionalidades_list",
            Nacionalidad.objects.all().values_list("id", "nacionalidad"),
            300,
        )

        mostrar_resultados = False
        mostrar_btn_resetear = False
        query = self.request.GET.get("busqueda")
        con_derivaciones = Derivacion.objects.none()
        sin_derivaciones = Ciudadano.objects.none()

        if query:
            # Solo buscar cuando se proporcione un término de búsqueda
            derivaciones_filtrado = (
                Derivacion.objects.annotate(
                    doc_str=Cast("ciudadano__documento", CharField())
                )
                .filter(
                    Q(ciudadano__apellido__icontains=query)
                    | Q(doc_str__startswith=query)
                )
                .values("ciudadano")
                .distinct()
            )
            ciudadanos_filtrado = (
                Ciudadano.objects.annotate(doc_str=Cast("documento", TextField()))
                .filter(Q(apellido__icontains=query) | Q(doc_str__startswith=query))
                .distinct()
            )
            if derivaciones_filtrado.exists():
                sin_derivaciones = ciudadanos_filtrado.exclude(
                    id__in=derivaciones_filtrado
                )
                con_derivaciones = ciudadanos_filtrado.filter(
                    id__in=derivaciones_filtrado
                )

            else:
                sin_derivaciones = ciudadanos_filtrado

            if not derivaciones_filtrado.exists() and not ciudadanos_filtrado.exists():
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

        # Cache estados para evitar consultas repetidas
        estado_pendiente = cache.get_or_set(
            "estado_pendiente",
            EstadoDerivacion.objects.filter(estado="Pendiente").first(),
            300,
        )
        estado_aceptada = cache.get_or_set(
            "estado_aceptada",
            EstadoDerivacion.objects.filter(estado="Aceptada").first(),
            300,
        )
        estado_analisis = cache.get_or_set(
            "estado_analisis",
            EstadoDerivacion.objects.filter(estado="En análisis").first(),
            300,
        )
        estado_asesoradas = cache.get_or_set(
            "estado_asesoradas",
            EstadoDerivacion.objects.filter(estado="Asesoramiento").first(),
            300,
        )

        # Optimización: usar una sola query con agregaciones para contar todos los estados
        counts = Derivacion.objects.aggregate(
            pendientes=Count(Case(When(estado=estado_pendiente, then=1))),
            aceptadas=Count(Case(When(estado=estado_aceptada, then=1))),
            analisis=Count(Case(When(estado=estado_analisis, then=1))),
            asesoradas=Count(Case(When(estado=estado_asesoradas, then=1))),
            enviadas=Count(Case(When(usuario=self.request.user, then=1))),
        )

        context.update(counts)
        return context

    # Funcion de busqueda

    def get_queryset(self):
        # Optimización: usar select_related para evitar N+1 queries
        queryset = Derivacion.objects.select_related(
            "ciudadano", "programa", "organismo", "estado", "usuario"
        )

        query = self.request.GET.get("busqueda")
        if query:
            queryset = (
                queryset.annotate(doc_str=Cast("ciudadano__documento", CharField()))
                .filter(
                    Q(ciudadano__apellido__icontains=query)
                    | Q(doc_str__startswith=query)
                )
                .distinct()
            )

        return queryset.order_by("-fecha_creado")


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

        # Optimización: cargar solo campos necesarios del ciudadano
        ciudadano = Ciudadano.objects.only("id", "nombre", "apellido").get(id=pk)

        # Optimización: usar prefetch con select_related para historial
        historial = Derivacion.objects.filter(ciudadano_id=pk).select_related(
            "estado", "programa", "organismo"
        )

        # Optimización: usar cache para estados y una sola query con agregaciones
        estado_pendiente = cache.get_or_set(
            "estado_pendiente_hist",
            EstadoDerivacion.objects.filter(estado="Pendiente").first(),
            300,
        )
        estado_aceptada = cache.get_or_set(
            "estado_aceptada_hist",
            EstadoDerivacion.objects.filter(estado="Aceptada").first(),
            300,
        )
        estado_rechazada = cache.get_or_set(
            "estado_rechazada_hist",
            EstadoDerivacion.objects.filter(estado="Rechazada").first(),
            300,
        )

        # Optimización: una sola query para contar todos los estados
        counts = historial.aggregate(
            pendientes=Count(Case(When(estado=estado_pendiente, then=1))),
            admitidas=Count(Case(When(estado=estado_aceptada, then=1))),
            rechazadas=Count(Case(When(estado=estado_rechazada, then=1))),
        )

        context["historial"] = historial
        context["ciudadano"] = ciudadano
        context.update(counts)
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
                registro_historial.eliminada_por = request.user.username
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
    """
    View refactorizada para actualizar dimensiones usando componentes
    Maneja múltiples formularios de dimensiones en una sola vista
    """

    template_name = "ciudadanos/dimension_form.html"
    model = DimensionFamilia
    form_class = DimensionFamiliaForm
    success_message = "Dimensiones actualizadas correctamente"

    def get_object(self, queryset=None):
        """Obtiene el objeto DimensionFamilia del ciudadano"""
        pk = self.kwargs["pk"]
        ciudadano = get_object_or_404(Ciudadano, id=pk)
        dimension_familia, created = DimensionFamilia.objects.get_or_create(
            ciudadano=ciudadano, defaults={"ciudadano": ciudadano}
        )
        return dimension_familia

    def get_context_data(self, **kwargs):
        """Contexto optimizado para usar con componentes"""
        context = super().get_context_data(**kwargs)

        pk = self.kwargs["pk"]

        # Cargar ciudadano con todas las dimensiones de una vez
        ciudadano = Ciudadano.objects.select_related(
            "tipo_documento", "sexo", "nacionalidad"
        ).get(id=pk)

        # Crear o recuperar todas las dimensiones
        dimensiones_data = self._get_or_create_dimensions(ciudadano)

        # Preparar formularios para cada dimensión (SIN prefijos)
        context.update(
            {
                "ciudadano": ciudadano,
                "form_vivienda": DimensionViviendaForm(
                    instance=dimensiones_data["vivienda"]
                ),
                "form_salud": DimensionSaludForm(instance=dimensiones_data["salud"]),
                "form_educacion": DimensionEducacionForm(
                    instance=dimensiones_data["educacion"]
                ),
                "form_economia": DimensionEconomiaForm(
                    instance=dimensiones_data["economia"]
                ),
                "form_trabajo": DimensionTrabajoForm(
                    instance=dimensiones_data["trabajo"]
                ),
            }
        )

        return context

    def _get_or_create_dimensions(self, ciudadano):
        """Método auxiliar para obtener o crear todas las dimensiones"""
        dimensiones = {}

        # Dimensión Vivienda
        dimensiones["vivienda"], _ = DimensionVivienda.objects.get_or_create(
            ciudadano=ciudadano, defaults={"ciudadano": ciudadano}
        )

        # Dimensión Salud
        dimensiones["salud"], _ = DimensionSalud.objects.get_or_create(
            ciudadano=ciudadano, defaults={"ciudadano": ciudadano}
        )

        # Dimensión Educación
        dimensiones["educacion"], _ = DimensionEducacion.objects.get_or_create(
            ciudadano=ciudadano, defaults={"ciudadano": ciudadano}
        )

        # Dimensión Economía
        dimensiones["economia"], _ = DimensionEconomia.objects.get_or_create(
            ciudadano=ciudadano, defaults={"ciudadano": ciudadano}
        )

        # Dimensión Trabajo
        dimensiones["trabajo"], _ = DimensionTrabajo.objects.get_or_create(
            ciudadano=ciudadano, defaults={"ciudadano": ciudadano}
        )

        return dimensiones

    def post(self, request, *args, **kwargs):
        """Maneja el POST para múltiples formularios"""
        self.object = self.get_object()
        pk = self.kwargs["pk"]
        ciudadano = get_object_or_404(Ciudadano, id=pk)

        # Obtener todas las dimensiones
        dimensiones_data = self._get_or_create_dimensions(ciudadano)

        # Crear formularios con datos POST (SIN prefijos para mantener compatibilidad)
        form = self.get_form()
        form_vivienda = DimensionViviendaForm(
            request.POST, instance=dimensiones_data["vivienda"]
        )
        form_salud = DimensionSaludForm(
            request.POST, instance=dimensiones_data["salud"]
        )
        form_educacion = DimensionEducacionForm(
            request.POST, instance=dimensiones_data["educacion"]
        )
        form_economia = DimensionEconomiaForm(
            request.POST, instance=dimensiones_data["economia"]
        )
        form_trabajo = DimensionTrabajoForm(
            request.POST, instance=dimensiones_data["trabajo"]
        )

        # Validar todos los formularios
        forms_valid = all(
            [
                form.is_valid(),
                form_vivienda.is_valid(),
                form_salud.is_valid(),
                form_educacion.is_valid(),
                form_economia.is_valid(),
                form_trabajo.is_valid(),
            ]
        )

        if forms_valid:
            return self._handle_valid_forms(
                request,
                pk,
                form,
                form_vivienda,
                form_salud,
                form_educacion,
                form_economia,
                form_trabajo,
            )
        else:
            # Si hay errores, mostrar mensajes
            messages.error(request, "Por favor corrige los errores en el formulario.")
            return self.form_invalid(form)

    def _handle_valid_forms(
        self,
        request,
        pk,
        form,
        form_vivienda,
        form_salud,
        form_educacion,
        form_economia,
        form_trabajo,
    ):
        """Maneja el guardado cuando todos los formularios son válidos"""

        with transaction.atomic():
            # Guardar todas las dimensiones
            form.save()
            form_vivienda.save()
            form_salud.save()
            form_educacion.save()
            form_economia.save()
            form_trabajo.save()

            # Invalidar cache de dimensiones para este ciudadano
            cache_key = f"ciudadano_dimensions_{pk}"
            cache.delete(cache_key)

            messages.success(request, self.success_message)

            # Redireccionar según el botón presionado
            return self._handle_form_navigation(request, pk)

    def _handle_form_navigation(self, request, pk):
        """Maneja la navegación entre pasos del formulario"""
        if "form_step1" in request.POST:
            # Volver al paso 1 (datos personales)
            return redirect("ciudadanos_editar", pk=pk)
        elif "form_step2" in request.POST:
            # Guardar y ir al detalle del ciudadano
            return redirect("ciudadanos_ver", pk=pk)
        elif "form_step3" in request.POST:
            # Continuar al paso 3 (grupo familiar)
            return redirect("grupofamiliar_crear", pk=pk)
        else:
            # Por defecto, volver al detalle
            return redirect("ciudadanos_ver", pk=pk)

    def form_invalid(self, form):
        """Maneja errores en los formularios"""
        pk = self.kwargs["pk"]
        ciudadano = get_object_or_404(Ciudadano, id=pk)
        dimensiones_data = self._get_or_create_dimensions(ciudadano)

        # Re-crear formularios para mostrar errores (SIN prefijos)
        context = self.get_context_data()
        context.update(
            {
                "form_vivienda": DimensionViviendaForm(
                    self.request.POST, instance=dimensiones_data["vivienda"]
                ),
                "form_salud": DimensionSaludForm(
                    self.request.POST, instance=dimensiones_data["salud"]
                ),
                "form_educacion": DimensionEducacionForm(
                    self.request.POST, instance=dimensiones_data["educacion"]
                ),
                "form_economia": DimensionEconomiaForm(
                    self.request.POST, instance=dimensiones_data["economia"]
                ),
                "form_trabajo": DimensionTrabajoForm(
                    self.request.POST, instance=dimensiones_data["trabajo"]
                ),
            }
        )

        return self.render_to_response(context)

    def get_success_url(self):
        """URL de éxito por defecto"""
        return reverse_lazy("ciudadanos_ver", kwargs={"pk": self.kwargs["pk"]})


class DimensionesDetailView(DetailView):
    model = Ciudadano
    template_name = "ciudadanos/dimension_detail.html"


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

        # Obtener hogares asociados al ciudadano principal
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
            "ciudadano_1Hogar__documento",  # Acceso correcto al documento
            "ciudadano_2Hogar__documento",  # Acceso correcto al documento
            "ciudadano_1Hogar__tipo_documento",  # Para mostrar tipo
            "ciudadano_2Hogar__tipo_documento",  # Para mostrar tipo
            "estado_relacion",
        )

        # Paginación
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

        context["hogares"] = page_obj
        context["count_hogar"] = hogares.count()
        context["ciudadano_principal"] = ciudadano_principal
        context["pk"] = pk

        # Preparar datos para familiares_grid.html (adaptado para hogar)
        hogar_display = []

        # Convertir hogar_1 para el componente
        for hogar in context.get("hogar_1", []):
            documento_completo = f"{hogar.get('ciudadano_2Hogar__tipo_documento', 'DNI')} {hogar.get('ciudadano_2Hogar__documento', 'N/A')}"
            hogar_display.append(
                {
                    "id": hogar["id"],
                    "nombre": hogar["ciudadano_2Hogar__nombre"],
                    "apellido": hogar["ciudadano_2Hogar__apellido"],
                    "documento": documento_completo,
                    "foto": hogar["ciudadano_2Hogar__foto"],
                    "vinculo": "Conviviente",  # Para hogar no hay vínculo específico familiar
                    "telefono": "",  # Los hogares no tienen teléfono directo
                    "fecha_nacimiento": "",  # Puedes agregar si necesitas
                    "convive": True,  # En hogar siempre conviven
                    "estado_relacion": hogar.get("estado_relacion", ""),
                }
            )

        # Convertir hogar_2 para el componente
        for hogar in context.get("hogar_2", []):
            documento_completo = f"{hogar.get('ciudadano_1Hogar__tipo_documento', 'DNI')} {hogar.get('ciudadano_1Hogar__documento', 'N/A')}"
            hogar_display.append(
                {
                    "id": hogar["id"],
                    "nombre": hogar["ciudadano_1Hogar__nombre"],
                    "apellido": hogar["ciudadano_1Hogar__apellido"],
                    "documento": documento_completo,
                    "foto": hogar["ciudadano_1Hogar__foto"],
                    "vinculo": "Conviviente",
                    "telefono": "",
                    "fecha_nacimiento": "",
                    "convive": True,
                    "estado_relacion": hogar.get("estado_relacion", ""),
                }
            )

        # Agregar al context
        context.update(
            {
                "hogar_display": hogar_display,
                "hogar_count_familia": len(hogar_display),  # Contador para el template
            }
        )

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
        except Exception as e:
            messages.error(
                self.request,
                f"Verifique que no exista un ciudadano con ese DNI y NÚMERO. Error: {e}",
            )
            return HttpResponseRedirect(self.request.path_info)

        # Crea la relación de grupo hogar
        try:
            estado_relacion_instance = EstadoRelacion.objects.get(pk=estado_relacion)
            ciudadano_principal = Ciudadano.objects.get(id=pk)

            GrupoHogar.objects.create(
                ciudadano_1Hogar=ciudadano_principal,
                ciudadano_2Hogar=nuevo_ciudadano,
                estado_relacion=estado_relacion_instance,
            )
        except Exception as e:
            messages.error(
                self.request,
                f"Error al crear la relación de hogar. Error: {e}",
            )
            return HttpResponseRedirect(self.request.path_info)

        messages.success(self.request, "Conviviente agregado correctamente.")
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
    hogares = (
        Ciudadano.objects.annotate(doc_str=Cast("documento", TextField()))
        .filter(
            ~Q(id=ciudadano_principal_id)
            & (Q(apellido__icontains=busqueda) | Q(doc_str__startswith=busqueda))
        )
        .exclude(id__in=ciudadanos_asociados_ids)
    )

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
