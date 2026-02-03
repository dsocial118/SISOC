from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count
from core.mixins import CSVExportMixin
from organizaciones.models import Organizacion


class OrganizacionExportView(LoginRequiredMixin, CSVExportMixin, View):
    export_filename = "listado_organizaciones.csv"

    def get_export_columns(self):
        return [
            ("CUIT", "cuit"),
            ("Nombre", "nombre"),
            ("Comedores", "comedores_count"),
            ("Tipo de Entidad", "tipo_entidad__nombre"),
            ("Subtipo de Entidad", "subtipo_entidad__nombre"),
            ("Teléfono", "telefono"),
            ("Email", "email"),
        ]

    def get_queryset(self):
        busqueda = self.request.GET.get("busqueda", "").strip()

        organizaciones = Organizacion.objects.select_related(
            "tipo_entidad", "subtipo_entidad"
        ).annotate(comedores_count=Count("comedor"))

        if busqueda:
            organizaciones = organizaciones.filter(
                Q(nombre__icontains=busqueda)
                | Q(cuit__icontains=busqueda)
                | Q(telefono__icontains=busqueda)
                | Q(email__icontains=busqueda)
            )

        # Sorting from request
        sort_col = self.request.GET.get("sort")
        direction = self.request.GET.get("direction", "asc")

        if sort_col:
            prefix = "-" if direction == "desc" else ""
            map_sort = {
                "cuit": "cuit",
                "nombre": "nombre",
                "comedores": "comedores_count",  # Annotated field, works in order_by
                "tipo_entidad": "tipo_entidad__nombre",
                "subtipo_entidad": "subtipo_entidad__nombre",
                "telefono": "telefono",
                "email": "email",
            }
            if sort_col in map_sort:
                organizaciones = organizaciones.order_by(
                    f"{prefix}{map_sort[sort_col]}"
                )
        else:
            organizaciones = organizaciones.order_by("-id")  # matches default view

        return organizaciones

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        return self.export_csv(queryset)
