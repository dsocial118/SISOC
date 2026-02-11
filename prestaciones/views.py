from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.forms import ValidationError
from django.http import HttpResponseRedirect, JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from prestaciones.models import Prestacion
from prestaciones.forms import PrestacionForm

class PrestacionListView(LoginRequiredMixin, ListView):
    model = Prestacion
    template_name = "prestacion_list.html"
    context_object_name = "prestacion"
    paginate_by = 10

class PrestacionCreateView(LoginRequiredMixin, CreateView):
    model = Prestacion
    form_class = PrestacionForm
    template_name = "prestacion_form.html"
    success_url = reverse_lazy("prestacion")

    def form_valid(self, form):
        obj = form.save(commit=False)
        if not getattr(obj, "usuario_creador", None):
            obj.usuario_creador = self.request.user
        obj.save()
        self.object = obj
        messages.success(self.request, "Prestación creada correctamente.")
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = [
            {"name": "Prestaciones", "url": reverse("prestacion")},
            {"name": "Crear Prestación"},
        ]
        context["back_button"] = reverse("prestacion")
        context["action_buttons"] = []
        context["hidden_fields_send"] = []
        context["guardar_otro_send"] = False
        return context

class PrestacionUpdateView(LoginRequiredMixin, UpdateView):
    model = Prestacion
    form_class = PrestacionForm
    template_name = "prestacion_form.html"
    success_url = reverse_lazy("prestacion")

class PrestacionDeleteView(LoginRequiredMixin, DeleteView):
    model = Prestacion
    template_name = "prestacion_confirm_delete.html"
    success_url = reverse_lazy("prestacion")

class PrestacionDetailView(LoginRequiredMixin, DetailView):
    model = Prestacion
    template_name = "prestacion_detail.html"
    context_object_name = "prestacion"