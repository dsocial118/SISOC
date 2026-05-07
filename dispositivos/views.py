from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import DispositivoForm
from .models import Dispositivo
from .services import (
    delete_dispositivo,
    get_dispositivos_queryset,
    save_dispositivo_from_form,
)


class DispositivoListView(LoginRequiredMixin, ListView):
    model = Dispositivo
    template_name = "dispositivos_list.html"
    context_object_name = "dispositivos"
    paginate_by = 15

    def get_queryset(self):
        return get_dispositivos_queryset()


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

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        delete_dispositivo(self.object)
        messages.success(self.request, "Dispositivo eliminado correctamente.")
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse("dispositivos_listar")

