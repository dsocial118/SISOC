# centrodefamilia/views/informescabal.py

from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages

from centrodefamilia.models import (
    Centro,
    Expediente,
)  # ajusta la ruta si lo tienes en otro módulo
from centrodefamilia.forms import ExpedienteCabalForm
from centrodefamilia.services.informescabal import procesar_informe
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)


class ExpedienteListView(LoginRequiredMixin, ListView):
    model = Expediente
    template_name = "centros/expediente_list.html"
    context_object_name = "expedientes"

    def get_queryset(self):
        return Expediente.objects.filter(centro_id=self.kwargs["centro_id"]).order_by(
            "-periodo"
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        centro = get_object_or_404(Centro, pk=self.kwargs["centro_id"])
        ctx["centro"] = centro
        ctx.update({
            "breadcrumb_items": [
                {"text": "Centro de Familia", "url": reverse("centro_list")},
                {"text": centro.nombre, "url": reverse("centro_detail", args=[centro.id])},
                {"text": "Expedientes CABAL", "active": True}
            ],
            "page_title": "Expedientes CABAL",
            "action_buttons": [
                {"url": reverse("centro_detail", args=[centro.id]), "text": "Volver", "type": "secondary"}
            ]
        })
        return ctx


class ExpedienteCreateView(CreateView):
    model = Expediente
    form_class = ExpedienteCabalForm
    template_name = "centros/expediente_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.centro = get_object_or_404(Centro, pk=kwargs["centro_id"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **ctx):
        ctx = super().get_context_data(**ctx)
        ctx["centro"] = self.centro
        return ctx

    def form_valid(self, form):
        form.instance.centro = self.centro
        form.instance.usuario = self.request.user
        messages.success(self.request, "Informe CABAL cargado correctamente.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("expediente_list", kwargs={"centro_id": self.centro.id})


class ExpedienteDetailView(LoginRequiredMixin, DetailView):
    model = Expediente
    template_name = "centros/expediente_detail.html"
    context_object_name = "expediente"

    def dispatch(self, request, *args, **kwargs):
        self.centro = get_object_or_404(Centro, pk=kwargs["centro_id"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **ctx):
        ctx = super().get_context_data(**ctx)
        ctx["centro"] = self.centro
        return ctx

    def get_success_url(self):
        return reverse("expediente_list", kwargs={"centro_id": self.centro.id})


class ExpedienteUpdateView(UpdateView):
    model = Expediente
    form_class = ExpedienteCabalForm
    template_name = "centros/expediente_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.centro = get_object_or_404(Centro, pk=kwargs["centro_id"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **ctx):
        ctx = super().get_context_data(**ctx)
        ctx["centro"] = self.centro
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Informe CABAL actualizado correctamente.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("expediente_list", kwargs={"centro_id": self.centro.id})
