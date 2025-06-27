from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from centrodefamilia.models import ParticipanteActividad
from centrodefamilia.forms import ParticipanteActividadForm
from django.http import JsonResponse
from django.template.loader import render_to_string
from ciudadanos.models import Ciudadano


def buscar_ciudadano(request):
    query = request.GET.get("query", "")
    data = {"html": ""}

    if len(query) >= 4:
        ciudadanos = Ciudadano.objects.filter(documento__icontains=query)[:10]
        html = render_to_string(
            "centros/ciudadano_resultado_busqueda.html",
            {"ciudadanos": ciudadanos},
            request=request,
        )
        data["html"] = html

    return JsonResponse(data)


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

    def form_valid(self, form):
        actividad_id = self.kwargs.get("actividad_id")
        form.instance.actividad_centro_id = actividad_id
        messages.success(self.request, "Participante cargado correctamente.")
        return super().form_valid(form)

    def get_success_url(self):
        centro_id = self.kwargs.get("centro_id")
        actividad_id = self.kwargs.get("actividad_id")
        return reverse_lazy(
            "actividadcentro_detail",
            kwargs={"centro_id": centro_id, "pk": actividad_id},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["centro_id"] = self.kwargs.get("centro_id")
        context["actividad_id"] = self.kwargs.get("actividad_id")
        return context
