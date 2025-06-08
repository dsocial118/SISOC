from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from centrodefamilia.models import Centro
from django.contrib import messages

class CentroListView(LoginRequiredMixin, ListView):
    model = Centro
    template_name = "centros/centro_list.html"
    context_object_name = "centros"

class CentroCreateView(LoginRequiredMixin, CreateView):
    model = Centro
    fields = ['nombre', 'tipo', 'direccion', 'contacto', 'activo', 'faro_asociado']
    template_name = "centros/centro_form.html"
    success_url = reverse_lazy("centros_listar")

    def form_valid(self, form):
        messages.success(self.request, "Centro creado correctamente.")
        return super().form_valid(form)

class CentroUpdateView(LoginRequiredMixin, UpdateView):
    model = Centro
    fields = ['nombre', 'tipo', 'direccion', 'contacto', 'activo', 'faro_asociado']
    template_name = "centros/centro_form.html"
    success_url = reverse_lazy("centros_listar")

    def form_valid(self, form):
        messages.success(self.request, "Centro actualizado correctamente.")
        return super().form_valid(form)
