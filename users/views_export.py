from django.views.generic import View
from django.contrib.auth.models import Group
from core.mixins import CSVExportMixin
from core.services.column_preferences import (
    build_export_columns,
    build_export_sort_map,
    resolve_column_state,
)
from users.grupos_column_config import GRUPOS_COLUMNS, GRUPOS_LIST_KEY
from users.services import UsuariosService
from users.usuarios_column_config import USUARIOS_COLUMNS, USUARIOS_LIST_KEY
from users.views import AdminRequiredMixin


class UserExportView(AdminRequiredMixin, CSVExportMixin, View):
    export_filename = "listado_usuarios.csv"

    def get_export_columns(self):
        column_state = resolve_column_state(
            self.request,
            USUARIOS_LIST_KEY,
            USUARIOS_COLUMNS,
        )
        return build_export_columns(USUARIOS_COLUMNS, column_state.active_keys)

    def get_queryset(self):
        # Sorting handled by service? Or manually? Service applies standard order.
        # Let's use service for base filtering
        queryset = UsuariosService.get_filtered_usuarios(self.request)

        # Apply sorting from request if present
        sort_col = self.request.GET.get("sort")
        direction = self.request.GET.get("direction", "asc")

        if sort_col:
            prefix = "-" if direction == "desc" else ""
            map_sort = build_export_sort_map(USUARIOS_COLUMNS)
            if sort_col in map_sort:
                queryset = queryset.order_by(f"{prefix}{map_sort[sort_col]}")

        return queryset

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        return self.export_csv(queryset)


class GroupExportView(AdminRequiredMixin, CSVExportMixin, View):
    export_filename = "listado_grupos.csv"

    def get_export_columns(self):
        column_state = resolve_column_state(
            self.request,
            GRUPOS_LIST_KEY,
            GRUPOS_COLUMNS,
        )
        return build_export_columns(GRUPOS_COLUMNS, column_state.active_keys)

    def get_queryset(self):
        queryset = Group.objects.all()

        sort_col = self.request.GET.get("sort")
        direction = self.request.GET.get("direction", "asc")
        if sort_col:
            prefix = "-" if direction == "desc" else ""
            map_sort = build_export_sort_map(GRUPOS_COLUMNS)
            if sort_col in map_sort:
                queryset = queryset.order_by(f"{prefix}{map_sort[sort_col]}")

        return queryset

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        return self.export_csv(queryset)
