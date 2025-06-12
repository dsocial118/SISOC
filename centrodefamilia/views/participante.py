from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from centrodefamilia.models import ParticipanteActividad
from centrodefamilia.forms import ParticipanteActividadForm


class ParticipanteActividadCreateView(CreateView):
    model = ParticipanteActividad
    form_class = ParticipanteActividadForm
    template_name = "centros/participanteactividad_form.html"

    def get_initial(self):
        initial = super().get_initial()
        actividad_id = self.kwargs.get("actividad_id")
        if actividad_id:
            initial["actividad_centro"] = actividad_id
        return initial

    def get_success_url(self):
        centro_id = self.kwargs.get("centro_id")
        actividad_id = self.kwargs.get("actividad_id")
        return reverse_lazy("actividadcentro_detail", kwargs={
            "centro_id": centro_id,
            "pk": actividad_id
        })


    def form_valid(self, form):
        messages.success(self.request, "Participante cargado correctamente.")
        return super().form_valid(form)
