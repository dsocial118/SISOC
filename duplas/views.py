from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import ValidationError
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie

from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from comedores.services.comedor_service import ComedorService
from core.services.advanced_filters import AdvancedFilterEngine
from core.services.column_preferences import (
    apply_queryset_column_hints,
    build_columns_context,
    resolve_column_state,
)
from core.services.favorite_filters import SeccionesFiltrosFavoritos
from core.soft_delete_views import SoftDeleteDeleteViewMixin

from duplas.dupla_column_config import DUPLA_COLUMNS, DUPLA_LIST_KEY
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


@method_decorator(ensure_csrf_cookie, name="dispatch")
class DuplaListView(LoginRequiredMixin, ListView):
    model = Dupla
    template_name = "dupla_list.html"
    context_object_name = "duplas"
    paginate_by = 10

    def get_queryset(self):
        """Retorna las duplas ordenadas y filtradas con filtros avanzados"""
        base_qs = Dupla.objects.order_by("-fecha", "nombre")

        # Aplicar filtros avanzados combinables asegurando resultados únicos para M2M
        filtered_qs = DUPLA_ADVANCED_FILTER.filter_queryset(base_qs, self.request)
        column_state = resolve_column_state(
            self.request,
            DUPLA_LIST_KEY,
            DUPLA_COLUMNS,
        )
        optimized_qs = apply_queryset_column_hints(
            filtered_qs,
            DUPLA_COLUMNS,
            column_state.active_keys,
        )
        return optimized_qs.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Configuracion de la tabla
        context.update(
            build_columns_context(
                self.request,
                DUPLA_LIST_KEY,
                DUPLA_COLUMNS,
            )
        )
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


class DuplaDeleteView(SoftDeleteDeleteViewMixin, LoginRequiredMixin, DeleteView):
    model = Dupla
    template_name = "dupla_confirm_delete.html"
    success_url = reverse_lazy("dupla_list")
    success_message = "Equipo técnico dado de baja correctamente."

    def get_success_url(self):
        return reverse("dupla_list")
