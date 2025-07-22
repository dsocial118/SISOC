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
from relevamientos.models import Relevamiento
from core.models import Prestacion
from relevamientos.service import RelevamientoService
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
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

        relevamiento = self.object

        prestaciones = Prestacion.objects.filter(id__in=relevamiento.prestaciones.all())
        context["prestacion"] = RelevamientoService.build_prestacion_compat(
            prestaciones
        )

        context["relevamiento_data"] = RelevamientoService.build_detail_extra_data(
            relevamiento
        )

        return context

    def get_object(self, queryset=None):
        return (
            Relevamiento.objects.select_related(
                "comedor",
                "comedor__referente",
                "comedor__provincia",
                "comedor__municipio",
                "comedor__localidad",
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
                "prestaciones",
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


class RelevamientoDeleteView(DeleteView):
    model = Relevamiento
    template_name = "relevamiento_confirm_delete.html"
    context_object_name = "relevamiento"

    def get_success_url(self):
        comedor = self.object.comedor

        return reverse_lazy("comedor_detalle", kwargs={"pk": comedor.id})


# Create your views here.
