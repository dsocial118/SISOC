import itertools
import re
import unicodedata

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import View

from centrodefamilia.services.beneficiarios_service import get_filtered_beneficiarios
from core.mixins import CSVExportMixin
from core.services.advanced_filters.payload import extract_raw_filters, load_payload

FILTERS_PARAM_NAME = "filters"
FILENAME_FIELDS_PRIORITY = ("provincia", "municipio", "localidad")


def _slugify_for_filename(value):
    normalized = unicodedata.normalize("NFKD", str(value))
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]", "", ascii_only.lower())


class BeneficiariosExportView(LoginRequiredMixin, CSVExportMixin, View):
    export_filename = "listado_beneficiarios.csv"

    def get_export_columns(self):
        return [
            ("CUIL", "cuil"),
            ("Apellido y Nombre", "custom_apellido_nombre"),
            ("DNI", "dni"),
            ("Género", "custom_genero"),
            ("Responsable", "custom_responsable"),
            ("Provincia", "provincia.nombre"),
            ("Municipio", "municipio.nombre"),
        ]

    def resolve_field(self, obj, field_path):
        if field_path == "custom_apellido_nombre":
            return f"{obj.apellido}, {obj.nombre}"
        if field_path == "custom_genero":
            return obj.get_genero_display()
        if field_path == "custom_responsable":
            return f"{obj.responsable.apellido}, {obj.responsable.nombre}"
        return super().resolve_field(obj, field_path)

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

        if not queryset.exists():
            messages.warning(
                request,
                "No hay beneficiarios para exportar con el filtro aplicado.",
            )
            return HttpResponseRedirect(
                request.META.get("HTTP_REFERER") or reverse("beneficiarios_list")
            )

        response = self.export_csv(queryset)
        # BOM UTF-8 para que Excel muestre correctamente tildes y ñ.
        response.streaming_content = itertools.chain(["﻿"], response.streaming_content)
        return response
