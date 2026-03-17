from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, View
from django.views.decorators.csrf import ensure_csrf_cookie

from VAT.forms import BeneficiarioForm, ResponsableForm
from VAT.models import Beneficiario, Responsable

from VAT.services.beneficiarios_service import (
    manejar_request_beneficiarios,
    buscar_responsable_renaper,
    buscar_cuil_beneficiario,
    get_beneficiarios_list_context,
    get_responsables_list_context,
    prepare_beneficiarios_for_display,
    prepare_responsables_for_display,
    get_filtered_beneficiarios,
    get_filtered_responsables,
    get_responsable_detail_context,
    get_beneficiario_detail_queryset,
)
from VAT.services.beneficiarios_filter_config import (
    get_filters_ui_config as get_beneficiarios_filters_ui_config,
)
from VAT.services.responsables_filter_config import (
    get_filters_ui_config as get_responsables_filters_ui_config,
)
from core.services.favorite_filters import SeccionesFiltrosFavoritos


class BuscarCUILView(LoginRequiredMixin, View):
    def get(self, request):
        return buscar_cuil_beneficiario(request, request.GET.get("cuil"))


class BuscarResponsableView(LoginRequiredMixin, View):
    def get(self, request):
        return buscar_responsable_renaper(
            request, request.GET.get("dni"), request.GET.get("sexo")
        )


@method_decorator(ensure_csrf_cookie, name="dispatch")
class BeneficiariosListView(LoginRequiredMixin, ListView):
    model = Beneficiario
    template_name = "vat/beneficiarios/beneficiarios_list.html"
    context_object_name = "beneficiarios"
    paginate_by = 10

    def get_queryset(self):
        return get_filtered_beneficiarios(self.request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_beneficiarios_list_context(self.request))
        prepare_beneficiarios_for_display(context["beneficiarios"])
        context.update(
            {
                "breadcrumb_items": [
                    {"text": "Beneficiarios", "url": reverse("vat_beneficiarios_list")},
                    {"text": "Listar", "active": True},
                ],
                "reset_url": reverse("vat_beneficiarios_list"),
                "add_url": reverse("vat_beneficiarios_crear"),
                "filters_mode": True,
                "filters_js": "custom/js/advanced_filters.js",
                "filters_action": reverse("vat_beneficiarios_list"),
                "filters_config": get_beneficiarios_filters_ui_config(),
                "seccion_filtros_favoritos": SeccionesFiltrosFavoritos.VAT_BENEFICIARIOS,
                "add_text": "Crear un nuevo Preinscripto",
            }
        )
        return context


@method_decorator(ensure_csrf_cookie, name="dispatch")
class ResponsableListView(LoginRequiredMixin, ListView):
    model = Responsable
    template_name = "vat/beneficiarios/responsable_list.html"
    context_object_name = "responsables"
    paginate_by = 10

    def get_queryset(self):
        return get_filtered_responsables(self.request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_responsables_list_context(self.request))
        prepare_responsables_for_display(context["responsables"])
        context.update(
            {
                "breadcrumb_items": [
                    {"text": "Responsables", "url": reverse("vat_responsables_list")},
                    {"text": "Listar", "active": True},
                ],
                "reset_url": reverse("vat_responsables_list"),
                "filters_mode": True,
                "filters_js": "custom/js/advanced_filters.js",
                "filters_action": reverse("vat_responsables_list"),
                "filters_config": get_responsables_filters_ui_config(),
                "seccion_filtros_favoritos": SeccionesFiltrosFavoritos.VAT_RESPONSABLES,
                "show_add_button": False,
            }
        )
        return context


class ResponsableDetailView(LoginRequiredMixin, DetailView):
    model = Responsable
    template_name = "vat/beneficiarios/responsable_detail.html"
    context_object_name = "responsable"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_responsable_detail_context(self.object))
        return context


class BeneficiariosDetailView(LoginRequiredMixin, DetailView):
    model = Beneficiario
    template_name = "vat/beneficiarios/beneficiarios_detail.html"
    context_object_name = "beneficiario"

    def get_queryset(self):
        return get_beneficiario_detail_queryset()


class BeneficiariosCreateView(LoginRequiredMixin, View):
    template_name = "vat/beneficiarios/beneficiarios_form.html"

    def get(self, request):
        return render(
            request,
            self.template_name,
            {"form": BeneficiarioForm(), "responsable_form": ResponsableForm()},
        )

    def post(self, request):
        return manejar_request_beneficiarios(request, self.template_name)
