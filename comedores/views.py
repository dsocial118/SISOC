from typing import Any
from django.db.models.query import QuerySet
from django.urls import reverse
from django.views.generic import ListView, CreateView, DetailView, UpdateView

from comedores.forms.comedor import ComedorForm
from .models import Comedor


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
            "referente__apellido",
            "referente__nombre",
            "referente__telefono",
        )


class ComedorCreateView(CreateView):
    model = Comedor
    form_class = ComedorForm
    template_name = "comedor_form.html"

    def get_success_url(self):
        return reverse("comedor_ver", kwargs={"pk": self.object.pk})


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
            "referente__apellido",
            "referente__nombre",
            "referente__telefono",
            "referente__email",
        )


class ComedorUpdateView(UpdateView):
    model = Comedor
    form_class = ComedorForm
    template_name = "comedor_form.html"

    def get_success_url(self):
        return reverse("comedor_ver", kwargs={"pk": self.object.pk})
