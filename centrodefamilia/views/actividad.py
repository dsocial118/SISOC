from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.urls import reverse
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator

from centrodefamilia.models import (
    ActividadCentro,
    Centro,
    ParticipanteActividad,
    Actividad,
)
from centrodefamilia.forms import ActividadCentroForm
from configuraciones.decorators import group_required
from django.http import JsonResponse


class ActividadCentroListView(ListView):
    model = ActividadCentro
    template_name = "centros/actividadcentro_list.html"
    context_object_name = "actividades"

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .select_related("centro", "actividad", "actividad__categoria")
        )
        centro_id = self.request.GET.get("centro")
        if centro_id:
            queryset = queryset.filter(centro_id=centro_id)
        return queryset


class ActividadCentroCreateView(CreateView):
    model = ActividadCentro
    form_class = ActividadCentroForm
    template_name = "centros/actividadcentro_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.centro_id = self.kwargs.get("centro_id") or self.request.GET.get("centro")
        self.centro = get_object_or_404(Centro, pk=self.centro_id)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["centro"] = self.centro
        return kwargs

    def form_valid(self, form):
        form.instance.centro = self.centro
        messages.success(self.request, "La actividad fue creada correctamente.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["centro_id"] = self.centro.pk
        return context

    def get_success_url(self):
        return reverse("centro_detail", kwargs={"pk": self.centro.pk})


class ActividadCentroDetailView(DetailView):
    model = ActividadCentro
    template_name = "centros/actividadcentro_detail.html"
    context_object_name = "actividad"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        actividad = self.get_object()
        participantes = ParticipanteActividad.objects.filter(actividad_centro=actividad)
        cantidad = participantes.count()
        precio = actividad.precio or 0
        context.update(
            {
                "participantes": participantes,
                "precio_total": cantidad * precio,
            }
        )
        return context


class ActividadCentroUpdateView(UpdateView):
    model = ActividadCentro
    form_class = ActividadCentroForm
    template_name = "centros/actividadcentro_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["centro"] = self.get_object().centro
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "La actividad fue actualizada correctamente.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("centro_detail", kwargs={"pk": self.object.centro.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["centro_id"] = self.object.centro.pk
        return context


def cargar_actividades_por_categoria(request):
    categoria_id = request.GET.get("categoria_id")
    actividades = Actividad.objects.filter(categoria_id=categoria_id).values(
        "id", "nombre"
    )
    return JsonResponse(list(actividades), safe=False)
