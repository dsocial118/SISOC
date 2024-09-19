from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView

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

