from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import ListView, DetailView, View

from centrodefamilia.forms import BeneficiarioForm, ResponsableForm
from centrodefamilia.models import Beneficiario, Responsable

from centrodefamilia.services.beneficiarios_service import (
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
from centrodefamilia.services.beneficiarios_filter_config import (
    get_filters_ui_config as get_beneficiarios_filters_ui_config,
)
from centrodefamilia.services.responsables_filter_config import (
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


class BeneficiariosListView(LoginRequiredMixin, ListView):
    model = Beneficiario
    template_name = "beneficiarios/beneficiarios_list.html"
    context_object_name = "beneficiarios"
    paginate_by = 10

    def get_queryset(self):
        return get_filtered_beneficiarios(self.request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_beneficiarios_list_context())
        prepare_beneficiarios_for_display(context["beneficiarios"])
        context.update(
            {
                "breadcrumb_items": [
                    {"text": "Beneficiarios", "url": reverse("beneficiarios_list")},
                    {"text": "Listar", "active": True},
                ],
                "reset_url": reverse("beneficiarios_list"),
                "add_url": reverse("beneficiarios_crear"),
                "filters_mode": True,
                "filters_js": "custom/js/advanced_filters.js",
                "filters_action": reverse("beneficiarios_list"),
                "filters_config": get_beneficiarios_filters_ui_config(),
                "seccion_filtros_favoritos": SeccionesFiltrosFavoritos.CDF_BENEFICIARIOS,
                "add_text": "Crear un nuevo Preinscripto",
            }
        )
        return context


class ResponsableListView(LoginRequiredMixin, ListView):
    model = Responsable
    template_name = "beneficiarios/responsable_list.html"
    context_object_name = "responsables"
    paginate_by = 10

    def get_queryset(self):
        return get_filtered_responsables(self.request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_responsables_list_context())
        prepare_responsables_for_display(context["responsables"])
        context.update(
            {
                "breadcrumb_items": [
                    {"text": "Responsables", "url": reverse("responsables_list")},
                    {"text": "Listar", "active": True},
                ],
                "reset_url": reverse("responsables_list"),
                "filters_mode": True,
                "filters_js": "custom/js/advanced_filters.js",
                "filters_action": reverse("responsables_list"),
                "filters_config": get_responsables_filters_ui_config(),
                "seccion_filtros_favoritos": SeccionesFiltrosFavoritos.CDF_RESPONSABLES,
                "show_add_button": False,
            }
        )
        return context


class ResponsableDetailView(LoginRequiredMixin, DetailView):
    model = Responsable
    template_name = "beneficiarios/responsable_detail.html"
    context_object_name = "responsable"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_responsable_detail_context(self.object))
        return context


class BeneficiariosDetailView(LoginRequiredMixin, DetailView):
    model = Beneficiario
    template_name = "beneficiarios/beneficiarios_detail.html"
    context_object_name = "beneficiario"

    def get_queryset(self):
        return get_beneficiario_detail_queryset()


class BeneficiariosCreateView(LoginRequiredMixin, View):
    template_name = "beneficiarios/beneficiarios_form.html"

    def get(self, request):
        return render(
            request,
            self.template_name,
            {"form": BeneficiarioForm(), "responsable_form": ResponsableForm()},
        )

    def post(self, request):
        return manejar_request_beneficiarios(request, self.template_name)
