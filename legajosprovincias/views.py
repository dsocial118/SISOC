import calendar  # pylint: disable=too-many-lines
import json

# Configurar el locale para usar el idioma español
import locale
import logging
from datetime import date, datetime, timedelta

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import transaction
from django.db.models import Case, IntegerField, Q, Value, When
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy

# Paginacion
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
    View,
)

from usuarios.mixins import PermisosMixin
from usuarios.utils import recortar_imagen

from legajosprovincias.forms import (
    LegajosProvinciasForm,
    PresupuestoForm,
    HistorialPresupuestoForm,
    ProyectosForm,
    DocumentacionArchivosForm,
)

from legajosprovincias.models import (
    LegajosProvincias,
    Presupuesto,
    Proyectos,
    DocumentacionArchivos,
    HistorialPresupuesto
)
locale.setlocale(locale.LC_ALL, "es_AR.UTF-8")

logger = logging.getLogger("django")

ROL_ADMIN = "usuarios.rol_admin"


class LegajosProvinciasListView(PermisosMixin, ListView):
    """Vista para listar las provincias de los legajos."""

    permission_required = ROL_ADMIN
    model = LegajosProvincias
    template_name = "legajosprovincias/lista.html"
    context_object_name = "legajosprovincias"
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.order_by("nombre")

class LegajosProvinciasCreateView(PermisosMixin, SuccessMessageMixin, CreateView):
    """Vista para crear una provincia de los legajos."""

    permission_required = ROL_ADMIN
    model = LegajosProvincias
    form_class = LegajosProvinciasForm
    template_name = "legajosprovincias/legajosprovincias_form.html"
    def form_valid(self, form):
        messages.success(self.request, "Provincia creada con éxito.")
        return super().form_valid(form)

class LegajosProvinciasUpdateView(PermisosMixin, SuccessMessageMixin, UpdateView):
    """Vista para editar una provincia de los legajos."""

    permission_required = ROL_ADMIN
    model = LegajosProvincias
    form_class = LegajosProvinciasForm
    template_name = "legajosprovincias/formulario.html"
    def form_valid(self, form):
        messages.success(self.request, "Provincia actualizada con éxito.")
        return super().form_valid(form)

class LegajosProvinciasDeleteView(PermisosMixin, DeleteView):
    """Vista para eliminar una provincia de los legajos."""

    permission_required = ROL_ADMIN
    model = LegajosProvincias
    template_name = "legajosprovincias/legajosprovincias_confirm_delete.html"

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Provincia eliminada")

class LegajosProvinciasDetailView(PermisosMixin, DetailView):
    """Vista para ver los detalles de una provincia de los legajos."""

    permission_required = ROL_ADMIN
    model = LegajosProvincias
    template_name = "legajosprovincias/legajosprovincias_detail.html"

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        context["provincia"] = LegajosProvincias.objects.filter(pk=pk).first()
        return context

class LegajosProvinciasProyectosListView(PermisosMixin, ListView):
    """Vista para listar los proyectos de una provincia de los legajos."""

    permission_required = ROL_ADMIN
    model = Proyectos
    template_name = "legajosprovincias/proyectos_list.html"
    context_object_name = "proyectos"
    paginate_by = 10

    def get_queryset(self):
        pk = self.kwargs["pk"]
        queryset = super().get_queryset()
        return queryset.filter(provincia_id=pk).order_by("proyecto")

class LegajosProvinciasProyectosDetailView(PermisosMixin, DetailView):
    """Vista para ver los detalles de un proyecto de una provincia de los legajos."""

    permission_required = ROL_ADMIN
    model = Proyectos
    template_name = "legajosprovincias/proyectos_detail.html"

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        context["proyecto"] = Proyectos.objects.filter(pk=pk).first()
        return context

class LegajosProvinciasPresupuestoListView(PermisosMixin, ListView):
    """Vista para listar los presupuestos de una provincia de los legajos."""

    permission_required = ROL_ADMIN
    model = Presupuesto
    template_name = "legajosprovincias/presupuesto_list.html"
    context_object_name = "presupuestos"
    paginate_by = 10

    def get_queryset(self):
        pk = self.kwargs["pk"]
        queryset = super().get_queryset()
        return queryset.filter(provincia_id=pk).order_by("fecha_creacion")

class LegajosProvinciasPresupuestoDetailView(PermisosMixin, DetailView):
    """Vista para ver los detalles de un presupuesto de una provincia de los legajos."""

    permission_required = ROL_ADMIN
    model = Presupuesto
    template_name = "legajosprovincias/presupuesto_detail.html"

    def get_context_data(self, **kwargs):
        pk = self.kwargs["pk"]
        context = super().get_context_data(**kwargs)
        context["presupuesto"] = Presupuesto.objects.filter(pk=pk).first()
        return context

class LegajosProvinciasPresupuestoUpdateView(PermisosMixin, SuccessMessageMixin, UpdateView):
    """Vista para editar un presupuesto de una provincia de los legajos."""

    permission_required = ROL_ADMIN
    model = Presupuesto
    form_class = PresupuestoForm
    template_name = "legajosprovincias/presupuesto_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Presupuesto actualizado con éxito.")
        return super().form_valid(form)

class LegajosProvinciasPresupuestoDeleteView(PermisosMixin, DeleteView):
    """Vista para eliminar un presupuesto de una provincia de los legajos."""

    permission_required = ROL_ADMIN
    model = Presupuesto
    template_name = "legajosprovincias/presupuesto_confirm_delete.html"

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Presupuesto eliminado")

class LegajosProvinciasPresupuestoHistorialView(PermisosMixin, ListView):
    """Vista para ver el historial de un presupuesto de una provincia de los legajos."""

    permission_required = ROL_ADMIN
    model = Presupuesto
    template_name = "legajosprovincias/presupuesto_historial.html"
    context_object_name = "historial"
    paginate_by = 10

    def get_queryset(self):
        pk = self.kwargs["pk"]
        queryset = super().get_queryset()
        return queryset.filter(provincia_id=pk).order_by("fecha_creacion")
