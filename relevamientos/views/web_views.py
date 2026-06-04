from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models as dj_models
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)
from django.views.generic.base import View

from comedores.models import Comedor
from core.soft_delete.view_helpers import SoftDeleteDeleteViewMixin
from relevamientos.form import RelevamientoForm
from relevamientos.helpers import RelevamientoFormManager
from relevamientos.models import PrimerSeguimiento, Relevamiento
from relevamientos.service import RelevamientoService


class RelevamientoCreateView(LoginRequiredMixin, CreateView):
    model = Relevamiento
    form_class = RelevamientoForm
    template_name = "relevamiento_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["comedor_pk"] = self.kwargs["comedor_pk"]
        return kwargs

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        forms = RelevamientoFormManager.build_forms(
            self.request.POST if self.request.method == "POST" else None
        )
        data.update(forms)
        data["comedor"] = RelevamientoFormManager.get_comedor_context(
            self.kwargs["comedor_pk"]
        )
        self._context_data = data
        return data

    def form_valid(self, form):
        context = getattr(self, "_context_data", None)
        if context is None:
            context = self.get_context_data()
        forms = {k: context[k] for k in RelevamientoFormManager.FORM_CLASSES}
        validation_results = RelevamientoFormManager.validate_forms(forms)
        if RelevamientoFormManager.all_valid(forms, validation_results):
            self.object = RelevamientoService.populate_relevamiento(form, forms)
            return redirect(
                "relevamiento_detalle",
                comedor_pk=int(self.object.comedor.id),
                pk=int(self.object.id),
            )
        RelevamientoFormManager.show_form_errors(
            self.request, forms, validation_results
        )
        return self.form_invalid(form)

    def error_message(self, forms):
        for form_name, form_instance in forms.items():
            if not form_instance.is_valid():
                messages.error(
                    self.request, f"Errores en {form_name}: {form_instance.errors}"
                )


class RelevamientoListView(LoginRequiredMixin, ListView):
    model = Relevamiento
    template_name = "relevamiento_list.html"
    context_object_name = "relevamientos"

    def get_queryset(self):
        comedor = self.kwargs["comedor_pk"]
        return (
            Relevamiento.objects.filter(comedor=comedor)
            .select_related("primer_seguimiento")
            .order_by("-estado", "-id")
        )

    def post(self, request, *args, **kwargs):
        if not request.user.has_perm("relevamientos.change_relevamiento"):
            messages.error(request, "No tiene permisos para editar el Número de IF.")
            return redirect("relevamientos", comedor_pk=kwargs["comedor_pk"])

        relevamiento_id = request.POST.get("relevamiento_id")
        numero_if = (request.POST.get("numero_if") or "").strip()
        Relevamiento.objects.filter(
            id=relevamiento_id,
            comedor_id=kwargs["comedor_pk"],
        ).update(numero_if=numero_if or None)
        messages.success(request, "Número de IF actualizado correctamente.")
        return redirect("relevamientos", comedor_pk=kwargs["comedor_pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comedor"] = Comedor.objects.values(
            "id",
            "nombre",
            "provincia__nombre",
            "localidad__nombre",
            "municipio__nombre",
        ).get(pk=self.kwargs["comedor_pk"])

        items = []
        for rel in context["relevamientos"]:
            items.append(
                {
                    "id": rel.id,
                    "fecha": rel.fecha_visita,
                    "estado": rel.estado,
                    "numero_if": rel.numero_if,
                    "is_child": False,
                    "parent_id": None,
                }
            )
            seguimiento = _get_primer_seguimiento(rel)
            if seguimiento is not None:
                items.append(
                    {
                        "id": seguimiento.id,
                        "fecha": seguimiento.fecha_hora,
                        "estado": seguimiento.estado,
                        "numero_if": None,
                        "is_child": True,
                        "parent_id": rel.id,
                    }
                )
        context["relevamientos_items"] = items
        return context


def _get_primer_seguimiento(relevamiento):
    try:
        return relevamiento.primer_seguimiento
    except PrimerSeguimiento.DoesNotExist:
        return None


class RelevamientoDetailView(LoginRequiredMixin, DetailView):
    model = Relevamiento
    template_name = "relevamiento_detail.html"
    context_object_name = "relevamiento"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        # Optimización: Usar self.object en lugar de nueva query
        relevamiento = self.object

        timeline_qs = (
            Relevamiento.objects.filter(comedor=relevamiento.comedor)
            .only("id", "fecha_visita", "estado")
            .order_by("fecha_visita", "id")
        )
        timeline_items = []
        for idx, item in enumerate(timeline_qs):
            estado = item.estado or ""
            is_finalizado = estado in {"Finalizado", "Finalizado/Excepciones"}
            is_pendiente = estado in {"Pendiente", "Visita pendiente"}
            card_class = (
                "active"
                if item.id == relevamiento.id
                else (
                    "finalizado"
                    if is_finalizado
                    else "pendiente" if is_pendiente else ""
                )
            )
            status_class = (
                "finalizado" if is_finalizado else "pendiente" if is_pendiente else ""
            )
            timeline_items.append(
                {
                    "id": item.id,
                    "step": idx + 1,
                    "fecha": item.fecha_visita,
                    "estado": item.estado or "Sin información",
                    "card_class": card_class,
                    "status_class": status_class,
                }
            )

        if len(timeline_items) > 3:
            current_index = next(
                (
                    index
                    for index, item in enumerate(timeline_items)
                    if item["id"] == relevamiento.id
                ),
                len(timeline_items) - 1,
            )
            start = max(current_index - 1, 0)
            end = start + 3
            if end > len(timeline_items):
                end = len(timeline_items)
                start = max(end - 3, 0)
            timeline_items = timeline_items[start:end]

        # Crear un diccionario para los datos adicionales del relevamiento
        relevamiento_data = {}
        relevamiento_data["gas"] = (
            RelevamientoService.separate_string(
                relevamiento.espacio.cocina.abastecimiento_combustible.all()
            )
            if relevamiento.espacio
            else None
        )

        # Optimización: Usar select_related, prestacion ya está cargada
        context["prestacion"] = relevamiento.prestacion

        # Optimización: Todas las relaciones ya están prefetched
        relevamiento_data["donaciones"] = (
            RelevamientoService.separate_string(
                relevamiento.recursos.recursos_donaciones_particulares.all()
            )
            if relevamiento.recursos
            else None
        )

        relevamiento_data["nacional"] = (
            RelevamientoService.separate_string(
                relevamiento.recursos.recursos_estado_nacional.all()
            )
            if relevamiento.recursos
            else None
        )

        relevamiento_data["provincial"] = (
            RelevamientoService.separate_string(
                relevamiento.recursos.recursos_estado_provincial.all()
            )
            if relevamiento.recursos
            else None
        )

        relevamiento_data["municipal"] = (
            RelevamientoService.separate_string(
                relevamiento.recursos.recursos_estado_municipal.all()
            )
            if relevamiento.recursos
            else None
        )

        relevamiento_data["otras"] = (
            RelevamientoService.separate_string(
                relevamiento.recursos.recursos_otros.all()
            )
            if relevamiento.recursos
            else None
        )

        relevamiento_data["Entregas"] = (
            RelevamientoService.separate_string(
                relevamiento.punto_entregas.frecuencia_recepcion_mercaderias.all()
            )
            if relevamiento.punto_entregas
            else None
        )

        # Agregar los datos adicionales al contexto
        context["relevamiento_data"] = relevamiento_data
        context["relevamientos_timeline"] = timeline_items

        return context

    def get_object(self, queryset=None):
        # Optimización: Retornar objeto completo con todas las relaciones optimizadas
        return (
            Relevamiento.objects.select_related(
                "comedor",
                "comedor__referente",
                "comedor__provincia",
                "comedor__municipio",
                "comedor__localidad",
                "prestacion",
                "espacio",
                "espacio__cocina",
                "espacio__cocina__abastecimiento_agua",
                "espacio__tipo_espacio_fisico",
                "espacio__prestacion",
                "espacio__prestacion__desague_hinodoro",
                "espacio__prestacion__gestion_quejas",
                "espacio__prestacion__frecuencia_limpieza",
                "recursos",
                "recursos__frecuencia_donaciones_particulares",
                "recursos__frecuencia_estado_nacional",
                "recursos__frecuencia_estado_provincial",
                "recursos__frecuencia_estado_municipal",
                "recursos__frecuencia_otros",
                "colaboradores",
                "colaboradores__cantidad_colaboradores",
                "compras",
                "anexo",
                "anexo__tipo_insumo",
                "anexo__frecuencia_insumo",
                "anexo__tecnologia",
                "anexo__acceso_comedor",
                "anexo__distancia_transporte",
                "punto_entregas",
                "funcionamiento",
                "funcionamiento__modalidad_prestacion",
                "responsable_relevamiento",
                "excepcion",
            )
            .prefetch_related(
                "espacio__cocina__abastecimiento_combustible",
                "recursos__recursos_donaciones_particulares",
                "recursos__recursos_estado_nacional",
                "recursos__recursos_estado_provincial",
                "recursos__recursos_estado_municipal",
                "recursos__recursos_otros",
                "punto_entregas__frecuencia_recepcion_mercaderias",
            )
            .get(pk=self.kwargs["pk"])
        )


class RelevamientoUpdateView(LoginRequiredMixin, UpdateView):
    model = Relevamiento
    form_class = RelevamientoForm
    template_name = "relevamiento_form.html"
    success_url = reverse_lazy("relevamiento_lista")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["comedor_pk"] = self.kwargs["comedor_pk"]
        return kwargs

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        instance_map = {}
        if hasattr(self, "object") and self.object:
            for name in RelevamientoFormManager.FORM_CLASSES:
                base_name = name.split("_form", maxsplit=1)[0]
                instance_map[name] = getattr(self.object, base_name, None)
            if self.object.espacio:
                instance_map["espacio_cocina_form"] = getattr(
                    self.object.espacio, "cocina", None
                )
                instance_map["espacio_prestacion_form"] = getattr(
                    self.object.espacio, "prestacion", None
                )
        forms = RelevamientoFormManager.build_forms(
            self.request.POST if self.request.method == "POST" else None,
            instance_map=instance_map,
        )
        data.update(forms)
        data["comedor"] = RelevamientoFormManager.get_comedor_context(
            self.kwargs["comedor_pk"]
        )
        data["responsable"] = getattr(self.object, "responsable", None)
        self._context_data = data
        return data

    def form_valid(self, form):
        context = getattr(self, "_context_data", None)
        if context is None:
            context = self.get_context_data()
        forms = {k: context[k] for k in RelevamientoFormManager.FORM_CLASSES}
        validation_results = RelevamientoFormManager.validate_forms(forms)
        if RelevamientoFormManager.all_valid(forms, validation_results):
            self.object = RelevamientoService.populate_relevamiento(form, forms)
            return redirect(
                "relevamiento_detalle",
                comedor_pk=int(self.object.comedor.id),
                pk=int(self.object.id),
            )
        RelevamientoFormManager.show_form_errors(
            self.request, forms, validation_results
        )
        return self.form_invalid(form)

    def error_message(self, forms):
        for form_name, form_instance in forms.items():
            if not form_instance.is_valid():
                messages.error(
                    self.request, f"Errores en {form_name}: {form_instance.errors}"
                )


class RelevamientoDeleteView(
    SoftDeleteDeleteViewMixin,
    LoginRequiredMixin,
    DeleteView,
):
    model = Relevamiento
    template_name = "relevamiento_confirm_delete.html"
    context_object_name = "relevamiento"
    success_message = "Relevamiento dado de baja correctamente."

    def get_success_url(self):
        comedor = self.object.comedor

        return reverse_lazy("comedor_detalle", kwargs={"pk": comedor.id})


PRIMER_SEGUIMIENTO_BLOQUES = (
    ("funcionamiento", "Funcionamiento"),
    ("servicios_basicos", "Servicios básicos"),
    ("almacenamiento_alimentos", "Almacenamiento de alimentos"),
    ("condiciones_higiene", "Condiciones de higiene"),
    ("tareas_comedor", "Tareas en el comedor"),
    ("recursos", "Recursos"),
    ("compras", "Compras"),
    ("frecuencia_compra_alimentos", "Frecuencia de compra de alimentos"),
    ("menu", "Menú"),
    ("registro_asistencia", "Registro de asistencia"),
    ("frecuencia_alimentos", "Frecuencia de alimentos"),
    ("actividades_extras", "Actividades extras"),
    ("tarjeta", "Tarjeta"),
    ("rendicion_cuentas", "Rendición de cuentas"),
    ("asistencia_tecnica", "Asistencia técnica"),
    ("cierre", "Cierre"),
)


def _display_value(instance, field):
    raw = getattr(instance, field.name, None)
    if raw is None:
        return None
    if getattr(field, "choices", None):
        getter = getattr(instance, f"get_{field.name}_display", None)
        if callable(getter):
            return getter()
    if isinstance(raw, bool):
        return "Sí" if raw else "No"
    if isinstance(raw, str) and not raw.strip():
        return None
    if isinstance(raw, dj_models.Model):
        return str(raw)
    return raw


def _bloque_campos(instance):
    if instance is None:
        return []
    rows = []
    for field in instance._meta.get_fields():
        if not isinstance(field, dj_models.Field):
            continue
        if field.primary_key or field.auto_created:
            continue
        value = _display_value(instance, field)
        if value is None or value == "":
            continue
        label = (
            str(field.verbose_name).capitalize()
            if field.verbose_name
            else field.name.replace("_", " ").capitalize()
        )
        rows.append({"label": label, "value": value})
    return rows


class PrimerSeguimientoDetailView(LoginRequiredMixin, DetailView):
    model = PrimerSeguimiento
    template_name = "primer_seguimiento_detail.html"
    context_object_name = "seguimiento"

    def get_object(self, queryset=None):
        queryset = PrimerSeguimiento.objects.select_related(
            "id_relevamiento",
            "id_relevamiento__comedor",
            "referente",
            "funcionamiento",
            "servicios_basicos",
            "almacenamiento_alimentos",
            "condiciones_higiene",
            "tareas_comedor",
            "tareas_comedor__tareas_comedor_cant_personas",
            "recursos",
            "recursos__fuente_recursos",
            "compras",
            "compras__fuente_compras",
            "frecuencia_compra_alimentos",
            "menu",
            "menu__modalidad_prestacion_del_dia",
            "registro_asistencia",
            "frecuencia_alimentos",
            "actividades_extras",
            "tarjeta",
            "rendicion_cuentas",
            "asistencia_tecnica",
            "cierre",
        ).prefetch_related("prestaciones", "menu__receta_items")
        return get_object_or_404(
            queryset,
            id_relevamiento_id=self.kwargs["relevamiento_pk"],
            id_relevamiento__comedor_id=self.kwargs["comedor_pk"],
        )

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        seguimiento = self.object
        context["relevamiento"] = seguimiento.id_relevamiento
        context["comedor"] = seguimiento.id_relevamiento.comedor

        bloques = []
        for attr, label in PRIMER_SEGUIMIENTO_BLOQUES:
            instance = getattr(seguimiento, attr, None)
            if instance is None:
                continue
            campos = _bloque_campos(instance)
            if not campos:
                continue
            bloques.append({"key": attr, "label": label, "campos": campos})
        context["bloques"] = bloques

        context["prestaciones"] = list(seguimiento.prestaciones.all())
        menu = seguimiento.menu
        context["receta_items"] = (
            list(menu.receta_items.all()) if menu is not None else []
        )
        return context


class PrimerSeguimientoEliminarView(LoginRequiredMixin, View):
    """Borrado del primer seguimiento desde la UI.

    La confirmacion se hace via modal en el detalle del relevamiento; por eso
    no exponemos GET y solo aceptamos POST. El borrado dispara la signal
    pre_delete que envia la baja al endpoint de GESTIONAR.
    """

    http_method_names = ["post"]

    def post(self, request, comedor_pk, relevamiento_pk):
        seguimiento = get_object_or_404(
            PrimerSeguimiento.objects.select_related("id_relevamiento"),
            id_relevamiento_id=relevamiento_pk,
            id_relevamiento__comedor_id=comedor_pk,
        )
        seguimiento.delete()
        messages.success(request, "Primer seguimiento eliminado correctamente.")
        return redirect(
            reverse(
                "relevamiento_detalle",
                kwargs={"comedor_pk": comedor_pk, "pk": relevamiento_pk},
            )
        )
