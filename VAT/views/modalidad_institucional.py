from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (
    ListView,
    CreateView,
    DetailView,
    UpdateView,
    DeleteView,
)
from django.urls import reverse, reverse_lazy
from django.contrib import messages

from VAT.models import ModalidadInstitucional
from VAT.forms import ModalidadInstitucionalForm


class ModalidadInstitucionalListView(LoginRequiredMixin, ListView):
    model = ModalidadInstitucional
    template_name = "vat/modalidad_institucional/list.html"
    context_object_name = "modalidades"
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset().order_by("nombre")
        activo = self.request.GET.get("activo")
        if activo == "true":
            queryset = queryset.filter(activo=True)
        elif activo == "false":
            queryset = queryset.filter(activo=False)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["table_headers"] = [
            {"title": "Nombre", "sortable": True, "sort_key": "nombre"},
            {"title": "Descripción", "sortable": False},
            {"title": "Estado", "sortable": True, "sort_key": "activo"},
            {"title": "Creado", "sortable": True, "sort_key": "fecha_creacion"},
        ]
        context["activo_filter"] = self.request.GET.get("activo")
        return context


class ModalidadInstitucionalCreateView(LoginRequiredMixin, CreateView):
    model = ModalidadInstitucional
    form_class = ModalidadInstitucionalForm
    template_name = "vat/modalidad_institucional/form.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Modalidad institucional creada correctamente.")
        return response

    def get_success_url(self):
        return reverse(
            "vat_modalidad_institucional_detail", kwargs={"pk": self.object.pk}
        )


class ModalidadInstitucionalDetailView(LoginRequiredMixin, DetailView):
    model = ModalidadInstitucional
    template_name = "vat/modalidad_institucional/detail.html"
    context_object_name = "modalidad"


class ModalidadInstitucionalUpdateView(LoginRequiredMixin, UpdateView):
    model = ModalidadInstitucional
    form_class = ModalidadInstitucionalForm
    template_name = "vat/modalidad_institucional/form.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request, "Modalidad institucional actualizada correctamente."
        )
        return response

    def get_success_url(self):
        return reverse(
            "vat_modalidad_institucional_detail", kwargs={"pk": self.object.pk}
        )


class ModalidadInstitucionalDeleteView(LoginRequiredMixin, DeleteView):
    model = ModalidadInstitucional
    template_name = "vat/modalidad_institucional/confirm_delete.html"
    context_object_name = "modalidad"
    success_url = reverse_lazy("vat_modalidad_institucional_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Modalidad institucional eliminada correctamente.")
        return super().delete(request, *args, **kwargs)
