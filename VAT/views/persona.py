import logging
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.contrib import messages
from django.db.models import Q

from core.soft_delete.view_helpers import SoftDeleteDeleteViewMixin
from ciudadanos.models import Ciudadano
from VAT.models import (
    Inscripcion,
)
from VAT.forms import (
    InscripcionForm,
)

logger = logging.getLogger("django")


# ============================================================================
# INSCRIPCIÓN VIEWS
# ============================================================================

class InscripcionListView(LoginRequiredMixin, ListView):
    model = Inscripcion
    template_name = "vat/persona/inscripcion_list.html"
    context_object_name = "inscripciones"
    paginate_by = 20

    def get_queryset(self):
        queryset = Inscripcion.objects.select_related(
            "ciudadano", "comision", "programa"
        ).order_by("-fecha_inscripcion")

        ciudadano_id = self.request.GET.get("ciudadano_id")
        comision_id = self.request.GET.get("comision_id")
        estado = self.request.GET.get("estado")
        buscar = self.request.GET.get("q")

        if ciudadano_id:
            queryset = queryset.filter(ciudadano_id=ciudadano_id)
        if comision_id:
            queryset = queryset.filter(comision_id=comision_id)
        if estado:
            queryset = queryset.filter(estado=estado)
        if buscar:
            queryset = queryset.filter(
                Q(ciudadano__apellido__icontains=buscar)
                | Q(ciudadano__nombre__icontains=buscar)
                | Q(comision__codigo_comision__icontains=buscar)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["estado_choices"] = Inscripcion.ESTADO_INSCRIPCION_CHOICES
        return context


class InscripcionCreateView(LoginRequiredMixin, CreateView):
    model = Inscripcion
    form_class = InscripcionForm
    template_name = "vat/persona/inscripcion_form.html"
    success_url = reverse_lazy("vat_inscripcion_list")

    def get_initial(self):
        initial = super().get_initial()
        ciudadano_id = self.request.GET.get("ciudadano")
        if ciudadano_id:
            initial["ciudadano"] = ciudadano_id
        return initial

    def form_valid(self, form):
        messages.success(self.request, "Inscripción creada exitosamente.")
        return super().form_valid(form)


class InscripcionDetailView(LoginRequiredMixin, DetailView):
    model = Inscripcion
    template_name = "vat/persona/inscripcion_detail.html"
    context_object_name = "inscripcion"


class InscripcionUpdateView(LoginRequiredMixin, UpdateView):
    model = Inscripcion
    form_class = InscripcionForm
    template_name = "vat/persona/inscripcion_form.html"
    success_url = reverse_lazy("vat_inscripcion_list")

    def form_valid(self, form):
        messages.success(self.request, "Inscripción actualizada exitosamente.")
        return super().form_valid(form)


class InscripcionDeleteView(SoftDeleteDeleteViewMixin, LoginRequiredMixin, DeleteView):
    model = Inscripcion
    template_name = "vat/persona/inscripcion_confirm_delete.html"
    context_object_name = "inscripcion"
    success_url = reverse_lazy("vat_inscripcion_list")
