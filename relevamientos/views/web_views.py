from typing import Any

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from comedores.models import Comedor
from relevamientos.form import RelevamientoForm
from relevamientos.helpers import RelevamientoFormManager
from relevamientos.models import Relevamiento
from relevamientos.service import RelevamientoService


class RelevamientoCreateView(CreateView):
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


class RelevamientoListView(ListView):
    model = Relevamiento
    template_name = "relevamiento_list.html"
    context_object_name = "relevamientos"

    def get_queryset(self):
        comedor = self.kwargs["comedor_pk"]
        return (
            Relevamiento.objects.filter(comedor=comedor)
            .order_by("-estado", "-id")
            .values("id", "fecha_visita", "estado")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comedor"] = Comedor.objects.values(
            "id",
            "nombre",
            "provincia__nombre",
            "localidad__nombre",
            "municipio__nombre",
        ).get(pk=self.kwargs["comedor_pk"])

        return context


class RelevamientoDetailView(DetailView):
    model = Relevamiento
    template_name = "relevamiento_detail.html"
    context_object_name = "relevamiento"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        # Optimización: Usar self.object en lugar de nueva query
        relevamiento = self.object

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

        return context

    def get_object(self, queryset=None):
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


class RelevamientoUpdateView(UpdateView):
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


class RelevamientoDeleteView(DeleteView):
    model = Relevamiento
    template_name = "relevamiento_confirm_delete.html"
    context_object_name = "relevamiento"

    def get_success_url(self):
        comedor = self.object.comedor

        return reverse_lazy("comedor_detalle", kwargs={"pk": comedor.id})
