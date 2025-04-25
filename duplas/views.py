from django.contrib import messages
from django.forms import ValidationError
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)
from duplas.models import Dupla
from duplas.forms import DuplaForm
from duplas.dupla_service import DuplaService
from comedores.services.comedor_service import ComedorService


class DuplaListView(ListView):
    model = Dupla
    template_name = "dupla_list.html"
    context_object_name = "duplas"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["duplas"] = DuplaService.get_all_duplas()
        return context


class DuplaCreateView(CreateView):
    model = Dupla
    template_name = "dupla_form.html"
    form_class = DuplaForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.get_form()
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            try:
                self.object = self.form_valid(form)
                messages.success(request, "Dupla creada correctamente.")
                return HttpResponseRedirect(self.get_success_url())
            except ValidationError as e:
                messages.error(request, str(e))
                return self.form_invalid(form)
        else:
            messages.error(request, "Error al crear la Dupla.")
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse("dupla_list")


class DuplaUpdateView(UpdateView):
    model = Dupla
    template_name = "dupla_form.html"
    fields = ["nombre", "tecnico", "estado", "abogado"]
    success_url = reverse_lazy("dupla_list")

    def get_success_url(self):
        return reverse("dupla_list")


class DuplaDetailView(DetailView):
    model = Dupla
    template_name = "dupla_detail.html"
    context_object_name = "dupla"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["dupla"] = self.object
        return context


class DuplaDeleteView(DeleteView):
    model = Dupla
    template_name = "dupla_confirm_delete.html"
    success_url = reverse_lazy("dupla_list")

    def get_success_url(self):
        return reverse("dupla_list")

    def post(self, request, *args, **kwargs):
        comedor = ComedorService.get_comedor_by_dupla(kwargs["pk"])
        if comedor:
            messages.error(
                request,
                "No se puede eliminar la dupla porque está asignada al comedor "
                + str(comedor.nombre),
            )
            return HttpResponseRedirect(self.get_success_url())
        self.object = self.get_object()
        self.object.delete()
        messages.success(request, "Dupla eliminada correctamente.")
        return HttpResponseRedirect(self.get_success_url())
