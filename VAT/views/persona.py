import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from ciudadanos.models import Ciudadano
from core.soft_delete.view_helpers import SoftDeleteDeleteViewMixin
from VAT.forms import InscripcionForm
from VAT.models import Inscripcion
from VAT.services.inscripcion_service import InscripcionService

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
        buscar = self.request.GET.get("busqueda") or self.request.GET.get("q")

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
        comision_id = self.request.GET.get("comision")
        if ciudadano_id:
            initial["ciudadano"] = ciudadano_id
        if comision_id:
            initial["comision"] = comision_id
        return initial

    def form_valid(self, form):
        try:
            data = form.cleaned_data
            self.object = InscripcionService.crear_inscripcion(
                ciudadano=data["ciudadano"],
                comision=data["comision"],
                programa=data["programa"],
                estado=data["estado"],
                origen_canal=data["origen_canal"],
                observaciones=data.get("observaciones", ""),
                usuario=self.request.user,
            )
        except ValueError as exc:
            messages.error(self.request, str(exc))
            return self.form_invalid(form)

        cantidad_debito = getattr(self.object, "_voucher_debito", 0)
        if cantidad_debito > 0:
            saldo = getattr(self.object, "_voucher_saldo", 0)
            messages.success(
                self.request,
                f"Inscripción creada. Se descontaron {cantidad_debito} créditos del voucher de {self.object.ciudadano} ({saldo} restantes).",
            )
        else:
            messages.success(self.request, "Inscripción creada exitosamente.")

        return HttpResponseRedirect(self.get_success_url())


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
