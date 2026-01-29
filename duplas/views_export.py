from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from core.mixins import CSVExportMixin
from core.services.column_preferences import (
    apply_queryset_column_hints,
    build_export_columns,
    build_export_sort_map,
    resolve_column_state,
)
from duplas.dupla_column_config import DUPLA_COLUMNS, DUPLA_LIST_KEY
from duplas.models import Dupla
from duplas.views import DUPLA_ADVANCED_FILTER


class DuplaExportView(LoginRequiredMixin, CSVExportMixin, View):
    export_filename = "listado_duplas.csv"

    def get_export_columns(self):
        column_state = resolve_column_state(
            self.request,
            DUPLA_LIST_KEY,
            DUPLA_COLUMNS,
        )
        return build_export_columns(DUPLA_COLUMNS, column_state.active_keys)

    def get_queryset(self):
        base_qs = Dupla.objects.all()

        filtered_qs = DUPLA_ADVANCED_FILTER.filter_queryset(base_qs, self.request)
        column_state = resolve_column_state(
            self.request,
            DUPLA_LIST_KEY,
            DUPLA_COLUMNS,
        )
        filtered_qs = apply_queryset_column_hints(
            filtered_qs,
            DUPLA_COLUMNS,
            column_state.active_keys,
        )

        # Sorting
        sort_col = self.request.GET.get("sort")
        direction = self.request.GET.get("direction", "asc")

        if sort_col:
            prefix = "-" if direction == "desc" else ""
            map_sort = build_export_sort_map(DUPLA_COLUMNS)
            if sort_col in map_sort:
                filtered_qs = filtered_qs.order_by(f"{prefix}{map_sort[sort_col]}")
        else:
            filtered_qs = filtered_qs.order_by("-fecha", "nombre")

        return filtered_qs.distinct()

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        return self.export_csv(queryset)
