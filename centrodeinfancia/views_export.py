import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpResponse
from django.utils.text import slugify
from django.views.generic import View

from centrodeinfancia.access import (
    aplicar_scope_centros_cdi,
    get_provincia_completa_unica_egp_id,
)
from centrodeinfancia.models import CentroDeInfancia
from centrodeinfancia.services_nomina_ninos_pdf import (
    NominaNinosPDFError,
    generar_nomina_ninos_pdf,
)
from core.mixins import CSVExportMixin
from core.models import Provincia
from core.services.column_preferences import build_columns_context_from_fields


logger = logging.getLogger(__name__)


class CentroDeInfanciaExportView(LoginRequiredMixin, CSVExportMixin, View):
    export_filename = "listado_centrodeinfancia.csv"

    def get_export_columns(self):
        headers = [
            {"title": "Nombre"},
            {"title": "Organización"},
            {"title": "Provincia"},
            {"title": "Departamento"},
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
            {"name": "departamento"},
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
            "organizacion": ("Organización", "organizacion"),
            "provincia": ("Provincia", "provincia.nombre"),
            "departamento": ("Departamento", "departamento.nombre"),
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
            "provincia",
            "departamento",
            "municipio",
            "localidad",
        )
        queryset = aplicar_scope_centros_cdi(queryset, self.request.user)
        if query:
            queryset = queryset.filter(
                Q(nombre__icontains=query) | Q(organizacion__icontains=query)
            )
        return queryset.order_by("nombre")

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        return self.export_csv(queryset)


class NominaNinosPDFView(LoginRequiredMixin, View):
    """Descarga provincial habilitada exclusivamente para SIMEPI - EGP."""

    def get(self, request, *args, **kwargs):
        provincia_id = get_provincia_completa_unica_egp_id(request.user)
        if not provincia_id:
            raise PermissionDenied(
                "La descarga requiere un único alcance provincial completo."
            )

        provincia = Provincia.objects.filter(pk=provincia_id).first()
        if provincia is None:
            raise PermissionDenied("El alcance provincial no es válido.")

        try:
            pdf_bytes = generar_nomina_ninos_pdf(
                user=request.user,
                provincia=provincia,
            )
        except NominaNinosPDFError:
            logger.exception(
                "No se pudo generar la nómina provincial de niños",
                extra={
                    "data": {
                        "usuario_id": request.user.pk,
                        "provincia_id": provincia_id,
                    }
                },
            )
            return HttpResponse(
                "No se pudo generar el archivo. Intente nuevamente más tarde.",
                status=503,
                content_type="text/plain; charset=utf-8",
            )

        filename = f"nomina-ninos-{slugify(provincia.nombre) or provincia.pk}.pdf"
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response["Cache-Control"] = "private, no-store"
        response["Pragma"] = "no-cache"
        return response
