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
    template_name = "prestaciones_list.html"
    context_object_name = "prestaciones"
    paginate_by = 10

class PrestacionCreateView(LoginRequiredMixin, CreateView):
    model = Prestacion
    form_class = PrestacionForm
    template_name = "prestacion_form.html"
    success_url = reverse_lazy("prestaciones")

class PrestacionUpdateView(LoginRequiredMixin, UpdateView):
    model = Prestacion
    form_class = PrestacionForm
    template_name = "prestacion_form.html"
    success_url = reverse_lazy("prestaciones")

class PrestacionDeleteView(LoginRequiredMixin, DeleteView):
    model = Prestacion
    template_name = "prestacion_confirm_delete.html"
    success_url = reverse_lazy("prestaciones")

class PrestacionDetailView(LoginRequiredMixin, DetailView):
    model = Prestacion
    template_name = "prestacion_detail.html"
    context_object_name = "prestacion"