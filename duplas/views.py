from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import ValidationError
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy

from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from comedores.services.comedor_service import ComedorService
from core.services.advanced_filters import AdvancedFilterEngine
from core.services.favorite_filters import SeccionesFiltrosFavoritos

from duplas.dupla_filter_config import (
    FIELD_MAP as DUPLA_FILTER_MAP,
    FIELD_TYPES as DUPLA_FIELD_TYPES,
    NUM_OPS as DUPLA_NUM_OPS,
    TEXT_OPS as DUPLA_TEXT_OPS,
    get_filters_ui_config,
)
from duplas.forms import DuplaForm
from duplas.models import Dupla

DUPLA_ADVANCED_FILTER = AdvancedFilterEngine(
    field_map=DUPLA_FILTER_MAP,
    field_types=DUPLA_FIELD_TYPES,
    allowed_ops={
        "text": DUPLA_TEXT_OPS,
        "number": DUPLA_NUM_OPS,
    },
)


class DuplaListView(LoginRequiredMixin, ListView):
    model = Dupla
    template_name = "dupla_list.html"
    context_object_name = "duplas"
    paginate_by = 10

    def get_queryset(self):
        """Retorna las duplas ordenadas y filtradas con filtros avanzados"""
        base_qs = (
            Dupla.objects.select_related("abogado", "coordinador")
            .prefetch_related("tecnico")
            .order_by("-fecha", "nombre")
        )

        # Aplicar filtros avanzados combinables asegurando resultados únicos para M2M
        filtered_qs = DUPLA_ADVANCED_FILTER.filter_queryset(base_qs, self.request)
        return filtered_qs.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Configuracion de la tabla
        context["table_headers"] = [
            {"title": "Nombre", "sortable": True, "sort_key": "nombre"},
            {
                "title": "Coordinador",
                "sortable": True,
                "sort_key": "coordinador_nombre",
            },
            {"title": "Técnico/s", "sortable": True, "sort_key": "tecnicos_nombres"},
            {"title": "Abogado", "sortable": True, "sort_key": "abogado_nombre"},
            {"title": "Estado", "sortable": True, "sort_key": "estado"},
        ]
        context["table_fields"] = [
            {"name": "nombre", "link_field": True, "link_url": "dupla_detalle"},
            {"name": "coordinador_nombre"},
            {"name": "tecnicos_nombres"},
            {"name": "abogado_nombre"},
            {"name": "estado"},
        ]
        context["table_actions"] = [
            {
                "label": "Editar",
                "url_name": "dupla_editar",
                "type": "editar",
                "icon": "edit",
            },
            {
                "label": "Eliminar",
                "url_name": "dupla_eliminar",
                "type": "eliminar",
                "icon": "trash-alt",
            },
        ]

        # Configuración para el search_bar con filtros avanzados
        context["reset_url"] = reverse("dupla_list")
        context["add_url"] = reverse("dupla_crear")
        context["filters_mode"] = True
        context["filters_config"] = get_filters_ui_config()
        context["filters_action"] = reverse("dupla_list")
        context["seccion_filtros_favoritos"] = SeccionesFiltrosFavoritos.DUPLAS
        context["show_add_button"] = True
        context["breadcrumb_items"] = [
            {"text": "Equipos técnicos", "url": reverse("dupla_list")},
            {"text": "Listar", "active": True},
        ]

        return context


class DuplaCreateView(LoginRequiredMixin, CreateView):
    model = Dupla
    template_name = "dupla_form.html"
    form_class = DuplaForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "form" in kwargs:
            context["form"] = kwargs["form"]
        else:
            context["form"] = self.get_form()
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            try:
                self.object = self.form_valid(form)
                messages.success(request, "Equipo técnico creado correctamente.")
                return HttpResponseRedirect(self.get_success_url())
            except ValidationError as e:
                messages.error(request, str(e))
                return self.form_invalid(form)
        else:
            messages.error(request, "Error al crear el Equipo técnico.")
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse("dupla_list")


class DuplaUpdateView(LoginRequiredMixin, UpdateView):
    model = Dupla
    template_name = "dupla_form.html"
    form_class = DuplaForm
    success_url = reverse_lazy("dupla_list")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.filtrar_campos_tecnico_abogado()
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "form" in kwargs:
            context["form"] = kwargs["form"]
        else:
            context["form"] = self.get_form()
        return context

    def get_success_url(self):
        return reverse("dupla_list")


class DuplaDetailView(LoginRequiredMixin, DetailView):
    model = Dupla
    template_name = "dupla_detail.html"
    context_object_name = "dupla"

    def get_queryset(self):
        """Optimiza las queries para el detalle de dupla"""
        return Dupla.objects.select_related("abogado", "coordinador").prefetch_related(
            "tecnico"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # El objeto ya está disponible como 'dupla' gracias a context_object_name
        return context


class DuplaDeleteView(LoginRequiredMixin, DeleteView):
    model = Dupla
    template_name = "dupla_confirm_delete.html"
    success_url = reverse_lazy("dupla_list")

    def get_success_url(self):
        return reverse("dupla_list")

    def post(self, request, *args, **kwargs):
        comedor = ComedorService.get_comedor_by_dupla(kwargs["pk"])
        if comedor:
            messages.error(
                request,
                "No se puede eliminar el equipo técnico porque está asignada al comedor "
                + str(comedor.nombre),
            )
            return HttpResponseRedirect(self.get_success_url())
        self.object = self.get_object()
        self.object.delete()
        messages.success(request, "Equipo técnico eliminado correctamente.")
        return HttpResponseRedirect(self.get_success_url())
