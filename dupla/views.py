from django.shortcuts import render

from django.contrib import messages
from django.db.models import Q
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

from dupla.models import Dupla

class DuplaListView(ListView):
    model = Dupla
    template_name = "dupla_list.html"
    context_object_name = "duplas"
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get("busqueda")
        queryset = Dupla.objects.all()

        if query:
            queryset = queryset.filter(
                Q(nombre__icontains=query)
                | Q(tecnico__username__icontains=query)
                | Q(abogado__username__icontains=query)
            )

        return queryset
    
class DuplaCreateView(CreateView):
    model = Dupla
    template_name = "dupla_form.html"
    fields = ["nombre", "tecnico", "fecha", "abogado"]

    def get_success_url(self):
        return reverse("dupla_detalle", kwargs={"pk": self.object.pk})
class DuplaUpdateView(UpdateView):
    model = Dupla
    template_name = "dupla_form.html"
    fields = ["nombre", "tecnico", "fecha", "abogado"]
    success_url = reverse_lazy("dupla_list")
    def get_success_url(self):
        return reverse("dupla_detalle", kwargs={"pk": self.object.pk})
    
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
        self.object = self.get_object()
        self.object.delete()
