from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from centrodefamilia.models import ActividadCentro, Centro
from centrodefamilia.form import ActividadCentroForm
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from centrodefamilia.services.centro_service import puede_operar


class ActividadCentroListView(LoginRequiredMixin, ListView):
    model = ActividadCentro
    template_name = "centros/actividadcentro_list.html"
    context_object_name = "actividades"

    def get_queryset(self):
        return ActividadCentro.objects.filter(centro__id=self.kwargs['centro_id'])

class ActividadCentroCreateView(LoginRequiredMixin, CreateView):
    model = ActividadCentro
    form_class = ActividadCentroForm
    template_name = "centros/actividadcentro_form.html"

    def dispatch(self, request, *args, **kwargs):
        centro = get_object_or_404(Centro, id=self.kwargs["centro_id"])
        if not puede_operar(centro):
            messages.error(request, "El centro no puede operar porque su faro está inactivo.")
            return redirect("actividadcentro_listar", centro_id=centro.id)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy("actividadcentro_listar", kwargs={"centro_id": self.kwargs["centro_id"]})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        centro = get_object_or_404(Centro, id=self.kwargs["centro_id"])
        kwargs['centro'] = centro
        return kwargs

    def form_valid(self, form):
        centro = get_object_or_404(Centro, id=self.kwargs["centro_id"])
        form.instance.centro = centro
        messages.success(self.request, "Actividad registrada correctamente.")
        return super().form_valid(form)
