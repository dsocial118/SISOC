from typing import Any
from django.db.models.query import QuerySet
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.views.generic import ListView, CreateView, DetailView, UpdateView

from comedores.forms.comedor import ComedorForm, ReferenteForm
from comedores.forms.relevamiento import (
    RelevamientoForm,
    FuncionamientoPrestacionForm,
    EspacioForm,
    EspacioCocinaForm,
    EspacioPrestacionForm,
    ColaboradoresForm,
    FuenteRecursosForm,
    FuenteComprasForm,
    PrestacionFormSet,
)
from .models import Comedor, Relevamiento


class ComedorListView(ListView):
    model = Comedor
    template_name = "comedor/comedor_list.html"
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
    template_name = "comedor/comedor_form.html"

    def get_success_url(self):
        return reverse("comedor_detalle", kwargs={"pk": self.object.pk})

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
    template_name = "comedor/comedor_detail.html"
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
    template_name = "comedor/comedor_form.html"

    def get_success_url(self):
        return reverse("comedor_detalle", kwargs={"pk": self.object.pk})

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


class ComedorDeleteView(DeleteView):
    model = Comedor
    template_name = "comedor/comedor_confirm_delete.html"
    context_object_name = "comedor"
    success_url = reverse_lazy("comedores")


class RelevamientoCreateView(CreateView):
    model = Relevamiento
    form_class = RelevamientoForm
    template_name = "relevamiento/relevamiento_form.html"

    def get_success_url(self):
        return reverse(
            "relevamiento_detalle",
            kwargs={"pk": self.object.pk},
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["pk"] = self.kwargs["pk"]
        return kwargs

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        forms = {
            "funcionamiento_form": FuncionamientoPrestacionForm,
            "espacio_form": EspacioForm,
            "espacio_cocina_form": EspacioCocinaForm,
            "espacio_prestacion_form": EspacioPrestacionForm,
            "colaboradores_form": ColaboradoresForm,
            "recursos_form": FuenteRecursosForm,
            "compras_form": FuenteComprasForm,
        }

        for form_name, form_class in forms.items():
            if self.request.POST:
                data[form_name] = form_class(self.request.POST)
            else:
                data[form_name] = form_class()

        return data

    def form_valid(self, form):
        context = self.get_context_data()
        forms = {
            "funcionamiento_form": context["funcionamiento_form"],
            "espacio_form": context["espacio_form"],
            "espacio_cocina_form": context["espacio_cocina_form"],
            "espacio_prestacion_form": context["espacio_prestacion_form"],
            "colaboradores_form": context["colaboradores_form"],
            "recursos_form": context["recursos_form"],
            "compras_form": context["compras_form"],
        }

        if all(form.is_valid() for form in forms.values()):
            self.object = form.save(commit=False)

            funcionamiento = forms["funcionamiento_form"].save()
            self.object.funcionamiento = funcionamiento

            espacio = forms["espacio_form"].save(commit=False)
            cocina = forms["espacio_cocina_form"].save(commit=True)
            espacio.cocina = cocina
            prestacion = forms["espacio_prestacion_form"].save(commit=True)
            espacio.prestacion = prestacion
            espacio.save()
            self.object.espacio = espacio

            colaboradores = forms["colaboradores_form"].save()
            self.object.colaboradores = colaboradores

            recursos = forms["recursos_form"].save()
            self.object.recursos = recursos

            compras = forms["compras_form"].save()
            self.object.compras = compras

            self.object.save()

            return super().form_valid(form)
        else:
            self.error_message(forms)
            return self.form_invalid(form)

    def error_message(self, forms):
        for form_name, form_instance in forms.items():
            if not form_instance.is_valid():
                messages.error(
                    self.request, f"Errores en {form_name}: {form_instance.errors}"
                )


class RelevamientoDetailView(DetailView):
    model = Relevamiento
    template_name = "relevamiento/relevamiento_detail.html"
    context_object_name = "relevamiento"

class RelevamientoDeleteView(DeleteView):
    model = Relevamiento
    template_name = "relevamiento/relevamiento_confirm_delete.html"
    context_object_name = "relevamiento"

    def get_success_url(self):
        comedor = self.object.comedor

        return reverse_lazy("comedor_detalle", kwargs={"pk": comedor.id})
