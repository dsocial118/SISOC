from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from prestaciones.models import Prestacion
from prestaciones.forms import PrestacionForm
from historial.services.historial_service import HistorialService


class PrestacionListView(LoginRequiredMixin, ListView):
    model = Prestacion
    template_name = "prestacion_list.html"
    context_object_name = "prestaciones"
    paginate_by = 10


class PrestacionCreateView(LoginRequiredMixin, CreateView):
    model = Prestacion
    form_class = PrestacionForm
    template_name = "prestacion_form.html"
    success_url = reverse_lazy("prestacion")

    def form_valid(self, form):
        obj = form.save(commit=False)
        if not getattr(obj, "usuario_creador", None):
            obj.usuario_creador = self.request.user
        obj.save()
        self.object = obj
        messages.success(self.request, "Prestación creada correctamente.")
        HistorialService.registrar_historial(
            accion="Creación de Prestación",
            instancia=obj,
            diferencias=form.cleaned_data,
        )
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = [
            {"name": "Prestaciones", "url": reverse("prestacion")},
            {"name": "Crear Prestación"},
        ]
        context["back_button"] = reverse("prestacion")
        context["action_buttons"] = []
        context["hidden_fields_send"] = []
        context["guardar_otro_send"] = False
        return context


class PrestacionUpdateView(LoginRequiredMixin, UpdateView):
    model = Prestacion
    form_class = PrestacionForm
    template_name = "prestacion_form.html"
    success_url = reverse_lazy("prestacion")

    def form_valid(self, form):
        obj = form.save()
        messages.success(self.request, "Prestación actualizada correctamente.")
        HistorialService.registrar_historial(
            accion="Edición de Prestación",
            instancia=obj,
            diferencias=form.cleaned_data,
        )
        return HttpResponseRedirect(self.get_success_url())


class PrestacionDeleteView(LoginRequiredMixin, DeleteView):
    model = Prestacion
    template_name = "prestacion_confirm_delete.html"
    success_url = reverse_lazy("prestacion")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = getattr(self, "object", None) or self.get_object()
        context["breadcrumb_items"] = [
            {"name": "Prestaciones", "url": reverse("prestacion")},
            {"name": "Eliminar Prestación"},
        ]
        context["object_title"] = str(obj)
        context["delete_message"] = (
            "¿Desea eliminar esta prestación? Esta acción no se puede deshacer."
        )
        context["cancel_url"] = reverse("prestacion")
        return context

    def form_valid(self, form):
        obj = self.get_object()
        messages.success(self.request, "Prestación eliminada correctamente.")
        try:
            HistorialService.registrar_historial(
                accion="Eliminación de Prestación",
                instancia=obj,
                diferencias={"programa": getattr(obj, "programa", None)},
            )
        except Exception:
            pass
        return super().form_valid(form)


class PrestacionDetailView(LoginRequiredMixin, DetailView):
    model = Prestacion
    template_name = "prestacion_detail.html"
    context_object_name = "prestacion"
