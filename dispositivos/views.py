import os

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)
from core.services.advanced_filters import AdvancedFilterEngine
from core.services.favorite_filters import SeccionesFiltrosFavoritos

from .dispositivos_filter_config import (
    CHOICE_OPS as DISPOSITIVOS_CHOICE_OPS,
    FIELD_MAP as DISPOSITIVOS_FIELD_MAP,
    FIELD_TYPES as DISPOSITIVOS_FIELD_TYPES,
    NUM_OPS as DISPOSITIVOS_NUM_OPS,
    TEXT_OPS as DISPOSITIVOS_TEXT_OPS,
    get_filters_ui_config,
)
from .forms import DispositivoForm
from .models import Dispositivo
from .services import (
    delete_dispositivo,
    get_dispositivos_queryset,
    save_dispositivo_from_form,
)


def _format_value(value):
    if value in (None, ""):
        return "-"
    return value


def _format_display_list(values, choices):
    labels = dict(choices)
    if not values:
        return []
    return [labels.get(v, v) for v in values]


def _format_file(file_field):
    if not file_field:
        return None
    return {
        "name": os.path.basename(file_field.name),
        "url": file_field.url,
    }


DISPOSITIVOS_ADVANCED_FILTER = AdvancedFilterEngine(
    field_map=DISPOSITIVOS_FIELD_MAP,
    field_types=DISPOSITIVOS_FIELD_TYPES,
    allowed_ops={
        "text": DISPOSITIVOS_TEXT_OPS,
        "number": DISPOSITIVOS_NUM_OPS,
        "choice": DISPOSITIVOS_CHOICE_OPS,
    },
)


class DispositivoListView(LoginRequiredMixin, ListView):
    model = Dispositivo
    template_name = "dispositivos_list.html"
    context_object_name = "dispositivos"
    paginate_by = 15

    def get_queryset(self):
        queryset = get_dispositivos_queryset()
        queryset = DISPOSITIVOS_ADVANCED_FILTER.filter_queryset(queryset, self.request)

        query = (self.request.GET.get("busqueda") or "").strip()
        if query:
            queryset = queryset.filter(
                Q(nombre_institucion__icontains=query)
                | Q(tipo_dispositivo__icontains=query)
                | Q(provincia__nombre__icontains=query)
                | Q(municipio__nombre__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["reset_url"] = reverse("dispositivos_listar")
        context["add_url"] = (
            reverse("dispositivos_crear")
            if self.request.user.has_perm("dispositivos.add_dispositivo")
            else None
        )
        context["filters_mode"] = True
        context["filters_config"] = get_filters_ui_config()
        context["filters_action"] = reverse("dispositivos_listar")
        context["seccion_filtros_favoritos"] = SeccionesFiltrosFavoritos.DISPOSITIVOS
        context["titulo"] = "Buscar Dispositivos"
        return context


class DispositivoDetailView(LoginRequiredMixin, DetailView):
    model = Dispositivo
    template_name = "dispositivos_detail.html"
    context_object_name = "dispositivo"

    def get_queryset(self):
        return get_dispositivos_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dispositivo = self.object
        context["breadcrumb_items"] = [
            {"text": "Dispositivos", "url": reverse("dispositivos_listar")},
            {"text": dispositivo.nombre_institucion},
        ]
        context["detalle_secciones"] = [
            {
                "titulo": "Identificación del dispositivo",
                "icono": "fas fa-building",
                "items": [
                    {"label": "Nombre de la institución", "value": _format_value(dispositivo.nombre_institucion)},
                    {"label": "Tipo de gestión", "value": dispositivo.get_tipo_gestion_display()},
                    {"label": "Tipo de gestión - detalle", "value": _format_value(dispositivo.tipo_gestion_otra)},
                    {"label": "Razón social", "value": _format_value(dispositivo.razon_social)},
                    {"label": "CUIT", "value": _format_value(dispositivo.cuit_institucion)},
                    {"label": "Provincia", "value": _format_value(str(dispositivo.provincia))},
                    {"label": "Municipio", "value": _format_value(str(dispositivo.municipio))},
                    {"label": "Domicilio", "value": _format_value(dispositivo.domicilio_institucion)},
                    {"label": "Teléfono de contacto", "value": _format_value(dispositivo.telefono_contacto)},
                    {"label": "Correo electrónico", "value": _format_value(dispositivo.correo_electronico)},
                    {"label": "Responsable", "value": _format_value(dispositivo.responsable_nombre_completo)},
                    {"label": "DNI del responsable", "value": _format_value(dispositivo.responsable_dni)},
                ],
            },
            {
                "titulo": "Características del dispositivo",
                "icono": "fas fa-cogs",
                "items": [
                    {"label": "Tipo de dispositivo", "value": dispositivo.get_tipo_dispositivo_display()},
                    {"label": "Tipo de dispositivo - detalle", "value": _format_value(dispositivo.tipo_dispositivo_otro)},
                    {"label": "Modalidad de funcionamiento", "value": dispositivo.get_modalidad_funcionamiento_display()},
                    {"label": "Capacidad total de plazas", "value": dispositivo.get_capacidad_total_plazas_display()},
                    {"label": "Días de atención", "value": _format_display_list(dispositivo.dias_atencion, DispositivoForm.DIAS_ATENCION_CHOICES), "kind": "list"},
                    {"label": "Horarios de funcionamiento", "value": _format_display_list(dispositivo.horarios_funcionamiento, DispositivoForm.HORARIOS_FUNCIONAMIENTO_CHOICES), "kind": "list"},
                ],
            },
            {
                "titulo": "Población destinataria",
                "icono": "fas fa-users",
                "items": [
                    {"label": "Población destinataria", "value": _format_display_list(dispositivo.poblacion_destinataria, DispositivoForm.POBLACION_DESTINATARIA_CHOICES), "kind": "list"},
                    {"label": "Detalle población", "value": _format_value(dispositivo.poblacion_destinataria_otro)},
                    {"label": "Franja etaria", "value": _format_display_list(dispositivo.franja_etaria_destinataria, DispositivoForm.FRANJA_ETARIA_CHOICES), "kind": "list"},
                    {"label": "Tiempo promedio de permanencia", "value": dispositivo.get_tiempo_permanencia_promedio_display() if dispositivo.tiempo_permanencia_promedio else "-"},
                    {"label": "Detalle permanencia", "value": _format_value(dispositivo.tiempo_permanencia_otro)},
                ],
            },
            {
                "titulo": "Modalidad de ingreso",
                "icono": "fas fa-sign-in-alt",
                "items": [
                    {"label": "Modalidad de ingreso", "value": _format_display_list(dispositivo.modalidad_ingreso, DispositivoForm.MODALIDAD_INGRESO_CHOICES), "kind": "list"},
                    {"label": "Detalle modalidad", "value": _format_value(dispositivo.modalidad_ingreso_otro)},
                    {"label": "Documentación para el ingreso", "value": _format_display_list(dispositivo.documentacion_ingreso, DispositivoForm.DOCUMENTACION_INGRESO_CHOICES), "kind": "list"},
                    {"label": "Detalle documentación", "value": _format_value(dispositivo.documentacion_ingreso_otro)},
                    {"label": "Requisitos para el ingreso", "value": _format_display_list(dispositivo.requisitos_ingreso, DispositivoForm.REQUISITOS_INGRESO_CHOICES), "kind": "list"},
                    {"label": "Detalle requisitos", "value": _format_value(dispositivo.requisitos_ingreso_otro)},
                ],
            },
            {
                "titulo": "Servicios brindados",
                "icono": "fas fa-hands-helping",
                "items": [
                    {"label": "Servicios brindados", "value": _format_display_list(dispositivo.servicios_brindados, DispositivoForm.SERVICIOS_BRINDADOS_CHOICES), "kind": "list"},
                    {"label": "Detalle servicios", "value": _format_value(dispositivo.servicios_brindados_otro)},
                    {"label": "Ofrece actividades formativas", "value": dispositivo.get_ofrece_actividades_formativas_display() if dispositivo.ofrece_actividades_formativas else "-"},
                    {"label": "Tipos de actividades formativas", "value": _format_display_list(dispositivo.tipos_actividades_formativas, DispositivoForm.TIPO_ACTIVIDADES_FORMATIVAS_CHOICES), "kind": "list"},
                    {"label": "Detalle actividades", "value": _format_value(dispositivo.tipos_actividades_formativas_otro)},
                    {"label": "Certificación oficial de actividades", "value": dispositivo.get_actividades_certificacion_oficial_display() if dispositivo.actividades_certificacion_oficial else "-"},
                ],
            },
            {
                "titulo": "Sistema de registro de personas usuarias",
                "icono": "fas fa-clipboard-list",
                "items": [
                    {"label": "Registra información de personas", "value": dispositivo.get_registra_informacion_personas_display() if dispositivo.registra_informacion_personas else "-"},
                    {"label": "Modo de registro", "value": dispositivo.get_modo_registro_display() if dispositivo.modo_registro else "-"},
                    {"label": "Detalle modo de registro", "value": _format_value(dispositivo.modo_registro_otro)},
                    {"label": "Tipo de información registrada", "value": _format_display_list(dispositivo.tipo_informacion_registrada, DispositivoForm.TIPO_INFO_REGISTRADA_CHOICES), "kind": "list"},
                    {"label": "Detalle información", "value": _format_value(dispositivo.tipo_informacion_registrada_otro)},
                ],
            },
            {
                "titulo": "Infraestructura y necesidades",
                "icono": "fas fa-tools",
                "items": [
                    {"label": "Infraestructura disponible", "value": _format_display_list(dispositivo.infraestructura_disponible, DispositivoForm.INFRAESTRUCTURA_DISPONIBLE_CHOICES), "kind": "list"},
                    {"label": "Detalle infraestructura", "value": _format_value(dispositivo.infraestructura_disponible_otro)},
                    {"label": "Infraestructura de accesibilidad", "value": _format_display_list(dispositivo.infraestructura_accesibilidad, DispositivoForm.INFRAESTRUCTURA_ACCESIBILIDAD_CHOICES), "kind": "list"},
                    {"label": "Detalle accesibilidad", "value": _format_value(dispositivo.infraestructura_accesibilidad_otro)},
                    {"label": "Principales limitaciones", "value": _format_value(dispositivo.principales_limitaciones), "wide": True},
                    {"label": "Necesidades prioritarias", "value": _format_value(dispositivo.necesidades_prioritarias), "wide": True},
                ],
            },
            {
                "titulo": "Articulaciones institucionales",
                "icono": "fas fa-network-wired",
                "items": [
                    {"label": "Articulaciones institucionales", "value": _format_display_list(dispositivo.articulaciones_institucionales, DispositivoForm.ARTICULACIONES_CHOICES), "kind": "list"},
                    {"label": "Detalle articulaciones", "value": _format_value(dispositivo.articulaciones_institucionales_otro)},
                ],
            },
            {
                "titulo": "Observaciones y documentación",
                "icono": "fas fa-file-alt",
                "items": [
                    {"label": "Observaciones adicionales", "value": _format_value(dispositivo.observaciones_adicionales), "wide": True},
                    {"label": "Documentación del dispositivo", "value": _format_file(dispositivo.documentacion_dispositivo), "kind": "file"},
                    {"label": "Documentación adicional 1", "value": _format_file(dispositivo.documentacion_dispositivo_adicional_1), "kind": "file"},
                    {"label": "Documentación adicional 2", "value": _format_file(dispositivo.documentacion_dispositivo_adicional_2), "kind": "file"},
                    {"label": "Documentación adicional 3", "value": _format_file(dispositivo.documentacion_dispositivo_adicional_3), "kind": "file"},
                    {"label": "Documentación adicional 4", "value": _format_file(dispositivo.documentacion_dispositivo_adicional_4), "kind": "file"},
                ],
            },
        ]
        return context


class DispositivoCreateView(LoginRequiredMixin, CreateView):
    model = Dispositivo
    form_class = DispositivoForm
    template_name = "dispositivos_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = [
            {"text": "Dispositivos", "url": reverse("dispositivos_listar")},
            {"text": "Nuevo dispositivo"},
        ]
        return context

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = [
            {"text": "Dispositivos", "url": reverse("dispositivos_listar")},
            {"text": self.object.nombre_institucion, "url": reverse("dispositivos_detalle", kwargs={"pk": self.object.pk})},
            {"text": "Editar"},
        ]
        return context

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

    def form_valid(self, form):
        self.object = self.get_object()
        delete_dispositivo(self.object)
        messages.success(self.request, "Dispositivo eliminado correctamente.")
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse("dispositivos_listar")
