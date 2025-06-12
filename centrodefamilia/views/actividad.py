from django.views.generic import ListView, CreateView
from django.urls import reverse
from django.contrib import messages
from centrodefamilia.models import ActividadCentro
from centrodefamilia.forms import ActividadCentroForm
from django.views.generic import DetailView
from centrodefamilia.models import ParticipanteActividad
from django.utils.decorators import method_decorator
from centrodefamilia.utils.decorators import group_required


class ActividadCentroListView(ListView):
    model = ActividadCentro
    template_name = "centros/actividadcentro_list.html"
    context_object_name = "actividades"

    def get_queryset(self):
        qs = super().get_queryset()
        centro_id = self.request.GET.get("centro")
        if centro_id:
            qs = qs.filter(centro_id=centro_id)
        return qs

@method_decorator(group_required("superadmin", "el"), name='dispatch')
class ActividadCentroCreateView(CreateView):
    model = ActividadCentro
    form_class = ActividadCentroForm
    template_name = "centros/actividadcentro_form.html"

    def get_initial(self):
        initial = super().get_initial()
        centro_id = self.kwargs.get("centro_id") or self.request.GET.get("centro")
        if centro_id:
            initial["centro"] = centro_id
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.kwargs.get("centro_id"):
            form.fields.pop("centro", None)
        return form

    def form_valid(self, form):
        centro_id = self.kwargs.get("centro_id") or self.request.GET.get("centro")
        if centro_id:
            form.instance.centro_id = centro_id
        messages.success(self.request, "Actividad creada correctamente.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "actividadcentro_detail",
            kwargs={
                "centro_id": self.object.centro.id,
                "pk": self.object.pk
            }
        )



class ActividadCentroDetailView(DetailView):
    model = ActividadCentro
    template_name = "centros/actividadcentro_detail.html"
    context_object_name = "actividad"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["participantes"] = ParticipanteActividad.objects.filter(
            actividad_centro=self.object
        )
        return context
