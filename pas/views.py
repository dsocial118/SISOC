from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import DetailView, ListView, TemplateView, View
from django.views.generic.edit import FormView

from core.models import Municipio
from core.pagination import NoCountPaginator, build_no_count_page_range
from pas.forms import (
    PasDeclaracionJuradaForm,
    PasInformeGenerarForm,
    PasRetornoSintysForm,
    PasTitularesImportForm,
)
from pas.models import (
    PasDeclaracionJurada,
    PasIncompatibilidad,
    PasInforme,
    PasInvitacionDDJJ,
    PasPersona,
)
from pas.services.cruces_service import (
    construir_etapas,
    obtener_circuito_actual,
    registrar_exportacion_sintys,
    registrar_importacion_sintys,
)
    PasTitularesImportForm,
)
from pas.models import PasDeclaracionJurada, PasInforme, PasInvitacionDDJJ
from pas.services.ddjj_service import presentar_ddjj
from pas.services.informe_service import (
    buscar_informes,
    csv_response_for_informe,
    errors_payload,
    generar_informe_pas,
    preview_payload,
)
from pas.services.supervivencia_service import (
    resumen_supervivencia,
    sincronizar_supervivencia_pas,
)
from pas.services.titulares_import_service import (
    generar_excel_tokens_vigentes,
    importar_titulares_csv,
)


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


class PasTokensExportView(LoginRequiredMixin, View):
    def get(self, request):
        contenido = generar_excel_tokens_vigentes(usuario=request.user)
        response = HttpResponse(
            contenido,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = (
            'attachment; filename="pas_tokens_ddjj_vigentes.xlsx"'
        )
        return response


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
            filename=f"DDJJ_PAS_{declaracion.persona.dni}_v{declaracion.version}.pdf",
            content_type="application/pdf",
        )


def _breadcrumb_informes(actual):
    return [
        {"text": "PAS"},
        {"text": "Informes", "url": reverse("pas_informe_listar")},
        {"text": actual, "active": True},
    ]


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
        return paginator, page_obj, page_obj.object_list, page_obj.has_other_pages()

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
        context["breadcrumb_items"] = _breadcrumb_informes("Generar")
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
        return PasInforme.objects.select_related("usuario").all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = _breadcrumb_informes(self.object.numero)
        return context


class PasInformeDownloadView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        informe = get_object_or_404(PasInforme, pk=kwargs["pk"])
        return csv_response_for_informe(informe)


class PasCrucesView(LoginRequiredMixin, TemplateView):
    template_name = "pas/cruces.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        circuito = obtener_circuito_actual()
        context.update(
            {
                "breadcrumb_items": [
                    {"text": "PAS"},
                    {"text": "Cruces y novedades", "active": True},
                ],
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


class PasCrucesExportarSintysView(LoginRequiredMixin, View):
    def post(self, request):
        circuito = obtener_circuito_actual(crear=True)
        contenido, nombre = registrar_exportacion_sintys(circuito, request.user)
        response = HttpResponse(
            contenido,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{nombre}"'
        return response


class PasCrucesImportarSintysView(LoginRequiredMixin, View):
    def post(self, request):
        form = PasRetornoSintysForm(request.POST, request.FILES)
        if not form.is_valid():
            errores = " ".join(
                error for items in form.errors.values() for error in items
            )
            messages.error(request, f"No se pudo importar el retorno: {errores}")
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
        nivel = messages.warning if resumen["errores"] else messages.success
        nivel(
            request,
            "Control RENAPER actualizado: "
            f"{resumen['vigentes']} personas vivas, "
            f"{resumen['fallecidas']} fallecidas, "
            f"{resumen['no_encontradas']} sin coincidencia y "
            f"{resumen['errores']} errores.",
        )
        return redirect("pas_cruces")
