from typing import Any
from django.db.models.query import QuerySet
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, CreateView, DetailView, UpdateView

from comedores.forms.comedor import ComedorForm, ReferenteForm
from comedores.forms.relevamiento import (
    RelevamientoForm,
    FuncionamientoPrestacionForm,
    EspacioForm,
    ColaboradoresForm,
    FuenteRecursosForm,
    FuenteComprasForm,
    PrestacionFormSet,
)
from .models import Comedor, Relevamiento


class ComedorListView(ListView):
    model = Comedor
    template_name = "comedor_list.html"
    context_object_name = "comedores"
    paginate_by = 10

    def get_queryset(self):
        return Comedor.objects.select_related("provincia", "referente").values(
            "id",
            "nombre",
            "provincia__nombre",
            "calle",
            "numero",
            "referente__nombre_completo",
            "referente__numero",
        )


class ComedorCreateView(CreateView):
    model = Comedor
    form_class = ComedorForm
    template_name = "comedor_form.html"

    def get_success_url(self):
        return reverse("comedor_ver", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data["referente_form"] = ReferenteForm(self.request.POST)
        else:
            data["referente_form"] = ReferenteForm()
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        referente_form = context["referente_form"]

        if referente_form.is_valid():
            self.object = form.save()
            referente = referente_form.save()

            self.object.referente = referente
            self.object.save()

            return super().form_valid(form)
        else:
            return self.form_invalid(form)


class ComedorDetailView(DetailView):
    model = Comedor
    template_name = "comedor_detail.html"
    context_object_name = "comedor"

    def get_queryset(self) -> QuerySet[Any]:
        return Comedor.objects.select_related("provincia", "referente").values(
            "id",
            "nombre",
            "comienzo",
            "provincia__nombre",
            "municipio__nombre_region",
            "localidad__nombre",
            "partido",
            "barrio",
            "calle",
            "numero",
            "entre_calle_1",
            "entre_calle_2",
            "codigo_postal",
            "referente__nombre_completo",
            "referente__mail",
            "referente__numero",
            "referente__documento",
        )


class ComedorUpdateView(UpdateView):
    model = Comedor
    form_class = ComedorForm
    template_name = "comedor_form.html"

    def get_success_url(self):
        return reverse("comedor_ver", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        self.object = self.get_object()
        if self.request.POST:
            data["referente_form"] = ReferenteForm(
                self.request.POST, instance=self.object.referente
            )
        else:
            data["referente_form"] = ReferenteForm(instance=self.object.referente)
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        referente_form = context["referente_form"]

        if referente_form.is_valid():
            self.object = form.save()
            referente = referente_form.save()

            self.object.referente = referente
            self.object.save()

            return super().form_valid(form)
        else:
            return self.form_invalid(form)

