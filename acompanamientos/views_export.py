from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from core.mixins import CSVExportMixin
from acompanamientos.acompanamiento_service import AcompanamientoService


class AcompanamientoExportView(LoginRequiredMixin, CSVExportMixin, View):
    export_filename = "listado_acompanamientos.csv"

    def get_export_columns(self):
        return [
            ("ID", "id"),
            ("Nombre", "nombre"),
            ("Organización", "organizacion__nombre"),
            ("N° Expediente", "custom_num_expediente"),
            ("Provincia", "provincia__nombre"),
            ("Dupla", "dupla__nombre"),
            ("Estado", "custom_estado"),
            ("Última Modificación", "custom_modificado"),
        ]

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
                return (
                    admision.modificado.strftime("%d/%m/%Y")
                    if admision and admision.modificado
                    else "-"
                )

        return super().resolve_field(obj, field_path)

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        return self.export_csv(queryset)
