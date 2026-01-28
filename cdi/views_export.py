from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from core.mixins import CSVExportMixin
from cdi.models import CentroDesarrolloInfantil


class CDIExportView(LoginRequiredMixin, CSVExportMixin, View):
    export_filename = "listado_cdi.csv"

    def get_export_columns(self):
        return [
            ("Nombre", "nombre"),
            ("Número Expediente", "numexpe"),
            ("Número Repi", "numrepo"),
            ("Organización", "organizacion__nombre"),
            ("Provincia", "provincia__nombre"),
        ]

    def get_queryset(self):
        query = self.request.GET.get("busqueda")
        queryset = CentroDesarrolloInfantil.objects.select_related(
            "organizacion", "provincia"
        )

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

        # Sorting from request
        sort_col = self.request.GET.get("sort")
        direction = self.request.GET.get("direction", "asc")

        if sort_col:
            prefix = "-" if direction == "desc" else ""
            # map headers to fields
            map_sort = {
                "nombre": "nombre",
                "numexpe": "numexpe",
                "numrepo": "numrepo",
                "organizacion": "organizacion__nombre",
                "provincia": "provincia__nombre",
            }
            if sort_col in map_sort:
                queryset = queryset.order_by(f"{prefix}{map_sort[sort_col]}")
        else:
            queryset = queryset.order_by("nombre")

        return queryset

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        return self.export_csv(queryset)
