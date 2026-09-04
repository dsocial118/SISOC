from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db.models import Exists, OuterRef, Q
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)
from django.views.generic import View
from django.views.generic.edit import FormView

from core.models import Municipio
from core.pagination import NoCountPaginator, build_no_count_page_range
from pas.favorite_filters import PAS_FILTER_SECTION
from pas.forms import (
    PasCambioEstadoForm,
    PasDeclaracionJuradaForm,
    PasInformeGenerarForm,
    PasPersonaCreateForm,
    PasPersonaUpdateForm,
    PasRetornoSintysForm,
    PasTitularesImportForm,
)
from pas.models import (
    PasAviso,
    PasDeclaracionJurada,
    PasEstado,
    PasIncompatibilidad,
    PasInforme,
    PasPersona,
    PasInvitacionDDJJ,
)
from pas.services.ddjj_service import presentar_ddjj
from pas.services.filter_config import get_filters_ui_config
from pas.services.formacion_service import (
    paginar_personas_formacion,
    preparar_personas_formacion,
    obtener_formacion_persona,
    resumir_formacion,
)
from pas.services.cruces_service import (
    construir_etapas,
    obtener_circuito_actual,
    registrar_exportacion_sintys,
    registrar_importacion_sintys,
)
from pas.services.informe_service import (
    buscar_informes,
    csv_response_for_informe,
    errors_payload,
    generar_informe_pas,
    preview_payload,
)
from pas.services.persona_service import (
    cambiar_estado,
    get_personas_filtradas,
    registrar_persona,
)
from pas.services.titulares_import_service import (
    generar_excel_tokens_vigentes,
    importar_titulares_csv,
)
from pas.services.supervivencia_service import (
    resumen_supervivencia,
    sincronizar_supervivencia_pas,
)


def _breadcrumb(actual):
    return [
        {"text": "PAS", "url": reverse("pas_persona_listar")},
        {"text": actual, "active": True},
    ]


def _breadcrumb_informes(actual):
    return [
        {"text": "PAS", "url": reverse("pas_persona_listar")},
        {"text": "Informes", "url": reverse("pas_informe_listar")},
        {"text": actual, "active": True},
    ]


def _avisos_por_estado():
    avisos = PasAviso.objects.prefetch_related("estados").order_by("codigo")
    data = {}
    for aviso in avisos:
        option = {"id": aviso.id, "text": str(aviso)}
        for estado in aviso.estados.all():
            data.setdefault(str(estado.id), []).append(option)
    return data


PAS_AREAS = (
    {
        "key": "panel",
        "number": "01",
        "title": "Panel de Control",
        "subtitle": "Titulares y ABM",
        "url_name": "pas_panel_control",
        "source_status": "disponible",
    },
    {
        "key": "formacion",
        "number": "02",
        "title": "Formación FCH",
        "subtitle": "Condicionalidad",
        "url_name": "pas_formacion",
        "source_status": "disponible",
    },
    {
        "key": "cruces",
        "number": "03",
        "title": "Cruces y Novedades",
        "subtitle": "Incompatibilidades",
        "url_name": "pas_cruces",
        "source_status": "disponible",
    },
    {
        "key": "mesa-ayuda",
        "number": "04",
        "title": "Mesa de Ayuda",
        "subtitle": "Reclamos y atención",
        "url_name": "pas_mesa_ayuda",
        "source_status": "pendiente",
    },
    {
        "key": "liquidacion",
        "number": "05",
        "title": "Liquidación",
        "subtitle": "Nómina de pago",
        "url_name": "pas_liquidacion",
        "source_status": "pendiente",
    },
)


def _pas_areas(active, persona=None):
    areas = []
    for area in PAS_AREAS:
        url = reverse(area["url_name"])
        if persona:
            if area["key"] == "panel":
                url = reverse("pas_panel_control_persona", kwargs={"pk": persona.pk})
            elif area["key"] == "formacion":
                url = f"{url}?persona={persona.pk}"
        areas.append(dict(area, active=area["key"] == active, url=url))
    return areas


class PasPersonaListView(LoginRequiredMixin, ListView):
    model = PasPersona
    template_name = "pas/persona_list.html"
    context_object_name = "personas"
    paginate_by = 10

    def get_queryset(self):
        return get_personas_filtradas(self.request)

    def paginate_queryset(self, queryset, page_size):
        paginator = NoCountPaginator(queryset, page_size)
        page_obj = paginator.get_page(self.request.GET.get(self.page_kwarg))
        object_list = page_obj.object_list
        return paginator, page_obj, object_list, page_obj.has_other_pages()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "breadcrumb_items": _breadcrumb("Listar"),
                "titulo": "Buscador PAS",
                "reset_url": reverse("pas_persona_listar"),
                "reset_url_full": reverse("pas_persona_listar"),
                "add_url": reverse("pas_persona_crear"),
                "add_url_full": reverse("pas_persona_crear"),
                "add_text": "Crear registro",
                "filters_mode": True,
                "filters_js": "custom/js/advanced_filters.js",
                "filters_action": reverse("pas_persona_listar"),
                "filters_config": get_filters_ui_config(),
                "seccion_filtros_favoritos": PAS_FILTER_SECTION,
                "query": self.request.GET.get("q", ""),
                "estado_seleccionado": self.request.GET.get("estado", ""),
                "estados_pas": PasEstado.objects.order_by("nombre"),
                "pas_areas": _pas_areas("panel"),
                "total_padron": PasPersona.objects.count(),
            }
        )
        page_obj = context.get("page_obj")
        if page_obj and getattr(page_obj.paginator, "count", None) is None:
            context["page_range"] = build_no_count_page_range(page_obj)
        return context


class PasPersonaCreateView(LoginRequiredMixin, CreateView):
    model = PasPersona
    form_class = PasPersonaCreateForm
    template_name = "pas/persona_form.html"

    def form_valid(self, form):
        self.object = registrar_persona(form, usuario=self.request.user)
        messages.success(self.request, "Registro PAS creado correctamente.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("pas_panel_control_persona", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "breadcrumb_items": _breadcrumb("Crear"),
                "titulo_formulario": "Crear registro PAS",
                "volver_url": reverse("pas_persona_listar"),
                "avisos_por_estado": _avisos_por_estado(),
                "mostrar_estado": True,
            }
        )
        return context


class PasTitularesImportView(LoginRequiredMixin, FormView):
    template_name = "pas/titulares_import.html"
    form_class = PasTitularesImportForm

    def form_valid(self, form):
        try:
            resultado = importar_titulares_csv(
                form.cleaned_data["archivo"], usuario=self.request.user
            )
        except ValidationError as exc:
            form.add_error("archivo", exc)
            return self.form_invalid(form)
        context = self.get_context_data(form=PasTitularesImportForm())
        context["resultado"] = resultado
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = _breadcrumb("Importar titulares")
        return context


class PasTokensExportView(LoginRequiredMixin, View):
    def get(self, request):
        contenido = generar_excel_tokens_vigentes(usuario=request.user)
        response = HttpResponse(
            contenido,
            content_type=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
        )
        response["Content-Disposition"] = (
            'attachment; filename="pas_tokens_ddjj_vigentes.xlsx"'
        )
        return response


class PasPersonaDetailView(LoginRequiredMixin, DetailView):
    model = PasPersona
    template_name = "pas/persona_detail.html"
    context_object_name = "persona"

    def get_queryset(self):
        return (
            PasPersona.objects.select_related("provincia", "municipio", "estado")
            .prefetch_related(
                "avisos",
                "historial_estados__avisos_anteriores",
                "historial_estados__avisos_nuevos",
                "historial_estados__estado_anterior",
                "historial_estados__estado_nuevo",
                "historial_estados__usuario",
                "declaraciones_juradas",
            )
            .all()
        )

    def get_object(self, queryset=None):
        queryset = queryset or self.get_queryset()
        persona_id = self.kwargs.get("pk")
        if persona_id:
            return get_object_or_404(queryset, pk=persona_id)
        return queryset.first()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        declaraciones = (
            list(self.object.declaraciones_juradas.all()) if self.object else []
        )
        declaracion_id = self.request.GET.get("ddjj")
        declaracion_seleccionada = next(
            (
                declaracion
                for declaracion in declaraciones
                if str(declaracion.pk) == declaracion_id
            ),
            declaraciones[0] if declaraciones else None,
        )
        eventos_historial = [
            {
                "tipo": "estado",
                "fecha": item.fecha_cambio,
                "objeto": item,
            }
            for item in (self.object.historial_estados.all() if self.object else [])
        ]
        eventos_historial.extend(
            {
                "tipo": "ddjj",
                "fecha": declaracion.presentada,
                "objeto": declaracion,
            }
            for declaracion in declaraciones
        )
        eventos_historial.sort(key=lambda evento: evento["fecha"], reverse=True)
        ddjj_completa = PasDeclaracionJurada.objects.filter(
            persona_id=OuterRef("pk"),
            finalizada__isnull=False,
        )
        query = (self.request.GET.get("q") or "").strip()
        estado_actual = self.request.GET.get("estado_actual") or "todos"
        personas_panel_queryset = PasPersona.objects.select_related(
            "provincia", "municipio", "estado"
        ).annotate(
            ddjj_completa=Exists(ddjj_completa),
        )
        if query:
            personas_panel_queryset = personas_panel_queryset.filter(
                Q(nombres__icontains=query)
                | Q(apellidos__icontains=query)
                | Q(cuit__icontains=query)
            )
        if estado_actual.isdigit():
            personas_panel_queryset = personas_panel_queryset.filter(
                estado_id=int(estado_actual)
            )
        personas_panel = list(
            personas_panel_queryset.order_by("apellidos", "nombres", "id")[:100]
        )
        for item in personas_panel:
            item.mostrar_tag_ddjj = not item.ddjj_completa
            item.mostrar_tag_fch = False
        context.update(
            {
                "persona": self.object,
                "personas_panel": personas_panel,
                "breadcrumb_items": _breadcrumb("Panel de Control"),
                "cambio_estado_form": PasCambioEstadoForm(),
                "avisos_por_estado": _avisos_por_estado(),
                "pas_areas": _pas_areas("panel", self.object),
                "query": query,
                "estado_actual": estado_actual,
                "estados_panel": PasEstado.objects.order_by("nombre"),
                "formaciones_pas": obtener_formacion_persona(self.object),
                "declaraciones_juradas": declaraciones,
                "declaracion_seleccionada": declaracion_seleccionada,
                "eventos_historial": eventos_historial,
            }
        )
        return context


class PasDDJJFormularioView(View):
    template_name = "pas/ddjj_formulario.html"

    def _invitacion(self, token):
        return get_object_or_404(
            PasInvitacionDDJJ.objects.select_related(
                "persona", "persona__provincia", "persona__municipio"
            ),
            token=token,
        )

    def get(self, request, token):
        invitacion = self._invitacion(token)
        if not invitacion.disponible:
            return HttpResponse(
                "Este enlace ya fue utilizado o se encuentra vencido.", status=410
            )
        return self._render(
            request, invitacion, PasDeclaracionJuradaForm(persona=invitacion.persona)
        )

    def post(self, request, token):
        invitacion = self._invitacion(token)
        if not invitacion.disponible:
            return HttpResponse(
                "Este enlace ya fue utilizado o se encuentra vencido.", status=410
            )
        form = PasDeclaracionJuradaForm(request.POST, persona=invitacion.persona)
        if not form.is_valid():
            return self._render(request, invitacion, form, status=400)
        try:
            presentar_ddjj(invitacion, form)
        except ValueError:
            return HttpResponse(
                "Este enlace ya fue utilizado o se encuentra vencido.", status=410
            )
        return redirect("pas_ddjj_confirmacion")

    def _render(self, request, invitacion, form, status=200):
        from django.shortcuts import render

        return render(
            request,
            self.template_name,
            {"invitacion": invitacion, "persona": invitacion.persona, "form": form},
            status=status,
        )


class PasDDJJMunicipiosView(View):
    def get(self, request, token):
        invitacion = get_object_or_404(PasInvitacionDDJJ, token=token)
        if not invitacion.disponible:
            return JsonResponse({"detalle": "Invitacion no disponible."}, status=410)
        provincia_id = request.GET.get("provincia_id")
        if not provincia_id or not provincia_id.isdigit():
            return JsonResponse([], safe=False)
        municipios = (
            Municipio.objects.filter(provincia_id=provincia_id)
            .order_by("nombre")
            .values("id", "nombre")
        )
        return JsonResponse(list(municipios), safe=False)


class PasDDJJConfirmacionView(TemplateView):
    template_name = "pas/ddjj_confirmacion.html"


class PasDDJJPrivateMediaView(View):
    """Impide que los PDF DDJJ evadan la descarga autenticada."""

    def get(self, request, path):
        raise Http404("Archivo no disponible por acceso directo.")


class PasDDJJDownloadView(LoginRequiredMixin, View):
    def get(self, request, pk):
        declaracion = get_object_or_404(
            PasDeclaracionJurada.objects.select_related("persona"), pk=pk
        )
        if not declaracion.archivo_pdf:
            raise Http404("La DDJJ no tiene un PDF asociado.")
        return FileResponse(
            declaracion.archivo_pdf.open("rb"),
            as_attachment=True,
            filename=(
                f"DDJJ_PAS_{declaracion.persona.dni}" f"_v{declaracion.version}.pdf"
            ),
            content_type="application/pdf",
        )


class PasCrucesView(LoginRequiredMixin, TemplateView):
    template_name = "pas/area.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        circuito = obtener_circuito_actual()
        context.update(
            {
                "breadcrumb_items": [
                    {"text": "PAS"},
                    {"text": "Cruces y novedades", "active": True},
                ],
                "area": next(area for area in PAS_AREAS if area["key"] == "cruces"),
                "area_key": "cruces",
                "pas_areas": _pas_areas("cruces"),
                "total_padron": PasPersona.objects.count(),
                "circuito": circuito,
                "etapas_circuito": construir_etapas(circuito),
                "retorno_sintys_form": PasRetornoSintysForm(),
                "resumen_renaper": resumen_supervivencia(),
                "incompatibilidades": list(
                    PasIncompatibilidad.objects.select_related("persona")
                    .filter(estado=PasIncompatibilidad.Estado.PENDIENTE)
                    .order_by("-fecha_deteccion")[:100]
                ),
            }
        )
        return context


class PasAreaView(LoginRequiredMixin, TemplateView):
    template_name = "pas/area.html"
    area_key = None

    def get_context_data(self, **kwargs):
        # La vista compone datos de presentación del padrón y del detalle seleccionado.
        # pylint: disable=too-many-locals
        context = super().get_context_data(**kwargs)
        area = next(item for item in PAS_AREAS if item["key"] == self.area_key)
        persona_seleccionada = None
        formaciones_pas = []
        resumen_formacion = None
        personas_formacion = []
        pagina_formacion = None
        persona_solicitada = None
        if self.area_key == "formacion":
            persona_id = self.request.GET.get("persona")
            if persona_id and persona_id.isdigit():
                persona_solicitada = (
                    PasPersona.objects.select_related("estado")
                    .filter(pk=int(persona_id))
                    .first()
                )
            query = (self.request.GET.get("q") or "").strip()
            estado_formacion = self.request.GET.get("estado_formacion") or "todos"
            excluir_id = persona_solicitada.pk if persona_solicitada else None
            pagina_formacion = paginar_personas_formacion(
                query=query,
                estado_formacion=estado_formacion,
                pagina=1,
                excluir_id=excluir_id,
            )
            personas_formacion = preparar_personas_formacion(
                pagina_formacion.object_list
            )
            if persona_solicitada:
                persona_seleccionada = preparar_personas_formacion(
                    [persona_solicitada]
                )[0]
                personas_formacion.insert(0, persona_seleccionada)
            persona_seleccionada = persona_seleccionada or next(
                iter(personas_formacion),
                None,
            )
            formaciones_pas = obtener_formacion_persona(persona_seleccionada)
            resumen_formacion = resumir_formacion(formaciones_pas)
        context.update(
            {
                "area": area,
                "area_key": self.area_key,
                "pas_areas": _pas_areas(self.area_key, persona_seleccionada),
                "personas": personas_formacion,
                "persona_seleccionada": persona_seleccionada,
                "formaciones_pas": formaciones_pas,
                "resumen_formacion": resumen_formacion,
                "query": self.request.GET.get("q", ""),
                "estado_formacion": self.request.GET.get("estado_formacion", "todos"),
                "pagina_formacion": pagina_formacion,
                "formacion_personas_url": reverse("pas_formacion_personas"),
                "persona_solicitada_id": (
                    persona_solicitada.pk if persona_solicitada else ""
                ),
                "total_padron": PasPersona.objects.count(),
            }
        )
        return context


class PasFormacionPersonasView(LoginRequiredMixin, View):
    """Entrega páginas HTML para el scroll incremental de titulares."""

    def get(self, request):
        query = (request.GET.get("q") or "").strip()
        estado_formacion = request.GET.get("estado_formacion") or "todos"
        persona_id = request.GET.get("persona")
        excluir_id = int(persona_id) if persona_id and persona_id.isdigit() else None
        pagina = paginar_personas_formacion(
            query=query,
            estado_formacion=estado_formacion,
            pagina=request.GET.get("page", 1),
            excluir_id=excluir_id,
        )
        personas = preparar_personas_formacion(pagina.object_list)
        html = render_to_string(
            "pas/includes/formacion_personas.html",
            {
                "personas": personas,
                "persona_seleccionada_id": excluir_id,
                "query": query,
                "estado_formacion": estado_formacion,
            },
            request=request,
        )
        return JsonResponse(
            {
                "html": html,
                "has_next": pagina.has_next(),
                "next_page": pagina.next_page_number() if pagina.has_next() else None,
            }
        )


class PasCrucesExportarSintysView(LoginRequiredMixin, View):
    def post(self, request):
        circuito = obtener_circuito_actual(crear=True)
        contenido, nombre = registrar_exportacion_sintys(circuito, request.user)
        response = HttpResponse(
            contenido,
            content_type=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
        )
        response["Content-Disposition"] = f'attachment; filename="{nombre}"'
        return response


class PasCrucesImportarSintysView(LoginRequiredMixin, View):
    def post(self, request):
        form = PasRetornoSintysForm(request.POST, request.FILES)
        if not form.is_valid():
            messages.error(
                request,
                "No se pudo importar el retorno: "
                + " ".join(
                    error for errores in form.errors.values() for error in errores
                ),
            )
            return redirect("pas_cruces")

        registrar_importacion_sintys(
            obtener_circuito_actual(crear=True),
            form.cleaned_data["archivo"],
            request.user,
        )
        messages.success(request, "Retorno SINTyS importado correctamente.")
        return redirect("pas_cruces")


class PasCrucesActualizarRenaperView(LoginRequiredMixin, View):
    def post(self, request):
        resumen = sincronizar_supervivencia_pas(forzar=True)
        if resumen["errores"]:
            messages.warning(
                request,
                "Control RENAPER finalizado con errores: "
                f"{resumen['vigentes']} personas vivas, "
                f"{resumen['fallecidas']} fallecidas, "
                f"{resumen['no_encontradas']} sin coincidencia y "
                f"{resumen['errores']} errores.",
            )
        else:
            messages.success(
                request,
                "Control RENAPER actualizado: "
                f"{resumen['vigentes']} personas vivas, "
                f"{resumen['fallecidas']} fallecidas y "
                f"{resumen['no_encontradas']} sin coincidencia.",
            )
        return redirect("pas_cruces")


class PasPersonaUpdateView(LoginRequiredMixin, UpdateView):
    model = PasPersona
    form_class = PasPersonaUpdateForm
    template_name = "pas/persona_form.html"

    def get_queryset(self):
        return PasPersona.objects.select_related("provincia", "municipio", "estado")

    def form_valid(self, form):
        messages.success(self.request, "Registro PAS actualizado correctamente.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("pas_panel_control_persona", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "breadcrumb_items": _breadcrumb("Editar"),
                "titulo_formulario": "Editar registro PAS",
                "volver_url": reverse(
                    "pas_panel_control_persona", kwargs={"pk": self.object.pk}
                ),
                "avisos_por_estado": {},
                "mostrar_estado": False,
            }
        )
        return context


class PasPersonaCambiarEstadoView(LoginRequiredMixin, FormView):
    form_class = PasCambioEstadoForm

    def dispatch(self, request, *args, **kwargs):
        self.persona = get_object_or_404(PasPersona, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        cambiar_estado(self.persona, form, usuario=self.request.user)
        messages.success(self.request, "Estado PAS actualizado correctamente.")
        return redirect("pas_panel_control_persona", pk=self.persona.pk)

    def form_invalid(self, form):
        for field_errors in form.errors.values():
            for error in field_errors:
                messages.error(self.request, error)
        return redirect("pas_panel_control_persona", pk=self.persona.pk)


class PasPersonaDeleteView(LoginRequiredMixin, DeleteView):
    model = PasPersona
    template_name = "pas/persona_confirm_delete.html"
    context_object_name = "persona"
    success_url = reverse_lazy("pas_persona_listar")

    def form_valid(self, form):
        messages.success(self.request, "Registro PAS eliminado correctamente.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = _breadcrumb("Eliminar")
        return context


class PasInformeListView(LoginRequiredMixin, ListView):
    model = PasInforme
    template_name = "pas/informe_list.html"
    context_object_name = "informes"
    paginate_by = 10

    def get_queryset(self):
        return buscar_informes(self.request.GET)

    def paginate_queryset(self, queryset, page_size):
        paginator = NoCountPaginator(queryset, page_size)
        page_obj = paginator.get_page(self.request.GET.get(self.page_kwarg))
        object_list = page_obj.object_list
        return paginator, page_obj, object_list, page_obj.has_other_pages()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "breadcrumb_items": _breadcrumb_informes("Listar"),
                "query": self.request.GET.get("q", ""),
            }
        )
        page_obj = context.get("page_obj")
        if page_obj and getattr(page_obj.paginator, "count", None) is None:
            context["page_range"] = build_no_count_page_range(page_obj)
        return context


class PasInformeGenerateView(LoginRequiredMixin, FormView):
    template_name = "pas/informe_form.html"
    form_class = PasInformeGenerarForm

    def form_valid(self, form):
        informe = generar_informe_pas(form, usuario=self.request.user)
        return csv_response_for_informe(informe)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "breadcrumb_items": _breadcrumb_informes("Generar"),
                "avisos_por_estado": _avisos_por_estado(),
            }
        )
        return context


class PasInformePreviewView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        form = PasInformeGenerarForm(request.POST)
        if not form.is_valid():
            return JsonResponse(errors_payload(form), status=400)
        return JsonResponse(preview_payload(form))


class PasInformeDetailView(LoginRequiredMixin, DetailView):
    model = PasInforme
    template_name = "pas/informe_detail.html"
    context_object_name = "informe"

    def get_queryset(self):
        return (
            PasInforme.objects.select_related("usuario")
            .prefetch_related(
                "personas",
                "personas__estado",
                "personas__provincia",
                "personas__avisos",
                "cambios",
                "cambios__persona",
                "cambios__estado_anterior",
                "cambios__estado_nuevo",
                "cambios__avisos_nuevos",
                "cambios__usuario",
            )
            .all()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = _breadcrumb_informes(self.object.numero)
        return context


class PasInformeDownloadView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        informe = get_object_or_404(PasInforme, pk=kwargs["pk"])
        return csv_response_for_informe(informe)
