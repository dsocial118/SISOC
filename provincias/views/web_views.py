from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, DeleteView
from django.shortcuts import redirect
from provincias.models import Proyecto
from provincias.forms import ProyectoForm
from usuarios.models import Usuarios

class ProyectoCreateView(CreateView):
    model = Proyecto
    form_class = ProyectoForm
    template_name = 'proyecto_form.html'

    def form_valid(self, form):
        form.instance.creador = Usuarios.objects.get(pk=self.request.user.id)
        tipo_anexo = form.cleaned_data['tipo_anexo']
        if tipo_anexo == 'SOCIO_PRODUCTIVO':
            return redirect('socio_productivo_create')
        elif tipo_anexo == 'FORMACION':
            return redirect('formacion_create')
        
        return  super().form_valid(form)


class ProyectoListView(ListView):
    model = Proyecto
    template_name = 'proyecto_list.html'
    context_object_name = 'proyectos'
    paginate_by = 10  # Paginación de 10 elementos por página

class ProyectoUpdateView(UpdateView):
    model = Proyecto
    form_class = ProyectoForm
    template_name = 'proyecto_form.html'

class ProyectoDeleteView(DeleteView):
    model = Proyecto
    template_name = 'proyecto_confirm_delete.html'
    success_url = reverse_lazy('proyecto_list')