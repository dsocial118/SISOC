from django.shortcuts import render
from django.views.generic import CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from .models import Dispositivo
from .forms import DispositivoForm

class DispositivoCreateView(CreateView):
    model = Dispositivo
    form_class = DispositivoForm
    template_name = 'dispositivos/dispositivo_form.html'
    success_url = reverse_lazy('dispositivos:listar')

class DispositivoUpdateView(UpdateView):
    model = Dispositivo
    form_class = DispositivoForm
    template_name = 'dispositivos/dispositivo_form.html'
    success_url = reverse_lazy('dispositivos:listar')

class DispositivoDeleteView(DeleteView):
    model = Dispositivo
    template_name = 'dispositivos/dispositivo_confirm_delete.html'
    success_url = reverse_lazy('dispositivos:listar')

class DispositivoListView(TemplateView):
    template_name = 'dispositivos/dispositivo_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['dispositivos'] = Dispositivo.objects.all()
        return context

