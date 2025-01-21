from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages


from cdi.forms.cdi_form import CentroDesarrolloInfantilForm
from cdi.services.cdi_service import CentroDesarrolloInfantilService
from comedores.forms.comedor_form import ReferenteForm
from .models import CentroDesarrolloInfantil


class CentroDesarrolloInfantilListView(ListView):
    model = CentroDesarrolloInfantil
    template_name = "centrodesarrolloinfantil/centrodesarrolloinfantil_list.html"
    context_object_name = "centros"
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get("busqueda")
        return CentroDesarrolloInfantilService.get_centros_filtrados(query)


class CentroDesarrolloInfantilCreateView(CreateView):
    model = CentroDesarrolloInfantil
    form_class = CentroDesarrolloInfantilForm
    template_name = "centrodesarrolloinfantil/centrodesarrolloinfantil_form.html"

    def get_success_url(self):
        return reverse("centrodesarrolloinfantil_detalle", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["referente_form"] = ReferenteForm(self.request.POST or None, prefix="referente")
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        referente_form = context["referente_form"]

        if referente_form.is_valid():
            self.object = form.save(commit=False)
            self.object.referente = referente_form.save()
            self.object.save()
            return super().form_valid(form)
        else:
            return self.form_invalid(form)


class CentroDesarrolloInfantilDetailView(DetailView):
    model = CentroDesarrolloInfantil
    template_name = "centrodesarrolloinfantil/centrodesarrolloinfantil_detail.html"
    context_object_name = "centro"

    def get_object(self, queryset=None):
        return CentroDesarrolloInfantilService.get_centro_detail_object(self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "referente": self.object.referente,
            "informacion_adicional": CentroDesarrolloInfantilService.get_informacion_adicional(self.object.id),
        })
        return context


class CentroDesarrolloInfantilUpdateView(UpdateView):
    model = CentroDesarrolloInfantil
    form_class = CentroDesarrolloInfantilForm
    template_name = "centrodesarrolloinfantil/centrodesarrolloinfantil_form.html"

    def get_success_url(self):
        return reverse("centrodesarrolloinfantil_detalle", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        self.object = self.get_object()
        data["referente_form"] = ReferenteForm(
            self.request.POST if self.request.POST else None,
            instance=self.object.referente,
            prefix="referente",
        )
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        referente_form = context["referente_form"]

        if referente_form.is_valid():
            self.object = form.save()
            self.object.referente = referente_form.save()
            self.object.save()
            return super().form_valid(form)
        else:
            return self.form_invalid(form)


class CentroDesarrolloInfantilDeleteView(DeleteView):
    model = CentroDesarrolloInfantil
    template_name = "centrodesarrolloinfantil/centrodesarrolloinfantil_confirm_delete.html"
    context_object_name = "centro"
    success_url = reverse_lazy("centrosdesarrolloinfantil")

