from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.views.generic import View

from centrodeinfancia.models import CentroDeInfancia
from core.mixins import CSVExportMixin


class CentroDeInfanciaExportView(LoginRequiredMixin, CSVExportMixin, View):
    export_filename = "listado_centrodeinfancia.csv"

    def get_export_columns(self):
        return [
            ("Nombre", "nombre"),
            ("Organización", "organizacion.nombre"),
        ]

    def get_queryset(self):
        query = self.request.GET.get("busqueda")
        queryset = CentroDeInfancia.objects.select_related("organizacion")
        if query:
            queryset = queryset.filter(
                Q(nombre__icontains=query) | Q(organizacion__nombre__icontains=query)
            )
        return queryset.order_by("nombre")

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        return self.export_csv(queryset)
