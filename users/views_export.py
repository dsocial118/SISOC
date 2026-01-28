from django.views.generic import View
from django.contrib.auth.models import Group
from core.mixins import CSVExportMixin
from users.services import UsuariosService
from users.views import AdminRequiredMixin


class UserExportView(AdminRequiredMixin, CSVExportMixin, View):
    export_filename = "listado_usuarios.csv"

    def get_export_columns(self):
        return [
            ("Nombre", "first_name"),
            ("Apellido", "last_name"),
            ("Username", "username"),
            ("Email", "email"),
            (
                "Rol",
                "rol",
            ),  # Assuming 'rol' is available on the queryset objects/annotations
        ]

    def get_queryset(self):
        # Sorting handled by service? Or manually? Service applies standard order.
        # Let's use service for base filtering
        queryset = UsuariosService.get_filtered_usuarios(self.request)

        # Apply sorting from request if present
        sort_col = self.request.GET.get("sort")
        direction = self.request.GET.get("direction", "asc")

        if sort_col:
            prefix = "-" if direction == "desc" else ""
            map_sort = {
                "first_name": "first_name",
                "last_name": "last_name",
                "username": "username",
                "email": "email",
                "rol": "rol",  # If annotated
            }
            if sort_col in map_sort:
                queryset = queryset.order_by(f"{prefix}{map_sort[sort_col]}")

        return queryset

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        return self.export_csv(queryset)


class GroupExportView(AdminRequiredMixin, CSVExportMixin, View):
    export_filename = "listado_grupos.csv"

    def get_export_columns(self):
        return [
            ("Nombre", "name"),
        ]

    def get_queryset(self):
        queryset = Group.objects.all()

        sort_col = self.request.GET.get("sort")
        direction = self.request.GET.get("direction", "asc")
        if sort_col == "name":
            prefix = "-" if direction == "desc" else ""
            queryset = queryset.order_by(f"{prefix}name")

        return queryset

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        return self.export_csv(queryset)
