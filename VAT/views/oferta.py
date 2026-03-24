import logging
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.contrib import messages
from django.db.models import Q

from VAT.models import InscripcionOferta, Voucher
from VAT.forms import InscripcionOfertaForm
from VAT.services.voucher_service.impl import VoucherService

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
        buscar = self.request.GET.get("q")

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
        form.instance.inscrito_por = self.request.user
        response = super().form_valid(form)

        inscripcion = self.object
        comision = inscripcion.oferta
        oferta = comision.oferta  # OfertaInstitucional

        if oferta.usa_voucher:
            voucher = (
                Voucher.objects.filter(
                    ciudadano=inscripcion.ciudadano,
                    programa=oferta.programa,
                    estado="activo",
                )
                .order_by("fecha_vencimiento")
                .first()
            )

            if not voucher:
                inscripcion.delete()
                messages.error(
                    self.request,
                    f"{inscripcion.ciudadano} no tiene voucher activo para el programa {oferta.programa}. No se realizó la inscripción.",
                )
                return self.form_invalid(form)

            ok, msg = VoucherService.usar_voucher(
                voucher=voucher,
                inscripcion_oferta=inscripcion,
                cantidad=1,
            )
            if not ok:
                inscripcion.delete()
                messages.error(self.request, f"No se pudo usar el voucher: {msg}")
                return self.form_invalid(form)

            messages.success(
                self.request,
                f"Inscripción creada. Se descontó 1 crédito del voucher de {inscripcion.ciudadano} ({voucher.cantidad_disponible} restantes).",
            )
        else:
            messages.success(self.request, "Inscripción creada exitosamente.")

        return response

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
