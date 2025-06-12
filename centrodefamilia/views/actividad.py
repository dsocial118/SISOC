from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from centrodefamilia.models import ActividadCentro
from centrodefamilia.forms import ActividadCentroForm

class ActividadCentroListView(ListView):
    model = ActividadCentro
    template_name = "centros/actividadcentro_list.html"
    context_object_name = "actividades"

    def get_queryset(self):
        qs = super().get_queryset()
        centro_id = self.request.GET.get('centro')
        if centro_id:
            qs = qs.filter(centro_id=centro_id)
        return qs

class ActividadCentroCreateView(CreateView):
    model = ActividadCentro
    form_class = ActividadCentroForm
    template_name = "centros/actividadcentro_form.html"
    success_url = reverse_lazy("actividadcentro_list")

    def get_initial(self):
        initial = super().get_initial()
        centro_id = self.kwargs.get('centro_id') or self.request.GET.get('centro')
        if centro_id:
            initial['centro'] = centro_id
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Ocultar el campo 'centro' en el formulario si viene por la URL
        if self.kwargs.get('centro_id'):
            form.fields.pop('centro', None)
        return form

    def form_valid(self, form):
        centro_id = self.kwargs.get('centro_id') or self.request.GET.get('centro')
        if centro_id:
            form.instance.centro_id = centro_id
        messages.success(self.request, "Actividad creada correctamente.")
        return super().form_valid(form)

