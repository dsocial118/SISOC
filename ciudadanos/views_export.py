from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from core.mixins import CSVExportMixin
from ciudadanos.models import Ciudadano
from ciudadanos.forms import CiudadanoFiltroForm
from ciudadanos.views import apply_ciudadanos_filters


class CiudadanosExportView(LoginRequiredMixin, CSVExportMixin, View):
    export_filename = "listado_ciudadanos.csv"

    def get_export_columns(self):
        return [
            ("Apellido", "apellido"),
            ("Nombre", "nombre"),
            ("Documento", "documento"),
            ("Sexo", "sexo"),
            ("Provincia", "provincia__nombre"),
            ("Municipio", "municipio__nombre"),
            ("Localidad", "localidad__nombre"),
        ]

    def get_queryset(self):
        queryset = Ciudadano.objects.select_related(
            "sexo", "provincia", "municipio", "localidad"
        )
        form = CiudadanoFiltroForm(self.request.GET or None)
        if form.is_valid():
            queryset = apply_ciudadanos_filters(queryset, form.cleaned_data)

        # Sorting
        sort_col = self.request.GET.get("sort")
        direction = self.request.GET.get("direction", "asc")
        if sort_col:
            prefix = "-" if direction == "desc" else ""
            # Map frontend columns to backend fields
            map_sort = {
                "apellido": "apellido",
                "nombre": "nombre",
                "documento": "documento",
                "sexo": "sexo",
                "provincia": "provincia__nombre",
            }
            if sort_col in map_sort:
                queryset = queryset.order_by(f"{prefix}{map_sort[sort_col]}")
        else:
            queryset = queryset.order_by("apellido", "nombre")

        return queryset

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        return self.export_csv(queryset)
