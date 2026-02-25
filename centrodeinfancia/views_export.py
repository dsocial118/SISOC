from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.views.generic import View

from centrodeinfancia.models import CentroDeInfancia
from core.mixins import CSVExportMixin
from core.services.column_preferences import build_columns_context_from_fields


def _get_provincia_usuario(user):
    if not user or not user.is_authenticated:
        return None

    try:
        return user.profile.provincia
    except Exception:
        return None


def _aplicar_filtro_provincia_usuario(queryset, user):
    provincia_usuario = _get_provincia_usuario(user)
    if provincia_usuario:
        return queryset.filter(provincia=provincia_usuario)
    return queryset


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
            {"title": "Teléfono"},
            {"title": "Referente"},
        ]
        fields = [
            {"name": "nombre"},
            {"name": "organizacion"},
            {"name": "provincia"},
            {"name": "municipio"},
            {"name": "localidad"},
            {"name": "calle"},
            {"name": "telefono"},
            {"name": "referente"},
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
            "telefono": ("Teléfono", "telefono"),
            "referente": ("Referente", "nombre_referente"),
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
        queryset = _aplicar_filtro_provincia_usuario(queryset, self.request.user)
        if query:
            queryset = queryset.filter(
                Q(nombre__icontains=query) | Q(organizacion__nombre__icontains=query)
            )
        return queryset.order_by("nombre")

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        return self.export_csv(queryset)
