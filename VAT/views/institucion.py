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
from django.http import JsonResponse

from core.soft_delete.view_helpers import SoftDeleteDeleteViewMixin
from core.models import Localidad
from VAT.models import (
    Centro,
    InstitucionContacto,
    AutoridadInstitucional,
    InstitucionIdentificadorHist,
    InstitucionUbicacion,
)
from VAT.forms import (
    InstitucionContactoForm,
    AutoridadInstitucionalForm,
    InstitucionIdentificadorHistForm,
    InstitucionUbicacionForm,
)

logger = logging.getLogger("django")


# ============================================================================
# INSTITUCIÓN CONTACTO VIEWS
# ============================================================================


class InstitucionContactoListView(LoginRequiredMixin, ListView):
    model = InstitucionContacto
    template_name = "vat/institucion/contacto_list.html"
    context_object_name = "contactos"
    paginate_by = 20

    def get_queryset(self):
        queryset = InstitucionContacto.objects.select_related("centro").order_by(
            "centro", "tipo"
        )
        centro_id = self.request.GET.get("centro_id")
        tipo = self.request.GET.get("tipo")
        buscar = self.request.GET.get("busqueda") or self.request.GET.get("q")

        if centro_id:
            queryset = queryset.filter(centro_id=centro_id)
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        if buscar:
            queryset = queryset.filter(
                Q(valor__icontains=buscar) | Q(centro__nombre__icontains=buscar)
            )

        return queryset


class InstitucionContactoCreateView(LoginRequiredMixin, CreateView):
    model = InstitucionContacto
    form_class = InstitucionContactoForm
    template_name = "vat/institucion/contacto_form.html"
    success_url = reverse_lazy("vat_institucion_contacto_list")

    def get_initial(self):
        initial = super().get_initial()
        centro_id = self.request.GET.get("centro")
        if centro_id:
            initial["centro"] = centro_id
        return initial

    def form_valid(self, form):
        messages.success(self.request, "Contacto creado exitosamente.")
        return super().form_valid(form)


class InstitucionContactoDetailView(LoginRequiredMixin, DetailView):
    model = InstitucionContacto
    template_name = "vat/institucion/contacto_detail.html"
    context_object_name = "contacto"


class InstitucionContactoUpdateView(LoginRequiredMixin, UpdateView):
    model = InstitucionContacto
    form_class = InstitucionContactoForm
    template_name = "vat/institucion/contacto_form.html"
    success_url = reverse_lazy("vat_institucion_contacto_list")

    def form_valid(self, form):
        messages.success(self.request, "Contacto actualizado exitosamente.")
        return super().form_valid(form)


class InstitucionContactoDeleteView(
    SoftDeleteDeleteViewMixin, LoginRequiredMixin, DeleteView
):
    model = InstitucionContacto
    template_name = "vat/institucion/contacto_confirm_delete.html"
    context_object_name = "contacto"
    success_url = reverse_lazy("vat_institucion_contacto_list")


# ============================================================================
# AUTORIDAD INSTITUCIONAL VIEWS
# ============================================================================


class AutoridadInstitucionalListView(LoginRequiredMixin, ListView):
    model = AutoridadInstitucional
    template_name = "vat/institucion/autoridad_list.html"
    context_object_name = "autoridades"
    paginate_by = 20

    def get_queryset(self):
        queryset = AutoridadInstitucional.objects.select_related("centro").order_by(
            "-es_actual", "centro"
        )
        centro_id = self.request.GET.get("centro_id")
        buscar = self.request.GET.get("busqueda") or self.request.GET.get("q")

        if centro_id:
            queryset = queryset.filter(centro_id=centro_id)
        if buscar:
            queryset = queryset.filter(
                Q(nombre_completo__icontains=buscar)
                | Q(centro__nombre__icontains=buscar)
            )

        return queryset


class AutoridadInstitucionalCreateView(LoginRequiredMixin, CreateView):
    model = AutoridadInstitucional
    form_class = AutoridadInstitucionalForm
    template_name = "vat/institucion/autoridad_form.html"
    success_url = reverse_lazy("vat_autoridad_institucional_list")

    def get_initial(self):
        initial = super().get_initial()
        centro_id = self.request.GET.get("centro")
        if centro_id:
            initial["centro"] = centro_id
        return initial

    def form_valid(self, form):
        messages.success(self.request, "Autoridad creada exitosamente.")
        return super().form_valid(form)


class AutoridadInstitucionalDetailView(LoginRequiredMixin, DetailView):
    model = AutoridadInstitucional
    template_name = "vat/institucion/autoridad_detail.html"
    context_object_name = "autoridad"


class AutoridadInstitucionalUpdateView(LoginRequiredMixin, UpdateView):
    model = AutoridadInstitucional
    form_class = AutoridadInstitucionalForm
    template_name = "vat/institucion/autoridad_form.html"
    success_url = reverse_lazy("vat_autoridad_institucional_list")

    def form_valid(self, form):
        messages.success(self.request, "Autoridad actualizada exitosamente.")
        return super().form_valid(form)


class AutoridadInstitucionalDeleteView(
    SoftDeleteDeleteViewMixin, LoginRequiredMixin, DeleteView
):
    model = AutoridadInstitucional
    template_name = "vat/institucion/autoridad_confirm_delete.html"
    context_object_name = "autoridad"
    success_url = reverse_lazy("vat_autoridad_institucional_list")


# ============================================================================
# INSTITUCIÓN IDENTIFICADOR HISTÓRICO VIEWS
# ============================================================================


class InstitucionIdentificadorHistListView(LoginRequiredMixin, ListView):
    model = InstitucionIdentificadorHist
    template_name = "vat/institucion/identificador_list.html"
    context_object_name = "identificadores"
    paginate_by = 20

    def get_queryset(self):
        queryset = InstitucionIdentificadorHist.objects.select_related(
            "centro"
        ).order_by("-es_actual", "centro")
        centro_id = self.request.GET.get("centro_id")
        tipo = self.request.GET.get("tipo_identificador")
        buscar = self.request.GET.get("busqueda") or self.request.GET.get("q")

        if centro_id:
            queryset = queryset.filter(centro_id=centro_id)
        if tipo:
            queryset = queryset.filter(tipo_identificador=tipo)
        if buscar:
            queryset = queryset.filter(
                Q(valor_identificador__icontains=buscar)
                | Q(centro__nombre__icontains=buscar)
            )

        return queryset


class InstitucionIdentificadorHistCreateView(LoginRequiredMixin, CreateView):
    model = InstitucionIdentificadorHist
    form_class = InstitucionIdentificadorHistForm
    template_name = "vat/institucion/identificador_form.html"
    success_url = reverse_lazy("vat_institucion_identificador_list")

    def get_initial(self):
        initial = super().get_initial()
        centro_id = self.request.GET.get("centro")
        if centro_id:
            initial["centro"] = centro_id
        return initial

    def form_valid(self, form):
        messages.success(self.request, "Identificador creado exitosamente.")
        return super().form_valid(form)


class InstitucionIdentificadorHistDetailView(LoginRequiredMixin, DetailView):
    model = InstitucionIdentificadorHist
    template_name = "vat/institucion/identificador_detail.html"
    context_object_name = "identificador"


class InstitucionIdentificadorHistUpdateView(LoginRequiredMixin, UpdateView):
    model = InstitucionIdentificadorHist
    form_class = InstitucionIdentificadorHistForm
    template_name = "vat/institucion/identificador_form.html"
    success_url = reverse_lazy("vat_institucion_identificador_list")

    def form_valid(self, form):
        messages.success(self.request, "Identificador actualizado exitosamente.")
        return super().form_valid(form)


class InstitucionIdentificadorHistDeleteView(
    SoftDeleteDeleteViewMixin, LoginRequiredMixin, DeleteView
):
    model = InstitucionIdentificadorHist
    template_name = "vat/institucion/identificador_confirm_delete.html"
    context_object_name = "identificador"
    success_url = reverse_lazy("vat_institucion_identificador_list")


# ============================================================================
# INSTITUCIÓN UBICACIÓN VIEWS
# ============================================================================


class InstitucionUbicacionListView(LoginRequiredMixin, ListView):
    model = InstitucionUbicacion
    template_name = "vat/institucion/ubicacion_list.html"
    context_object_name = "ubicaciones"
    paginate_by = 20

    def get_queryset(self):
        queryset = InstitucionUbicacion.objects.select_related(
            "centro", "localidad"
        ).order_by("-es_principal", "centro")
        centro_id = self.request.GET.get("centro_id")
        rol = self.request.GET.get("rol_ubicacion")
        buscar = self.request.GET.get("busqueda") or self.request.GET.get("q")

        if centro_id:
            queryset = queryset.filter(centro_id=centro_id)
        if rol:
            queryset = queryset.filter(rol_ubicacion=rol)
        if buscar:
            queryset = queryset.filter(
                Q(domicilio__icontains=buscar) | Q(centro__nombre__icontains=buscar)
            )

        return queryset


class InstitucionUbicacionCreateView(LoginRequiredMixin, CreateView):
    model = InstitucionUbicacion
    form_class = InstitucionUbicacionForm
    template_name = "vat/institucion/ubicacion_form.html"
    success_url = reverse_lazy("vat_institucion_ubicacion_list")

    def get_initial(self):
        initial = super().get_initial()
        centro_id = self.request.GET.get("centro")
        if centro_id:
            initial["centro"] = centro_id
        return initial

    def form_valid(self, form):
        messages.success(self.request, "Ubicación creada exitosamente.")
        return super().form_valid(form)


class InstitucionUbicacionDetailView(LoginRequiredMixin, DetailView):
    model = InstitucionUbicacion
    template_name = "vat/institucion/ubicacion_detail.html"
    context_object_name = "ubicacion"


class InstitucionUbicacionUpdateView(LoginRequiredMixin, UpdateView):
    model = InstitucionUbicacion
    form_class = InstitucionUbicacionForm
    template_name = "vat/institucion/ubicacion_form.html"
    success_url = reverse_lazy("vat_institucion_ubicacion_list")

    def form_valid(self, form):
        messages.success(self.request, "Ubicación actualizada exitosamente.")
        return super().form_valid(form)


class InstitucionUbicacionDeleteView(
    SoftDeleteDeleteViewMixin, LoginRequiredMixin, DeleteView
):
    model = InstitucionUbicacion
    template_name = "vat/institucion/ubicacion_confirm_delete.html"
    context_object_name = "ubicacion"
    success_url = reverse_lazy("vat_institucion_ubicacion_list")


def localidades_por_centro(request):
    """Devuelve localidades filtradas por el municipio/provincia del centro seleccionado."""
    centro_id = request.GET.get("centro_id")
    if not centro_id:
        return JsonResponse({"localidades": []})
    try:
        centro = Centro.objects.select_related("municipio", "provincia").get(
            pk=centro_id
        )
    except Centro.DoesNotExist:
        return JsonResponse({"localidades": []})

    qs = Localidad.objects.select_related("municipio__provincia").order_by("nombre")
    if centro.municipio_id:
        qs = qs.filter(municipio_id=centro.municipio_id)
    elif centro.provincia_id:
        qs = qs.filter(municipio__provincia_id=centro.provincia_id)

    data = [{"id": loc.id, "nombre": loc.nombre} for loc in qs]
    return JsonResponse({"localidades": data})
