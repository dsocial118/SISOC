from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.views.generic import View

from centrodeinfancia.access import aplicar_filtro_provincia_usuario
from centrodeinfancia.models import CentroDeInfancia
from core.mixins import CSVExportMixin
from core.services.column_preferences import build_columns_context_from_fields


class CentroDeInfanciaExportView(LoginRequiredMixin, CSVExportMixin, View):
    export_filename = "listado_centrodeinfancia.csv"

    def get_export_columns(self):
        headers = [
            {"title": "Nombre"},
            {"title": "Organización"},
            {"title": "Provincia"},
            {"title": "Municipio"},
            {"title": "Localidad"},
            {"title": "Calle"},
            {"title": "Número"},
            {"title": "Teléfono"},
            {"title": "Nombre del referente"},
            {"title": "Apellido del referente"},
        ]
        fields = [
            {"name": "nombre"},
            {"name": "organizacion"},
            {"name": "provincia"},
            {"name": "municipio"},
            {"name": "localidad"},
            {"name": "calle"},
            {"name": "numero"},
            {"name": "telefono"},
            {"name": "nombre_referente"},
            {"name": "apellido_referente"},
        ]
        columns_context = build_columns_context_from_fields(
            self.request,
            "centrodeinfancia_list",
            headers,
            fields,
            required_keys=["nombre"],
        )
        columns_map = {
            "nombre": ("Nombre", "nombre"),
            "organizacion": ("Organización", "organizacion.nombre"),
            "provincia": ("Provincia", "provincia.nombre"),
            "municipio": ("Municipio", "municipio.nombre"),
            "localidad": ("Localidad", "localidad.nombre"),
            "calle": ("Calle", "calle"),
            "numero": ("Número", "numero"),
            "telefono": ("Teléfono", "telefono"),
            "nombre_referente": ("Nombre del referente", "nombre_referente"),
            "apellido_referente": ("Apellido del referente", "apellido_referente"),
        }

        active_keys = columns_context.get("column_active_keys", [])
        if not active_keys:
            return list(columns_map.values())
        return [columns_map[key] for key in active_keys if key in columns_map]

    def get_queryset(self):
        query = self.request.GET.get("busqueda")
        queryset = CentroDeInfancia.objects.select_related(
            "organizacion", "provincia", "municipio", "localidad"
        )
        queryset = aplicar_filtro_provincia_usuario(queryset, self.request.user)
        if query:
            queryset = queryset.filter(
                Q(nombre__icontains=query) | Q(organizacion__nombre__icontains=query)
            )
        return queryset.order_by("nombre")

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        return self.export_csv(queryset)
