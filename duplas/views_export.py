from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from core.mixins import CSVExportMixin
from duplas.models import Dupla
from duplas.views import DUPLA_ADVANCED_FILTER


class DuplaExportView(LoginRequiredMixin, CSVExportMixin, View):
    export_filename = "listado_duplas.csv"

    def get_export_columns(self):
        return [
            ("Nombre", "nombre"),
            ("Coordinador", "coordinador_nombre"),
            ("Técnicos", "tecnicos_nombres"),
            ("Abogado", "abogado_nombre"),
            ("Estado", "estado"),
        ]

    def get_queryset(self):
        base_qs = Dupla.objects.select_related(
            "abogado", "coordinador"
        ).prefetch_related("tecnico")

        filtered_qs = DUPLA_ADVANCED_FILTER.filter_queryset(base_qs, self.request)

        # Sorting
        sort_col = self.request.GET.get("sort")
        direction = self.request.GET.get("direction", "asc")

        if sort_col:
            prefix = "-" if direction == "desc" else ""
            map_sort = {
                "nombre": "nombre",
                "coordinador_nombre": "coordinador__last_name",  # Sort by lastname roughly matches name sort
                "abogado_nombre": "abogado__last_name",
                "estado": "estado",
                # tecnicos_nombres is M2M, usually handled by distinct or not sortable easily on backend without annotation
            }
            if sort_col in map_sort:
                filtered_qs = filtered_qs.order_by(f"{prefix}{map_sort[sort_col]}")
        else:
            filtered_qs = filtered_qs.order_by("-fecha", "nombre")

        return filtered_qs.distinct()

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        return self.export_csv(queryset)
