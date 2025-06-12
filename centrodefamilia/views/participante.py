from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from centrodefamilia.models import ParticipanteActividad
from centrodefamilia.forms import ParticipanteActividadForm

class ParticipanteActividadListView(ListView):
    model = ParticipanteActividad
    template_name = "centros/participanteactividad_list.html"
    context_object_name = "participantes"

    def get_queryset(self):
        qs = super().get_queryset()
        actividad_id = self.kwargs.get('actividad_id')
        if actividad_id:
            qs = qs.filter(actividad_centro_id=actividad_id)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['actividad_id'] = self.kwargs.get('actividad_id')
        return context


class ParticipanteActividadCreateView(CreateView):
    model = ParticipanteActividad
    form_class = ParticipanteActividadForm
    template_name = "centros/participanteactividad_form.html"

    def get_initial(self):
        initial = super().get_initial()
        actividad_id = self.kwargs.get('actividad_id')
        if actividad_id:
            initial['actividad_centro'] = actividad_id
        return initial

    def get_success_url(self):
        actividad_id = self.kwargs.get('actividad_id')
        return reverse_lazy("participanteactividad_list", kwargs={"actividad_id": actividad_id})

    def form_valid(self, form):
        messages.success(self.request, "Participante cargado correctamente.")
        return super().form_valid(form)
