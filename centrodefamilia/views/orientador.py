from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from centrodefamilia.models import Centro, Orientadores
from centrodefamilia.forms import OrientadoresForm
from django.utils.decorators import method_decorator


class OrientadorListView(ListView):
    model = Orientadores
    template_name = "centros/orientador_list.html"
    context_object_name = "orientadores"

    def get_queryset(self):
        self.centro = get_object_or_404(Centro, pk=self.kwargs["centro_id"])
        return Orientadores.objects.filter(centro=self.centro)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["centro"] = self.centro
        return context



class OrientadorCreateView(CreateView):
    model = Orientadores
    form_class = OrientadoresForm
    template_name = "centros/orientador_form.html"

    def form_valid(self, form):
        centro = get_object_or_404(Centro, pk=self.kwargs["centro_id"])
        form.instance.centro = centro
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("orientador_list", kwargs={"centro_id": self.kwargs["centro_id"]})



class OrientadorUpdateView(UpdateView):
    model = Orientadores
    form_class = OrientadoresForm
    template_name = "centros/orientador_form.html"

    def get_success_url(self):
        return reverse_lazy("orientador_list", kwargs={"centro_id": self.object.centro.id})



class OrientadorDeleteView(DeleteView):
    model = Orientadores
    template_name = "centros/orientador_confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy("orientador_list", kwargs={"centro_id": self.object.centro.id})
