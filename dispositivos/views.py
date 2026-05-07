from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from core.services.advanced_filters import AdvancedFilterEngine
from core.services.favorite_filters import SeccionesFiltrosFavoritos

from .dispositivos_filter_config import (
    CHOICE_OPS as DISPOSITIVOS_CHOICE_OPS,
    FIELD_MAP as DISPOSITIVOS_FIELD_MAP,
    FIELD_TYPES as DISPOSITIVOS_FIELD_TYPES,
    NUM_OPS as DISPOSITIVOS_NUM_OPS,
    TEXT_OPS as DISPOSITIVOS_TEXT_OPS,
    get_filters_ui_config,
)
from .forms import DispositivoForm
from .models import Dispositivo
from .services import (
    delete_dispositivo,
    get_dispositivos_queryset,
    save_dispositivo_from_form,
)

DISPOSITIVOS_ADVANCED_FILTER = AdvancedFilterEngine(
    field_map=DISPOSITIVOS_FIELD_MAP,
    field_types=DISPOSITIVOS_FIELD_TYPES,
    allowed_ops={
        "text": DISPOSITIVOS_TEXT_OPS,
        "number": DISPOSITIVOS_NUM_OPS,
        "choice": DISPOSITIVOS_CHOICE_OPS,
    },
)


class DispositivoListView(LoginRequiredMixin, ListView):
    model = Dispositivo
    template_name = "dispositivos_list.html"
    context_object_name = "dispositivos"
    paginate_by = 15

    def get_queryset(self):
        queryset = get_dispositivos_queryset()
        queryset = DISPOSITIVOS_ADVANCED_FILTER.filter_queryset(queryset, self.request)

        query = (self.request.GET.get("busqueda") or "").strip()
        if query:
            queryset = queryset.filter(
                Q(nombre_institucion__icontains=query)
                | Q(tipo_dispositivo__icontains=query)
                | Q(provincia__nombre__icontains=query)
                | Q(municipio__nombre__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["reset_url"] = reverse("dispositivos_listar")
        context["add_url"] = reverse("dispositivos_crear")
        context["filters_mode"] = True
        context["filters_config"] = get_filters_ui_config()
        context["filters_action"] = reverse("dispositivos_listar")
        context["seccion_filtros_favoritos"] = SeccionesFiltrosFavoritos.DISPOSITIVOS
        context["titulo"] = "Buscar Dispositivos"
        return context


class DispositivoDetailView(LoginRequiredMixin, DetailView):
    model = Dispositivo
    template_name = "dispositivos_detail.html"
    context_object_name = "dispositivo"

    def get_queryset(self):
        return get_dispositivos_queryset()


class DispositivoCreateView(LoginRequiredMixin, CreateView):
    model = Dispositivo
    form_class = DispositivoForm
    template_name = "dispositivos_form.html"

    def form_valid(self, form):
        self.object = save_dispositivo_from_form(form)
        messages.success(self.request, "Dispositivo creado correctamente.")
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse("dispositivos_detalle", kwargs={"pk": self.object.pk})


class DispositivoUpdateView(LoginRequiredMixin, UpdateView):
    model = Dispositivo
    form_class = DispositivoForm
    template_name = "dispositivos_form.html"

    def get_queryset(self):
        return get_dispositivos_queryset()

    def form_valid(self, form):
        self.object = save_dispositivo_from_form(form, instance=self.get_object())
        messages.success(self.request, "Dispositivo actualizado correctamente.")
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse("dispositivos_detalle", kwargs={"pk": self.object.pk})


class DispositivoDeleteView(LoginRequiredMixin, DeleteView):
    model = Dispositivo
    template_name = "dispositivos_confirm_delete.html"
    context_object_name = "dispositivo"

    def get_queryset(self):
        return get_dispositivos_queryset()

    def form_valid(self, form):
        self.object = self.get_object()
        delete_dispositivo(self.object)
        messages.success(self.request, "Dispositivo eliminado correctamente.")
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse("dispositivos_listar")

