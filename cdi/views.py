from django.db.models import Q
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    ListView,
    CreateView,
    DetailView,
    UpdateView,
    DeleteView,
)


from cdi.forms import CentroDesarrolloInfantilForm
from cdi.models import CentroDesarrolloInfantil


class CDIListView(ListView):
    model = CentroDesarrolloInfantil
    template_name = "centrodesarrolloinfantil_list.html"
    context_object_name = "centrodesarrolloinfantiles"
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get("busqueda")
        queryset = CentroDesarrolloInfantil.objects.all()

        if query:
            queryset = queryset.filter(
                Q(nombre__icontains=query)
                | Q(organizacion__nombre__icontains=query)
                | Q(numexpe__icontains=query)
                | Q(numrepo__icontains=query)
                | Q(provincia__nombre__icontains=query)
                | Q(telefono__icontains=query)
                | Q(email__icontains=query)
            )

        return queryset


class CDICreateView(CreateView):
    model = CentroDesarrolloInfantil
    form_class = CentroDesarrolloInfantilForm
    template_name = "centrodesarrolloinfantil_form.html"

    def get_success_url(self):
        return reverse("cdi")


class CDIDetailView(DetailView):
    model = CentroDesarrolloInfantil
    template_name = "centrodesarrolloinfantil_detail.html"
    context_object_name = "centrodesarrolloinfantiles"


class CDIUpdateView(UpdateView):
    model = CentroDesarrolloInfantil
    form_class = CentroDesarrolloInfantilForm
    template_name = "centrodesarrolloinfantil_form.html"

    def get_success_url(self):
        return reverse("cdi_detalle", kwargs={"pk": self.object.pk})


class CDIDeleteView(DeleteView):
    model = CentroDesarrolloInfantil
    template_name = "centrodesarrolloinfantil_confirm_delete.html"
    context_object_name = "centrodesarrolloinfantiles"
    success_url = reverse_lazy("cdi")
