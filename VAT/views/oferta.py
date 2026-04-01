import logging
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    CreateView,
    DetailView,
    UpdateView,
    DeleteView,
)
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseRedirect

from VAT.models import InscripcionOferta
from VAT.forms import InscripcionOfertaForm
from VAT.services.inscripcion_service import InscripcionService

logger = logging.getLogger("django")


class InscripcionOfertaListView(LoginRequiredMixin, ListView):
    model = InscripcionOferta
    template_name = "vat/inscripcion_oferta/list.html"
    context_object_name = "inscripciones"
    paginate_by = 20

    def get_queryset(self):
        queryset = InscripcionOferta.objects.select_related(
            "oferta", "ciudadano"
        ).order_by("-fecha_inscripcion")

        oferta_id = self.request.GET.get("oferta_id")
        estado = self.request.GET.get("estado")
        buscar = self.request.GET.get("busqueda") or self.request.GET.get("q")

        if oferta_id:
            queryset = queryset.filter(oferta_id=oferta_id)
        if estado:
            queryset = queryset.filter(estado=estado)
        if buscar:
            queryset = queryset.filter(
                Q(ciudadano__nombre__icontains=buscar)
                | Q(ciudadano__apellido__icontains=buscar)
                | Q(ciudadano__documento__icontains=buscar)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q", "")
        context["estado_choices"] = InscripcionOferta.ESTADO_CHOICES
        context["selected_estado"] = self.request.GET.get("estado", "")
        return context


class InscripcionOfertaCreateView(LoginRequiredMixin, CreateView):
    model = InscripcionOferta
    form_class = InscripcionOfertaForm
    template_name = "vat/inscripcion_oferta/form.html"
    success_url = reverse_lazy("vat_inscripcion_oferta_list")

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            self.object = InscripcionService.crear_inscripcion_oferta(
                ciudadano=data["ciudadano"],
                comision=data["oferta"],
                estado=data["estado"],
                inscrito_por=self.request.user,
            )
        except ValueError as exc:
            messages.error(self.request, str(exc))
            return self.form_invalid(form)

        cantidad_debito = getattr(self.object, "voucher_debito", 0)
        if cantidad_debito > 0:
            saldo = getattr(self.object, "voucher_saldo", 0)
            messages.success(
                self.request,
                (
                    f"Inscripción creada. Se descontaron {cantidad_debito} "
                    f"créditos del voucher de {self.object.ciudadano} "
                    f"({saldo} restantes)."
                ),
            )
        else:
            messages.success(self.request, "Inscripción creada exitosamente.")

        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        messages.error(self.request, "Error al crear la inscripción.")
        return super().form_invalid(form)


class InscripcionOfertaDetailView(LoginRequiredMixin, DetailView):
    model = InscripcionOferta
    template_name = "vat/inscripcion_oferta/detail.html"
    context_object_name = "inscripcion"


class InscripcionOfertaUpdateView(LoginRequiredMixin, UpdateView):
    model = InscripcionOferta
    form_class = InscripcionOfertaForm
    template_name = "vat/inscripcion_oferta/form.html"
    success_url = reverse_lazy("vat_inscripcion_oferta_list")

    def form_valid(self, form):
        messages.success(self.request, "Inscripción actualizada exitosamente.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Error al actualizar la inscripción.")
        return super().form_invalid(form)


class InscripcionOfertaDeleteView(LoginRequiredMixin, DeleteView):
    model = InscripcionOferta
    template_name = "vat/inscripcion_oferta/confirm_delete.html"
    context_object_name = "inscripcion"
    success_url = reverse_lazy("vat_inscripcion_oferta_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Inscripción eliminada exitosamente.")
        return super().delete(request, *args, **kwargs)
