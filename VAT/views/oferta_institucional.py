import logging
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.contrib import messages
from django.db.models import Q, Count

from core.soft_delete.view_helpers import SoftDeleteDeleteViewMixin
from VAT.models import (
    OfertaInstitucional,
    Comision,
    ComisionHorario,
)
from VAT.forms import (
    OfertaInstitucionalForm,
    ComisionForm,
    ComisionHorarioForm,
)

logger = logging.getLogger("django")


# ============================================================================
# OFERTA INSTITUCIONAL VIEWS
# ============================================================================

class OfertaInstitucionalListView(LoginRequiredMixin, ListView):
    model = OfertaInstitucional
    template_name = "vat/oferta_institucional/oferta_list.html"
    context_object_name = "ofertas"
    paginate_by = 20

    def get_queryset(self):
        queryset = OfertaInstitucional.objects.select_related(
            "centro", "plan_curricular", "programa"
        ).order_by("-ciclo_lectivo")

        centro_id = self.request.GET.get("centro_id")
        estado = self.request.GET.get("estado")
        buscar = self.request.GET.get("q")

        if centro_id:
            queryset = queryset.filter(centro_id=centro_id)
        if estado:
            queryset = queryset.filter(estado=estado)
        if buscar:
            queryset = queryset.filter(
                Q(centro__nombre__icontains=buscar)
                | Q(plan_curricular__titulo_referencia__nombre__icontains=buscar)
                | Q(nombre_local__icontains=buscar)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["estado_choices"] = OfertaInstitucional.ESTADO_OFERTA_CHOICES
        return context


class OfertaInstitucionalCreateView(LoginRequiredMixin, CreateView):
    model = OfertaInstitucional
    form_class = OfertaInstitucionalForm
    template_name = "vat/oferta_institucional/oferta_form.html"
    success_url = reverse_lazy("vat_oferta_institucional_list")

    def get_initial(self):
        initial = super().get_initial()
        centro_id = self.request.GET.get("centro")
        if centro_id:
            initial["centro"] = centro_id
        return initial

    def form_valid(self, form):
        messages.success(self.request, "Oferta institucional creada exitosamente.")
        return super().form_valid(form)


class OfertaInstitucionalDetailView(LoginRequiredMixin, DetailView):
    model = OfertaInstitucional
    template_name = "vat/oferta_institucional/oferta_detail.html"
    context_object_name = "oferta"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        oferta = self.get_object()
        context["comisiones"] = Comision.objects.filter(oferta=oferta).prefetch_related("horarios")
        context["total_comisiones"] = context["comisiones"].count()
        return context


class OfertaInstitucionalUpdateView(LoginRequiredMixin, UpdateView):
    model = OfertaInstitucional
    form_class = OfertaInstitucionalForm
    template_name = "vat/oferta_institucional/oferta_form.html"
    success_url = reverse_lazy("vat_oferta_institucional_list")

    def form_valid(self, form):
        messages.success(self.request, "Oferta institucional actualizada exitosamente.")
        return super().form_valid(form)


class OfertaInstitucionalDeleteView(SoftDeleteDeleteViewMixin, LoginRequiredMixin, DeleteView):
    model = OfertaInstitucional
    template_name = "vat/oferta_institucional/oferta_confirm_delete.html"
    context_object_name = "oferta"
    success_url = reverse_lazy("vat_oferta_institucional_list")


# ============================================================================
# COMISIÓN VIEWS
# ============================================================================

class ComisionListView(LoginRequiredMixin, ListView):
    model = Comision
    template_name = "vat/oferta_institucional/comision_list.html"
    context_object_name = "comisiones"
    paginate_by = 20

    def get_queryset(self):
        queryset = Comision.objects.select_related("oferta").prefetch_related("horarios").order_by("codigo_comision")

        oferta_id = self.request.GET.get("oferta_id")
        estado = self.request.GET.get("estado")
        buscar = self.request.GET.get("q")

        if oferta_id:
            queryset = queryset.filter(oferta_id=oferta_id)
        if estado:
            queryset = queryset.filter(estado=estado)
        if buscar:
            queryset = queryset.filter(Q(codigo_comision__icontains=buscar) | Q(nombre__icontains=buscar))

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["estado_choices"] = Comision.ESTADO_COMISION_CHOICES
        return context


class ComisionCreateView(LoginRequiredMixin, CreateView):
    model = Comision
    form_class = ComisionForm
    template_name = "vat/oferta_institucional/comision_form.html"
    success_url = reverse_lazy("vat_comision_list")

    def get_initial(self):
        initial = super().get_initial()
        oferta_id = self.request.GET.get("oferta")
        if oferta_id:
            initial["oferta"] = oferta_id
        return initial

    def form_valid(self, form):
        messages.success(self.request, "Comisión creada exitosamente.")
        return super().form_valid(form)


class ComisionDetailView(LoginRequiredMixin, DetailView):
    model = Comision
    template_name = "vat/oferta_institucional/comision_detail.html"
    context_object_name = "comision"

    def get_context_data(self, **kwargs):
        from VAT.models import SesionComision
        context = super().get_context_data(**kwargs)
        comision = self.get_object()
        context["horarios"] = ComisionHorario.objects.filter(comision=comision).select_related("dia_semana")
        context["sesiones"] = SesionComision.objects.filter(comision=comision).select_related("horario__dia_semana").order_by("fecha", "horario__hora_desde")
        return context


class ComisionUpdateView(LoginRequiredMixin, UpdateView):
    model = Comision
    form_class = ComisionForm
    template_name = "vat/oferta_institucional/comision_form.html"
    success_url = reverse_lazy("vat_comision_list")

    def form_valid(self, form):
        messages.success(self.request, "Comisión actualizada exitosamente.")
        return super().form_valid(form)


class ComisionDeleteView(SoftDeleteDeleteViewMixin, LoginRequiredMixin, DeleteView):
    model = Comision
    template_name = "vat/oferta_institucional/comision_confirm_delete.html"
    context_object_name = "comision"
    success_url = reverse_lazy("vat_comision_list")


# ============================================================================
# COMISIÓN HORARIO VIEWS
# ============================================================================

class ComisionHorarioListView(LoginRequiredMixin, ListView):
    model = ComisionHorario
    template_name = "vat/oferta_institucional/horario_list.html"
    context_object_name = "horarios"
    paginate_by = 20

    def get_queryset(self):
        queryset = ComisionHorario.objects.select_related("comision", "dia_semana").order_by("comision", "dia_semana", "hora_desde")

        comision_id = self.request.GET.get("comision_id")
        dia = self.request.GET.get("dia_semana")

        if comision_id:
            queryset = queryset.filter(comision_id=comision_id)
        if dia:
            queryset = queryset.filter(dia_semana_id=dia)

        return queryset


class ComisionHorarioCreateView(LoginRequiredMixin, CreateView):
    model = ComisionHorario
    form_class = ComisionHorarioForm
    template_name = "vat/oferta_institucional/horario_form.html"

    def get_initial(self):
        initial = super().get_initial()
        comision_id = self.request.GET.get("comision")
        if comision_id:
            initial["comision"] = comision_id
        return initial

    def form_valid(self, form):
        response = super().form_valid(form)
        from VAT.services.sesion_comision_service.impl import SesionComisionService
        cantidad = SesionComisionService.generar_para_horario(self.object)
        if cantidad:
            messages.success(self.request, f"Horario creado. Se generaron {cantidad} sesiones.")
        else:
            messages.success(self.request, "Horario creado exitosamente.")
        return response

    def get_success_url(self):
        return reverse("vat_comision_detail", kwargs={"pk": self.object.comision_id})


class ComisionHorarioDetailView(LoginRequiredMixin, DetailView):
    model = ComisionHorario
    template_name = "vat/oferta_institucional/horario_detail.html"
    context_object_name = "horario"


class ComisionHorarioUpdateView(LoginRequiredMixin, UpdateView):
    model = ComisionHorario
    form_class = ComisionHorarioForm
    template_name = "vat/oferta_institucional/horario_form.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        from VAT.services.sesion_comision_service.impl import SesionComisionService
        cantidad = SesionComisionService.regenerar_para_horario(self.object)
        messages.success(self.request, f"Horario actualizado. {cantidad} sesiones regeneradas.")
        return response

    def get_success_url(self):
        return reverse("vat_comision_detail", kwargs={"pk": self.object.comision_id})


class ComisionHorarioDeleteView(LoginRequiredMixin, DeleteView):
    model = ComisionHorario
    template_name = "vat/oferta_institucional/horario_confirm_delete.html"
    context_object_name = "horario"

    def form_valid(self, form):
        from VAT.services.sesion_comision_service.impl import SesionComisionService
        SesionComisionService.eliminar_para_horario(self.object)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("vat_comision_detail", kwargs={"pk": self.object.comision_id})
