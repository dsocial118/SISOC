import re
import unicodedata

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import View

from centrodefamilia.access import ROLE_CDF_SSE_PERMISSION
from centrodefamilia.services.beneficiarios_service import (
    formatear_fecha_nacimiento,
    get_filtered_beneficiarios,
)
from core.mixins import CSVExportMixin
from core.services.advanced_filters.payload import extract_raw_filters, load_payload
from iam.services import user_has_any_permission_codes

FILTERS_PARAM_NAME = "filters"
FILENAME_FIELDS_PRIORITY = ("provincia", "municipio", "localidad")
CSV_FORMULA_PREFIXES = ("=", "+", "-", "@")
SORT_FIELDS = {
    "cuil": ("cuil",),
    "apellido_nombre": ("apellido", "nombre"),
    "dni": ("dni",),
    "fecha_nacimiento_display": ("fecha_nacimiento",),
    "genero_display": ("genero",),
    "responsable_nombre": ("responsable__apellido", "responsable__nombre"),
    "responsable_cuil": ("responsable__cuil",),
    "provincia": ("provincia__nombre",),
    "municipio": ("municipio__nombre",),
}


def _slugify_for_filename(value):
    normalized = unicodedata.normalize("NFKD", str(value))
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]", "", ascii_only.lower())


def _neutralize_csv_formula(value):
    value = str(value or "")
    return f"'{value}" if value.startswith(CSV_FORMULA_PREFIXES) else value


class BeneficiariosExportView(LoginRequiredMixin, CSVExportMixin, View):
    export_filename = "listado_beneficiarios.csv"
    # El rol CDF SSE exporta el padrón de preinscriptos sin necesitar el rol
    # transversal de exportación a CSV.
    export_permission_codes = (
        CSVExportMixin.export_permission_code,
        ROLE_CDF_SSE_PERMISSION,
    )

    def check_export_permission(self, request):
        if not request.user.is_authenticated:
            raise PermissionDenied

        if not user_has_any_permission_codes(
            request.user, self.export_permission_codes
        ):
            raise PermissionDenied

        return True

    def get_export_columns(self):
        return [
            ("CUIL", "cuil"),
            ("Apellido y Nombre", "custom_apellido_nombre"),
            ("DNI", "dni"),
            ("Fecha de nacimiento", "custom_fecha_nacimiento"),
            ("Género", "custom_genero"),
            ("Responsable", "custom_responsable"),
            ("CUIL del responsable", "responsable.cuil"),
            ("Provincia", "provincia.nombre"),
            ("Municipio", "municipio.nombre"),
        ]

    def resolve_field(self, obj, field_path):
        if field_path == "custom_apellido_nombre":
            value = f"{obj.apellido}, {obj.nombre}"
        elif field_path == "custom_fecha_nacimiento":
            value = formatear_fecha_nacimiento(obj.fecha_nacimiento, vacio="")
        elif field_path == "custom_genero":
            value = obj.get_genero_display()
        elif field_path == "custom_responsable":
            value = f"{obj.responsable.apellido}, {obj.responsable.nombre}"
        else:
            value = super().resolve_field(obj, field_path)
        return _neutralize_csv_formula(value)

    def get_ordering(self):
        fields = SORT_FIELDS.get(self.request.GET.get("sort"))
        direction = self.request.GET.get("direction")
        if not fields or direction not in {"asc", "desc"}:
            return ()

        prefix = "-" if direction == "desc" else ""
        return tuple(f"{prefix}{field}" for field in fields) + (
            "-id",
            "apellido",
            "nombre",
        )

    def get_export_filename(self):
        payload = (
            load_payload(extract_raw_filters(FILTERS_PARAM_NAME, self.request)) or {}
        )
        items = payload.get("items") or []
        if isinstance(items, list):
            for campo in FILENAME_FIELDS_PRIORITY:
                for item in items:
                    if not isinstance(item, dict) or item.get("field") != campo:
                        continue
                    valor = item.get("value")
                    if valor is None or str(valor).strip() == "":
                        continue
                    slug = _slugify_for_filename(valor)
                    if slug:
                        return f"beneficiarios_{campo}_{slug}.csv"
        return "beneficiarios_todos.csv"

    def get(self, request, *args, **kwargs):
        self.check_export_permission(request)

        queryset = get_filtered_beneficiarios(request)
        ordering = self.get_ordering()
        if ordering:
            queryset = queryset.order_by(*ordering)

        if not queryset.exists():
            messages.warning(
                request,
                "No hay beneficiarios para exportar con el filtro aplicado.",
            )
            return HttpResponseRedirect(
                request.META.get("HTTP_REFERER") or reverse("beneficiarios_list")
            )

        return self.export_csv(queryset)
