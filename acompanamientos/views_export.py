from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from core.mixins import CSVExportMixin
from core.services.column_preferences import build_columns_context_for_custom_cells
from acompanamientos.acompanamiento_service import AcompanamientoService


class AcompanamientoExportView(LoginRequiredMixin, CSVExportMixin, View):
    export_filename = "listado_acompanamientos.csv"

    def get_export_columns(self):
        headers = [
            {"key": "id", "title": "ID"},
            {"key": "nombre", "title": "Nombre"},
            {"key": "organizacion", "title": "Organización"},
            {"key": "expediente", "title": "N° Expediente"},
            {"key": "provincia", "title": "Provincia"},
            {"key": "dupla", "title": "Dupla"},
            {"key": "estado", "title": "Estado"},
            {"key": "modificado", "title": "Última Modificación"},
        ]
        columns_map = {
            "id": ("ID", "id"),
            "nombre": ("Nombre", "nombre"),
            "organizacion": ("Organización", "organizacion__nombre"),
            "expediente": ("N° Expediente", "custom_num_expediente"),
            "provincia": ("Provincia", "provincia__nombre"),
            "dupla": ("Dupla", "dupla__nombre"),
            "estado": ("Estado", "custom_estado"),
            "modificado": ("Última Modificación", "custom_modificado"),
        }
        columns_context = build_columns_context_for_custom_cells(
            self.request,
            "acompanamientos_comedores_list",
            headers,
            [],
        )
        active_keys = columns_context.get("column_active_keys", [])
        if not active_keys:
            return list(columns_map.values())
        return [columns_map[key] for key in active_keys if key in columns_map]

    def get_queryset(self):
        user = self.request.user
        busqueda = self.request.GET.get("busqueda", "").strip().lower()
        # Returns Comedor queryset with prefetched admisions
        return AcompanamientoService.obtener_comedores_acompanamiento(user, busqueda)

    def resolve_field(self, obj, field_path):
        # Handle custom fields dependent on the related Admission
        if field_path.startswith("custom_"):
            admision = (
                obj.admisiones_acompaniamiento[0]
                if getattr(obj, "admisiones_acompaniamiento", None)
                else None
            )

            if field_path == "custom_num_expediente":
                return admision.num_expediente if admision else "-"

            if field_path == "custom_estado":
                return admision.get_estado_admision_display() if admision else "-"

            if field_path == "custom_modificado":
                if admision and admision.modificado:
                    # Format dates as YYYY-MM-DD HH:MM:SS
                    if hasattr(admision.modificado, 'hour'):  # datetime
                        return admision.modificado.strftime("%Y-%m-%d %H:%M:%S")
                    else:  # date
                        return admision.modificado.strftime("%Y-%m-%d 00:00:00")
                return "-"

        return super().resolve_field(obj, field_path)

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        return self.export_csv(queryset)
