from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from core.mixins import CSVExportMixin
from core.services.column_preferences import build_columns_context_for_custom_cells
from acompanamientos.acompanamiento_service import AcompanamientoService
from acompanamientos.models.acompanamiento import Acompanamiento
from acompanamientos.views import ACOMPANAMIENTOS_LIST_HEADERS_KEY


class AcompanamientoExportView(LoginRequiredMixin, CSVExportMixin, View):
    export_filename = "listado_acompanamientos.csv"

    def get_export_columns(self):
        headers = [
            {"key": "id", "title": "ID"},
            {"key": "nombre", "title": "Nombre"},
            {"key": "convenio", "title": "Convenio"},
            {"key": "organizacion", "title": "Organización"},
            {"key": "expediente", "title": "N° Expediente"},
            {"key": "provincia", "title": "Provincia"},
            {"key": "dupla", "title": "Dupla"},
            {"key": "estado", "title": "Estado"},
            {"key": "estado_acompanamiento", "title": "Estado del acompañamiento"},
            {"key": "modificado", "title": "Última Modificación"},
        ]
        # resolve_field navega con puntos, no con "__": usar lookups del ORM
        # deja la celda vacía en silencio.
        columns_map = {
            "id": ("ID", "comedor.id"),
            "nombre": ("Nombre", "comedor.nombre"),
            "convenio": ("Convenio", "custom_convenio"),
            "organizacion": ("Organización", "comedor.organizacion.nombre"),
            "expediente": ("N° Expediente", "num_expediente"),
            "provincia": ("Provincia", "comedor.provincia.nombre"),
            "dupla": ("Dupla", "comedor.dupla.nombre"),
            "estado": ("Estado", "custom_estado"),
            "estado_acompanamiento": (
                "Estado del acompañamiento",
                "custom_estado_acompanamiento",
            ),
            "modificado": ("Última Modificación", "custom_modificado"),
        }
        columns_context = build_columns_context_for_custom_cells(
            self.request,
            ACOMPANAMIENTOS_LIST_HEADERS_KEY,
            headers,
            [],
        )
        active_keys = columns_context.get("column_active_keys", [])
        if not active_keys:
            return list(columns_map.values())
        return [columns_map[key] for key in active_keys if key in columns_map]

    def get_queryset(self):
        return AcompanamientoService.obtener_acompanamientos(
            self.request.user, self.request
        )

    def resolve_field(self, obj, field_path):
        """Resuelve las columnas que no salen directo de un campo de Admision."""
        if field_path.startswith("custom_"):
            if field_path == "custom_convenio":
                acompanamiento = getattr(obj, "acompanamiento", None)
                if acompanamiento and acompanamiento.nro_convenio:
                    return acompanamiento.nro_convenio
                return f"Admisión #{obj.id}"

            if field_path == "custom_estado":
                return obj.get_estado_admision_display() if obj.estado_admision else "-"

            if field_path == "custom_estado_acompanamiento":
                estado = getattr(
                    obj, "estado_acompanamiento", Acompanamiento.ESTADO_ACTIVO
                )
                return dict(Acompanamiento.ESTADOS).get(estado, "-")

            if field_path == "custom_modificado":
                if obj.modificado:
                    # Format dates as YYYY-MM-DD HH:mm:ss
                    if hasattr(obj.modificado, "hour"):  # datetime
                        return obj.modificado.strftime("%Y-%m-%d %H:%M:%S")
                    return obj.modificado.strftime("%Y-%m-%d 00:00:00")
                return "-"

        return super().resolve_field(obj, field_path)

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        return self.export_csv(queryset)
