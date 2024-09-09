import locale
import logging
from datetime import date

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy

from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
    View,
)

from config.settings import CACHE_TIMEOUT
from configuraciones.choices import CHOICE_CIRCUITOS
from configuraciones.models import Alertas, CategoriaAlertas, Organismos, Programas
from legajos.choices import (
    CHOICE_ESTADO_DERIVACION,
    CHOICE_NACIONALIDAD,
    EMOJIS_BANDERAS,
    VINCULO_MAP,
)
from legajos.forms import (
    DimensionEconomiaForm,
    DimensionEducacionForm,
    DimensionFamiliaForm,
    DimensionSaludForm,
    DimensionTrabajoForm,
    DimensionViviendaForm,
    LegajoGrupoHogarForm,
    LegajosAlertasForm,
    LegajosArchivosForm,
    LegajosDerivacionesForm,
    LegajosForm,
    LegajosUpdateForm,
    NuevoLegajoFamiliarForm,
)
from legajos.models import (
    DimensionEconomia,
    DimensionEducacion,
    DimensionFamilia,
    DimensionSalud,
    DimensionTrabajo,
    DimensionVivienda,
    HistorialLegajoAlertas,
    LegajoAlertas,
    LegajoGrupoFamiliar,
    LegajoGrupoHogar,
    Legajos,
    LegajosArchivos,
    LegajosDerivaciones,
)
from legajos.services.legajos_service import LegajosService

from usuarios.mixins import PermisosMixin
from usuarios.utils import recortar_imagen

locale.setlocale(locale.LC_ALL, "es_AR.UTF-8")

logger = logging.getLogger("django")

ROL_ADMIN = "Usuarios.rol_admin"

class MunicipiosView(View):
    def get(self, request, *args, **kwargs):
        provincia_id = request.GET.get("provincia_id")
        municipios = LegajosService.obtener_municipios(provincia_id)

        return JsonResponse(municipios, safe=False)

class LocalidadesView(View):
    def get(self, request, *args, **kwargs):
        municipio_id = request.GET.get("municipio_id")
        localidades = LegajosService.obtener_localidades(municipio_id)

        return JsonResponse(localidades, safe=False)


class LegajosReportesListView(ListView):
    template_name = "legajos/legajos_reportes.html"
    model = LegajosDerivaciones

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        derivaciones = LegajosService.obtener_derivaciones(
            self.request.GET.get("data_programa"),
            self.request.GET.get("data_organismo"),
            self.request.GET.get("busqueda"),
            self.request.GET.get("data_estado"),
            self.request.GET.get("data_fecha_derivacion"),
        )
        if not derivaciones.exists():
            messages.warning(self.request, "La búsqueda no arrojó resultados.")

        organismos = cache.get_or_set(
            "organismos", Organismos.objects.all().values("id", "nombre"), CACHE_TIMEOUT
        )
        programas = cache.get_or_set(
            "programas", Programas.objects.all().values("id", "nombre"), CACHE_TIMEOUT
        )

        context.update(
            {
                "derivaciones": derivaciones,
                "organismos": organismos,
                "programas": programas,
                "estados": CHOICE_ESTADO_DERIVACION,
            }
        )
        return context


class LegajosListView(ListView):
    model = Legajos
    template_name = "legajos/legajos_list.html"
    context_object_name = "legajos"
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get("busqueda")

        if query:
            cached_queryset_name = f"cached_queryset_{query}"
            queryset_filtrado = cache.get_or_set(
                cached_queryset_name,
                LegajosService.obtener_queryset_filtrado(query),
                CACHE_TIMEOUT,
            )
            return queryset_filtrado

        return Legajos.objects.none()

    def get(self, request, *args, **kwargs):
        query = self.request.GET.get("busqueda")
        queryset = self.get_queryset()
        size_queryset = queryset.count()

        if size_queryset == 1:
            pk = queryset.first().id
            return redirect("legajos_ver", pk=pk)
        elif size_queryset == 0 and query:
            messages.warning(self.request, "La búsqueda no arrojó resultados.")

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get("busqueda")

        context["mostrar_resultados"] = bool(query)
        context["query"] = query

        page_obj = context.get("page_obj")
        if page_obj:
            context["page_range"] = page_obj.paginator.get_elided_page_range(
                number=page_obj.number
            )

        return context


class LegajosDetailView(DetailView):
    model = Legajos
    template_name = "legajos/legajos_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        pk = self.kwargs["pk"]

        extras = LegajosService.obtener_extras_legajo(pk)

        context["emoji_nacionalidad"] = EMOJIS_BANDERAS.get(
            context["object"].nacionalidad, ""
        )
        context.update(extras)

        return context


class LegajosDeleteView(PermisosMixin, DeleteView):
    permission_required = ROL_ADMIN
    model = Legajos
    success_url = reverse_lazy("legajos_listar")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        legajo = self.get_object()

        # Lista de nombres de relaciones
        context.update(
            {"relaciones_existentes": LegajosService.obtener_relaciones(legajo)}
        )

        return context

    def form_valid(self, form):
        usuario_eliminacion = self.request.user
        legajo = self.get_object()

        # Graba la data del usuario que realiza la eliminacion en el LOG
        mensaje = (
            f"Legajo borrado - Nombre: {legajo.nombre}, Apellido: {legajo.apellido}, "
            f"Tipo de documento: {legajo.tipo_doc}, Documento: {legajo.documento}"
        )
        logger.info(f"Username: {usuario_eliminacion} - {mensaje}")
        return super().form_valid(form)


class LegajosCreateView(PermisosMixin, CreateView):
    permission_required = ROL_ADMIN
    model = Legajos
    form_class = LegajosForm

    def form_valid(self, form):
        legajo = form.save(commit=False)

        if legajo.foto:
            buffer = recortar_imagen(legajo.foto)
            legajo.foto.save(legajo.foto.name, ContentFile(buffer.getvalue()))

        try:
            with transaction.atomic():
                legajo.save()

                # Crear las dimensiones
                DimensionFamilia.objects.create(fk_legajo_id=legajo.id)
                DimensionVivienda.objects.create(fk_legajo_id=legajo.id)
                DimensionSalud.objects.create(fk_legajo_id=legajo.id)
                DimensionEconomia.objects.create(fk_legajo_id=legajo.id)
                DimensionEducacion.objects.create(fk_legajo_id=legajo.id)
                DimensionTrabajo.objects.create(fk_legajo_id=legajo.id)

            # Redireccionar según el botón presionado
            if "form_legajos" in self.request.POST:
                return redirect("legajos_ver", pk=int(legajo.id))
            elif "form_step2" in self.request.POST:
                return redirect("legajosdimensiones_editar", pk=int(legajo.id))
            return None

        except Exception as e:
            messages.error(
                self.request,
                f"Se produjo un error al crear las dimensiones. Por favor, inténtalo de nuevo. Error: {e}",
            )
            return redirect("legajos_crear")


class LegajosUpdateView(PermisosMixin, UpdateView):
    permission_required = ROL_ADMIN
    model = Legajos
    form_class = LegajosUpdateForm

    def form_valid(self, form):
        legajo = form.save(commit=False)  # Guardamos sin persistir en la base de datos
        current_legajo = self.get_object()

        with transaction.atomic():
            # Comprobamos si se ha cargado una nueva foto y si es diferente de la foto actual
            if legajo.foto and legajo.foto != current_legajo.foto:
                buffer = recortar_imagen(legajo.foto)
                legajo.foto.save(legajo.foto.name, ContentFile(buffer.getvalue()))

            self.object = (
                form.save()
            )  # Guardamos el objeto Legajos con la imagen recortada (si corresponde)

        if "form_legajos" in self.request.POST:
            return redirect("legajos_ver", pk=self.object.id)

        if "form_step2" in self.request.POST:
            return redirect("legajosdimensiones_editar", pk=legajo.id)

        return super().form_valid(form)


# endregion


# region ############################################################### GRUPO FAMILIAR


class LegajosGrupoFamiliarCreateView(CreateView):
    permission_required = ROL_ADMIN
    model = LegajoGrupoFamiliar
    form_class = NuevoLegajoFamiliarForm
    paginate_by = 8  # Número de elementos por página

    def get_context_data(self, **kwargs):
        # Paginación

        context = super().get_context_data(**kwargs)
        pk = self.kwargs["pk"]
        legajo_principal = Legajos.objects.get(pk=pk)
        # Calcula la edad utilizando la función 'edad' del modelo
        edad_calculada = legajo_principal.edad()

        # Verifica si tiene más de 18 años
        es_menor_de_18 = True
        if isinstance(edad_calculada, str) and "años" in edad_calculada:
            edad_num = int(edad_calculada.split()[0])
            if edad_num >= 18:
                es_menor_de_18 = False

        # Verificar si tiene un cuidador principal asignado utilizando el método que agregaste al modelo
        tiene_cuidador_ppal = LegajoGrupoFamiliar.objects.filter(
            fk_legajo_1=legajo_principal, cuidador_principal=True
        ).exists()

        # Obtiene los familiares asociados al legajo principal
        familiares = LegajoGrupoFamiliar.objects.filter(
            Q(fk_legajo_1=pk) | Q(fk_legajo_2=pk)
        ).values(
            "fk_legajo_1__nombre",
            "fk_legajo_1__apellido",
            "fk_legajo_1__id",
            "fk_legajo_1__foto",
            "fk_legajo_2__nombre",
            "fk_legajo_2__apellido",
            "fk_legajo_2__id",
            "fk_legajo_2__foto",
            "vinculo",
            "vinculo_inverso",
        )

        paginator = Paginator(familiares, self.paginate_by)
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context["familiares_fk1"] = [
            familiar for familiar in page_obj if familiar["fk_legajo_1__id"] == int(pk)
        ]
        context["familiares_fk2"] = [
            familiar for familiar in page_obj if familiar["fk_legajo_2__id"] == int(pk)
        ]

        context["familiares"] = page_obj
        context["count_familia"] = familiares.count()
        context["legajo_principal"] = legajo_principal
        context.update(
            {
                "es_menor_de_18": es_menor_de_18,
                "tiene_cuidador_ppal": tiene_cuidador_ppal,
                "pk": pk,
                "id_dimensionfamiliar": DimensionFamilia.objects.get(fk_legajo=pk).id,
            }
        )
        return context

    def form_valid(self, form):
        pk = self.kwargs["pk"]
        vinculo = form.cleaned_data["vinculo"]
        conviven = form.cleaned_data["conviven"]
        estado_relacion = form.cleaned_data["estado_relacion"]
        cuidador_principal = form.cleaned_data["cuidador_principal"]

        # Crea el objeto Legajos
        try:
            nuevo_legajo = form.save()
            DimensionFamilia.objects.create(fk_legajo=nuevo_legajo)
            DimensionVivienda.objects.create(fk_legajo=nuevo_legajo)
            DimensionSalud.objects.create(fk_legajo=nuevo_legajo)
            DimensionEconomia.objects.create(fk_legajo=nuevo_legajo)
            DimensionEducacion.objects.create(fk_legajo=nuevo_legajo)
            DimensionTrabajo.objects.create(fk_legajo=nuevo_legajo)
        except Exception as e:
            return messages.error(
                self.request,
                f"Verifique que no exista un legajo con ese DNI y NÚMERO. Error: {e}",
            )

        # Crea el objeto LegajoGrupoFamiliar con los valores del formulario
        vinculo_data = VINCULO_MAP.get(vinculo)
        if not vinculo_data:
            return messages.error(self.request, "Vinculo inválido.")

        # crea la relacion de grupo familiar
        legajo_principal = Legajos.objects.get(id=pk)
        try:
            LegajoGrupoFamiliar.objects.create(
                fk_legajo_1=legajo_principal,
                fk_legajo_2=nuevo_legajo,
                vinculo=vinculo_data["vinculo"],
                vinculo_inverso=vinculo_data["vinculo_inverso"],
                conviven=conviven,
                estado_relacion=estado_relacion,
                cuidador_principal=cuidador_principal,
            )

        except Exception as e:
            return messages.error(
                self.request,
                f"Verifique que no exista un legajo con ese DNI y NÚMERO. Error: {e}",
            )

        messages.success(self.request, "Familair agregado correctamente.")
        # Redireccionar a la misma página después de realizar la acción con éxito
        return HttpResponseRedirect(self.request.path_info)


def busqueda_familiares(request):
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        res = None
        busqueda = request.POST.get("busqueda")
        legajo_principal_id = request.POST.get("id")
        page_number = request.POST.get("page", 1)

        legajos_asociados = LegajoGrupoFamiliar.objects.filter(
            Q(fk_legajo_1_id=legajo_principal_id)
            | Q(fk_legajo_2_id=legajo_principal_id)
        ).values_list("fk_legajo_1_id", "fk_legajo_2_id")

        legajos_asociados_ids = set()
        for fk_legajo_1_id, fk_legajo_2_id in legajos_asociados:
            if fk_legajo_1_id != legajo_principal_id:
                legajos_asociados_ids.add(fk_legajo_1_id)
            if fk_legajo_2_id != legajo_principal_id:
                legajos_asociados_ids.add(fk_legajo_2_id)

        paginate_by = 10
        familiares = Legajos.objects.filter(
            ~Q(id=legajo_principal_id)
            & (Q(apellido__icontains=busqueda) | Q(documento__icontains=busqueda))
        ).exclude(id__in=legajos_asociados_ids)

        if len(familiares) > 0 and busqueda:
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
                    "tipo_doc": familiar.tipo_doc,
                    "fecha_nacimiento": familiar.fecha_nacimiento,
                    "sexo": familiar.sexo,
                    # Otros campos que deseas incluir
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

    return JsonResponse({"data": "this is data"})


class LegajoGrupoFamiliarList(ListView):
    model = LegajoGrupoFamiliar

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        context["familiares_fk1"] = LegajoGrupoFamiliar.objects.filter(fk_legajo_1=pk)
        context["familiares_fk2"] = LegajoGrupoFamiliar.objects.filter(fk_legajo_2=pk)
        context["count_familia"] = (
            context["familiares_fk1"].count() + context["familiares_fk1"].count()
        )
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
            "mensaje": "Vínculo familiar agregado correctamente.",
        }

        return JsonResponse({"familiar": familiar, "data": data})


class DeleteGrupoFamiliar(View):
    def get(self, request):
        pk = request.GET.get("id", None)
        try:
            familiar = get_object_or_404(LegajoGrupoFamiliar, pk=pk)
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


# endregion


# region ############################################################### DERIVACIONES


class LegajosDerivacionesBuscar(PermisosMixin, TemplateView):
    permission_required = ROL_ADMIN
    template_name = "legajos/legajosderivaciones_buscar.html"

    def get(self, request, *args, **kwargs):  # pylint: disable=too-many-locals
        context = self.get_context_data(**kwargs)
        legajos = cache.get("legajos")
        derivaciones = cache.get("derivaciones")
        con_derivaciones = cache.get("con_derivaciones")
        sin_derivaciones = cache.get("sin_derivaciones")

        if not legajos:
            legajos = Legajos.objects.all()
            cache.set("legajos", legajos, 60)
        if not derivaciones:
            derivaciones = LegajosDerivaciones.objects.all()
            cache.set("derivaciones", derivaciones, 60)
        if not con_derivaciones:
            con_derivaciones = LegajosDerivaciones.objects.none()
            cache.set("con_derivaciones", con_derivaciones, 60)
        if not sin_derivaciones:
            sin_derivaciones = Legajos.objects.none()
            cache.set("sin_derivaciones", sin_derivaciones, 60)

        barrios = legajos.values_list("barrio")
        circuitos = CHOICE_CIRCUITOS
        localidad = CHOICE_NACIONALIDAD
        mostrar_resultados = False
        mostrar_btn_resetear = False
        query = self.request.GET.get("busqueda")
        if query:
            derivaciones_filtrado = (
                derivaciones.filter(
                    Q(fk_legajo__apellido__icontains=query)
                    | Q(fk_legajo__documento__icontains=query)
                )
                .values("fk_legajo")
                .distinct()
            )
            legajos_filtrado = legajos.filter(
                Q(apellido__icontains=query) | Q(documento__icontains=query)
            ).distinct()

            if derivaciones_filtrado:
                sin_derivaciones = legajos_filtrado.exclude(
                    id__in=derivaciones_filtrado
                )
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
    permission_required = ROL_ADMIN
    model = LegajosDerivaciones
    paginate_by = 25

    def get_context_data(self, **kwargs):
        context = super(LegajosDerivacionesListView, self).get_context_data(**kwargs)

        model = cache.get("model")
        if not model:
            model = LegajosDerivaciones.objects.all()
            cache.set("model", model, 60)

        context["pendientes"] = model.filter(estado="Pendiente")
        context["aceptadas"] = model.filter(estado="Aceptada")
        context["analisis"] = model.filter(estado="En análisis")
        context["asesoradas"] = model.filter(estado="Asesoramiento")
        context["enviadas"] = model.filter(fk_usuario=self.request.user)
        return context

    # Funcion de busqueda

    def get_queryset(self):
        model = cache.get("model")
        if model is None:
            model = LegajosDerivaciones.objects.all()
            cache.set("model", model, 60)

        query = self.request.GET.get("busqueda")

        if query:
            object_list = model.filter(
                Q(fk_legajo__apellido__icontains=query)
                | Q(fk_legajo__documento__icontains=query)
            ).distinct()

        else:
            object_list = model.all()

        return object_list.order_by("-estado")


class LegajosDerivacionesCreateView(PermisosMixin, CreateView):
    permission_required = ROL_ADMIN
    model = LegajosDerivaciones
    form_class = LegajosDerivacionesForm
    success_message = "Derivación registrada con éxito"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        pk = self.kwargs.get("pk")

        if pk:
            # excluyo los programas que ya tienen derivaciones en curso para este legajo (solo dejo fuera las 'asesoradas')

            programas = Programas.objects.all().exclude(
                id__in=LegajosDerivaciones.objects.filter(fk_legajo=pk)
                .exclude(estado__in=["Rechazada", "Finalizada"])
                .values_list("fk_programa", flat=True)
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
    permission_required = ROL_ADMIN
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
    permission_required = ROL_ADMIN
    model = LegajosDerivaciones
    template_name = "legajos/legajosderivaciones_historial.html"

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
    permission_required = ROL_ADMIN
    model = LegajosDerivaciones

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
    permission_required = ROL_ADMIN
    model = LegajosDerivaciones


# endregion


# region ############################################################### ALERTAS


class LegajosAlertasListView(PermisosMixin, ListView):
    permission_required = ROL_ADMIN
    model = HistorialLegajoAlertas
    template_name = "legajos/legajoalertas_list.html"

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        context["legajo_alertas"] = HistorialLegajoAlertas.objects.filter(fk_legajo=pk)
        context["legajo"] = (
            Legajos.objects.filter(id=pk).values("apellido", "nombre", "id").first()
        )
        return context


class LegajosAlertasCreateView(PermisosMixin, SuccessMessageMixin, CreateView):
    permission_required = ROL_ADMIN
    model = LegajoAlertas
    form_class = LegajosAlertasForm
    success_message = "Alerta asignada correctamente."

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        context = super().get_context_data(**kwargs)

        alertas = LegajoAlertas.objects.filter(fk_legajo=pk)

        legajo = Legajos.objects.values("pk", "dimensionfamilia__id").get(pk=pk)

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
    permission_required = ROL_ADMIN

    def get(self, request):
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
            categorias = CategoriaAlertas.objects.filter(alertas__id=alerta_id)
        else:
            categorias = CategoriaAlertas.objects.all()

        data = [
            {"id": categoria.id, "text": categoria.nombre} for categoria in categorias
        ]
        return JsonResponse(data, safe=False)


class AlertasSelectView(View):
    def get(self, request, *args, **kwargs):
        categoria_id = request.GET.get("categoria_id")
        if categoria_id:
            alertas = Alertas.objects.filter(fk_categoria_id=categoria_id)
        else:
            alertas = Alertas.objects.all()

        data = [{"id": alerta.id, "text": alerta.nombre} for alerta in alertas]
        return JsonResponse(data, safe=False)


# endregion


# region ############################################################### DIMENSIONES


class DimensionesUpdateView(PermisosMixin, SuccessMessageMixin, UpdateView):
    # FIXME: Crear updateView por cada formulario
    permission_required = ROL_ADMIN
    template_name = "legajos/legajosdimensiones_form.html"
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
        legajo = Legajos.objects.only("id").get(id=pk)
        return DimensionFamilia.objects.get(fk_legajo=legajo.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        pk = self.kwargs["pk"]
        legajo = (
            Legajos.objects.select_related(
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
                "dimensionvivienda__fk_legajo",
                "dimensionvivienda__obs_vivienda",
                "dimensionsalud__fk_legajo",
                "dimensionsalud__obs_salud",
                "dimensionsalud__hay_obra_social",
                "dimensionsalud__hay_enfermedad",
                "dimensionsalud__hay_discapacidad",
                "dimensionsalud__hay_cud",
                "dimensioneducacion__fk_legajo",
                "dimensioneducacion__obs_educacion",
                "dimensioneducacion__areaCurso",
                "dimensioneducacion__areaOficio",
                "dimensioneconomia__fk_legajo",
                "dimensioneconomia__obs_economia",
                "dimensioneconomia__m2m_planes",
                "dimensiontrabajo__fk_legajo",
                "dimensiontrabajo__obs_trabajo",
            )
            .get(id=pk)
        )

        # TODO: Modificar logica para no utilizar los siguientes "None' y crear la dimension segun haga falta
        context.update(
            {
                "legajo": legajo,
                "form_vivienda": self.form_vivienda(
                    instance=getattr(legajo, "dimensionvivienda", None)
                ),
                "form_salud": self.form_salud(
                    instance=getattr(legajo, "dimensionsalud", None)
                ),
                "form_educacion": self.form_educacion(
                    instance=getattr(legajo, "dimensioneducacion", None)
                ),
                "form_economia": self.form_economia(
                    instance=getattr(legajo, "dimensioneconomia", None)
                ),
                "form_trabajo": self.form_trabajo(
                    instance=getattr(legajo, "dimensiontrabajo", None)
                ),
            }
        )

        return context

    def form_valid(  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        self, form
    ):
        # TODO: Esto sera refactorizado
        self.object = form.save(commit=False)

        pk = self.kwargs["pk"]

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
            "PoseenCeludar": "PoseenCeludar",
            "PoseenPC": "PoseenPC",
            "Poseeninternet": "Poseeninternet",
            "ContextoCasa": "ContextoCasa",
            "CondicionDe": "CondicionDe",
            "CantidadAmbientes": "CantidadAmbientes",
            "gas": "gas",
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
            "oficio": "oficio",
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
            "noBusquedaLaboral": "noBusquedaLaboral",
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
    permission_required = ROL_ADMIN
    model = Legajos
    template_name = "legajos/legajosdimensiones_detail.html"


# endregion


# region ################################################################ ARCHIVOS
class LegajosArchivosListView(PermisosMixin, ListView):
    permission_required = ROL_ADMIN
    model = LegajosArchivos
    template_name = "legajos/legajosarchivos_list.html"

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        context["legajo_archivos"] = LegajosArchivos.objects.filter(fk_legajo=pk)
        context["legajo"] = Legajos.objects.filter(id=pk).first()
        return context


class LegajosArchivosCreateView(PermisosMixin, SuccessMessageMixin, CreateView):
    permission_required = ROL_ADMIN
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

                legajo_archivo = LegajosArchivos.objects.create(
                    fk_legajo=legajo, archivo=f, tipo=tipo
                )

                response_data = {
                    "id": legajo_archivo.id,
                    "tipo": legajo_archivo.tipo,
                    "archivo_url": legajo_archivo.archivo.url,
                }

                response_data_list.append(
                    response_data
                )  # Agregar la respuesta actual a la lista

        return JsonResponse(
            response_data_list, safe=False
        )  # Devolver la lista completa de respuestas como JSON


class DeleteArchivo(PermisosMixin, View):
    permission_required = ROL_ADMIN

    def get(self, request):
        try:
            pk = request.GET.get("id", None)
            legajo_archivo = get_object_or_404(LegajosArchivos, pk=pk)
            legajo_archivo.delete()

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


class ProgramasIntervencionesView(TemplateView):
    template_name = "legajos/programas_intervencion.html"
    model = Legajos

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        legajo = Legajos.objects.filter(pk=self.kwargs["pk"]).first()

        context["legajo"] = legajo

        return context


class AccionesSocialesView(TemplateView):
    template_name = "legajos/acciones_sociales.html"
    model = Legajos

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        legajo_id = self.kwargs["pk"]

        legajo = Legajos.objects.only(
            "apellido",
            "nombre",
            "id",
            "tipo_doc",
            "documento",
            "fecha_nacimiento",
            "sexo",
        ).get(pk=legajo_id)

        context["legajo"] = legajo

        return context


class IntervencionesSaludView(TemplateView):
    template_name = "legajos/intervenciones_salud.html"
    model = Legajos

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        legajo = Legajos.objects.filter(pk=self.kwargs["pk"]).first()

        context["legajo"] = legajo

        return context


class IndicesView(TemplateView):
    template_name = "legajos/indices.html"
    model = Legajos

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        legajo = Legajos.objects.filter(pk=self.kwargs["pk"]).first()

        context["legajo"] = legajo

        return context


class IndicesDetalleView(TemplateView):
    template_name = "legajos/indices_detalle.html"
    model = Legajos

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        legajo = Legajos.objects.filter(pk=self.kwargs["pk"]).first()

        context["legajo"] = legajo

        return context


# endregion ###########################################################

# region ############################################################### GRUPO Hogar


class LegajosGrupoHogarCreateView(CreateView):
    permission_required = ROL_ADMIN
    model = LegajoGrupoHogar
    form_class = LegajoGrupoHogarForm
    paginate_by = 8

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        legajo_principal = Legajos.objects.filter(pk=pk).first()

        context = super().get_context_data(**kwargs)

        hogares = LegajoGrupoHogar.objects.filter(
            Q(fk_legajo_1Hogar=pk) | Q(fk_legajo_2Hogar=pk)
        ).values(
            "fk_legajo_1Hogar__nombre",
            "fk_legajo_2Hogar__nombre",
            "fk_legajo_1Hogar__apellido",
            "fk_legajo_2Hogar__apellido",
            "fk_legajo_1Hogar__foto",
            "fk_legajo_2Hogar__foto",
            "fk_legajo_1Hogar__id",
            "fk_legajo_2Hogar__id",
        )

        # Paginacion

        paginator = Paginator(hogares, self.paginate_by)
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context["hogar_1"] = [
            familiar
            for familiar in page_obj
            if familiar["fk_legajo_1Hogar__id"] == int(pk)
        ]
        context["hogar_2"] = [
            familiar
            for familiar in page_obj
            if familiar["fk_legajo_2Hogar__id"] == int(pk)
        ]
        print(context["hogar_1"])

        context["hogares"] = page_obj
        context["count_hogar"] = hogares.count()
        context["legajo_principal"] = legajo_principal
        context["pk"] = pk

        return context

    def form_valid(self, form):
        pk = self.kwargs["pk"]
        estado_relacion = form.cleaned_data["estado_relacion"]

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
        except Exception as e:
            return messages.error(
                self.request,
                f"Verifique que no exista un legajo con ese DNI y NÚMERO. Error: {e}",
            )

        # Crea el objeto LegajoGrupoFamiliar con los valores del formulario
        # vinculo_data = VINCULO_MAP.get(vinculo)
        # if not vinculo_data:
        #   return messages.error(self.request, "Vinculo inválido.")

        # crea la relacion de grupo familiar
        legajo_principal = Legajos.objects.get(id=pk)
        try:
            LegajoGrupoFamiliar.objects.create(
                fk_legajo_1=legajo_principal,
                fk_legajo_2=nuevo_legajo,
                #  vinculo=vinculo_data["vinculo"],
                # vinculo_inverso=vinculo_data["vinculo_inverso"],
                estado_relacion=estado_relacion,
            )
        except Exception as e:
            return messages.error(
                self.request,
                f"Verifique que no exista un legajo con ese DNI y NÚMERO. {e}",
            )

        messages.success(self.request, "Familair agregado correctamente.")
        # Redireccionar a la misma página después de realizar la acción con éxito
        return HttpResponseRedirect(self.request.path_info)


def busqueda_hogar(request):
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        res = None
        busqueda = request.POST.get("busqueda")
        legajo_principal_id = request.POST.get("id")
        page_number = request.POST.get("page", 1)

        legajos_asociados = LegajoGrupoHogar.objects.filter(
            Q(fk_legajo_1Hogar_id=legajo_principal_id)
            | Q(fk_legajo_2Hogar_id=legajo_principal_id)
        ).values_list("fk_legajo_1Hogar_id", "fk_legajo_2Hogar_id")

        legajos_asociados_ids = set()
        for fk_legajo_1hogar_id, fk_legajo_2hogar_id in legajos_asociados:
            if fk_legajo_1hogar_id != legajo_principal_id:
                legajos_asociados_ids.add(fk_legajo_1hogar_id)
            if fk_legajo_2hogar_id != legajo_principal_id:
                legajos_asociados_ids.add(fk_legajo_2hogar_id)

        paginate_by = 10
        hogares = Legajos.objects.filter(
            ~Q(id=legajo_principal_id)
            & (Q(apellido__icontains=busqueda) | Q(documento__icontains=busqueda))
        ).exclude(id__in=legajos_asociados_ids)

        if len(hogares) > 0 and busqueda:
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
                    "tipo_doc": hogar.tipo_doc,
                    "fecha_nacimiento": hogar.fecha_nacimiento,
                    "sexo": hogar.sexo,
                    # Otros campos que deseas incluir
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

    return JsonResponse({"data": "this is data"})


class LegajoGrupoHogarList(ListView):
    model = LegajoGrupoFamiliar

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        context = super().get_context_data(**kwargs)

        # FIXME: Esta query optimizada de "familiares" no se termino de implementar
        familiares = LegajoGrupoFamiliar.objects.filter(
            Q(fk_legajo_1=pk) | Q(fk_legajo_2=pk)
        ).values(
            "fk_legajo2__id",
            "fk_legajo1__id",
            "fk_legajo_2__nombre",
            "fk_legajo_2__apellido",
            "fk_legajo_2__calle",
            "fk_legajo_2__telefono",
            "estado_relacion",
            "conviven",
            "cuidado_principal",
            "fk_legajo_2__foto",
            "fk_legajo_1__nombre",
            "fk_legajo_1__apellido",
            "fk_legajo_1__calle",
            "fk_legajo_1__telefono",
            "estado_relacion",
            "conviven",
            "cuidado_principal",
            "fk_legajo_1__foto",
            "vinculo",
        )
        context["familiares_fk1"] = [
            familiar
            for familiar in familiares
            if familiar["fk_legajo_1__id"] == int(pk)
        ]
        context["familiares_fk2"] = [
            familiar
            for familiar in familiares
            if familiar["fk_legajo_1__id"] == int(pk)
        ]
        context["count_familia"] = (
            context["familiares_fk1"].count() + context["familiares_fk1"].count()
        )
        context["nombre"] = Legajos.objects.filter(pk=pk).values("nombre").first()
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
            "foto": (
                obj.fk_legajo_2Hogar.foto.url if obj.fk_legajo_2Hogar.foto else None
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
            familiar = get_object_or_404(LegajoGrupoHogar, pk=pk)
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
