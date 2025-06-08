from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from centrodefamilia.models import ParticipanteActividad, ActividadCentro
from centrodefamilia.form import ParticipanteActividadForm
from django.shortcuts import get_object_or_404
from django.contrib import messages

class ParticipanteActividadListView(LoginRequiredMixin, ListView):
    model = ParticipanteActividad
    template_name = "centros/participante_list.html"
    context_object_name = "participantes"

    def get_queryset(self):
        return ParticipanteActividad.objects.filter(actividad_centro__id=self.kwargs['actividadcentro_id'])

class ParticipanteActividadCreateView(LoginRequiredMixin, CreateView):
    model = ParticipanteActividad
    form_class = ParticipanteActividadForm
    template_name = "centros/participante_form.html"

    def get_success_url(self):
        return reverse_lazy("participante_listar", kwargs={"actividadcentro_id": self.kwargs["actividadcentro_id"]})

    def form_valid(self, form):
        actividad_centro = get_object_or_404(ActividadCentro, id=self.kwargs["actividadcentro_id"])
        form.instance.actividad_centro = actividad_centro
        messages.success(self.request, "Participante registrado correctamente.")
        return super().form_valid(form)
