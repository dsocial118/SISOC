from typing import Any
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from comedores.forms.comedor_form import ReferenteForm
from comedores.models import Comedor
from relevamientos.form import (
    AnexoForm,
    ColaboradoresForm,
    EspacioCocinaForm,
    EspacioForm,
    EspacioPrestacionForm,
    FuenteComprasForm,
    FuenteRecursosForm,
    FuncionamientoPrestacionForm,
    PrestacionForm,
    PuntosEntregaForm,
    RelevamientoForm,
)
from relevamientos.helpers import RelevamientoFormManager
from relevamientos.models import Prestacion, Relevamiento
from relevamientos.service import RelevamientoService
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)


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
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        forms = {k: context[k] for k in RelevamientoFormManager.FORM_CLASSES.keys()}
        if RelevamientoFormManager.all_valid(forms):
            self.object = RelevamientoService.populate_relevamiento(form, forms)
            return redirect(
                "relevamiento_detalle",
                comedor_pk=int(self.object.comedor.id),
                pk=int(self.object.id),
            )
        else:
            self.error_message(forms)
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

        relevamiento = Relevamiento.objects.get(pk=self.get_object()["id"])
        context["relevamiento"]["gas"] = (
            RelevamientoService.separate_string(
                relevamiento.espacio.cocina.abastecimiento_combustible.all()
            )
            if relevamiento.espacio
            else None
        )
        context["prestacion"] = (
            Prestacion.objects.get(pk=relevamiento.prestacion.id)
            if relevamiento.prestacion
            else None
        )
        context["relevamiento"]["donaciones"] = (
            RelevamientoService.separate_string(
                relevamiento.recursos.recursos_donaciones_particulares.all()
            )
            if relevamiento.recursos
            else None
        )

        context["relevamiento"]["nacional"] = (
            RelevamientoService.separate_string(
                relevamiento.recursos.recursos_estado_nacional.all()
            )
            if relevamiento.recursos
            else None
        )

        context["relevamiento"]["provincial"] = (
            RelevamientoService.separate_string(
                relevamiento.recursos.recursos_estado_provincial.all()
            )
            if relevamiento.recursos
            else None
        )

        context["relevamiento"]["municipal"] = (
            RelevamientoService.separate_string(
                relevamiento.recursos.recursos_estado_municipal.all()
            )
            if relevamiento.recursos
            else None
        )

        context["relevamiento"]["otras"] = (
            RelevamientoService.separate_string(
                relevamiento.recursos.recursos_otros.all()
            )
            if relevamiento.recursos
            else None
        )

        context["relevamiento"]["Entregas"] = (
            RelevamientoService.separate_string(
                relevamiento.punto_entregas.frecuencia_recepcion_mercaderias.all()
            )
            if relevamiento.punto_entregas
            else None
        )

        return context

    def get_object(self, queryset=None):
        return RelevamientoService.get_relevamiento_detail_object(self.kwargs["pk"])


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
            for name in RelevamientoFormManager.FORM_CLASSES.keys():
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
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        forms = {k: context[k] for k in RelevamientoFormManager.FORM_CLASSES.keys()}
        if RelevamientoFormManager.all_valid(forms):
            self.object = RelevamientoService.populate_relevamiento(form, forms)
            return redirect(
                "relevamiento_detalle",
                comedor_pk=int(self.object.comedor.id),
                pk=int(self.object.id),
            )
        else:
            self.error_message(forms)
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
