from decimal import Decimal
import csv
import io
from datetime import datetime

from django.views.generic import FormView
from django.urls import reverse_lazy
from django.db import transaction
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import CSVUploadForm
from expedientespagos.models import ExpedientePago
from comedores.models import Comedor
from .models import ArchivosImportados


DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]

# mapeo de cabeceras posibles -> campo de modelo
HEADER_MAP = {
    "expediente": "expediente_pago",
    "expediente de pago": "expediente_pago",
    "resolucion": "resolucion_pago",
    "resolución": "resolucion_pago",
    "resolución de pago": "resolucion_pago",
    "anexo": "anexo",
    "if cantidad de prestaciones": "if_cantidad_de_prestaciones",
    "if pagado": "if_pagado",
    "monto": "monto",
    "numero orden pago": "numero_orden_pago",
    "número de orden de pago": "numero_orden_pago",
    "fecha pago al banco": "fecha_pago_al_banco",
    "fecha de pago al banco": "fecha_pago_al_banco",
    "fecha acreditacion": "fecha_acreditacion",
    "fecha de acreditación": "fecha_acreditacion",
    "observaciones": "observaciones",
    "comedor": "comedor",
    "comedor_id": "comedor",
}


class ImportExpedientesView(FormView):
    template_name = "upload.html"
    form_class = CSVUploadForm
    success_url = reverse_lazy("upload")

    def parse_date(self, value):
        if not value:
            return None
        s = str(value).strip()
        for fmt in DATE_FORMATS:
            try:
                return datetime.strptime(s, fmt).date()
            except Exception:
                continue
        # intentar ISO
        try:
            return datetime.fromisoformat(s).date()
        except Exception:
            return None

    def parse_decimal(self, value):
        if value is None or value == "":
            return None
        s = str(value).replace(",", ".").strip()
        try:
            return Decimal(s)
        except Exception:
            return None

    def resolve_comedor(self, raw):
        if not raw:
            return None
        r = str(raw).strip()
        # si es pk
        if r.isdigit():
            try:
                return Comedor.objects.get(pk=int(r))
            except Comedor.DoesNotExist:
                return None
        # buscar por nombre
        try:
            return Comedor.objects.filter(nombre__iexact=r).first()
        except Exception:
            return None

    def form_valid(self, form):
        f = form.cleaned_data["file"]
        delim = form.cleaned_data["delimiter"]
        has_header = form.cleaned_data["has_header"]
        try:
            decoded = f.read().decode("utf-8-sig")
        except Exception:
            decoded = f.read().decode("latin-1")

        stream = io.StringIO(decoded)
        reader = csv.reader(stream, delimiter=delim)
        rows = list(reader)

        if not rows:
            messages.error(self.request, "CSV vacío.")
            return redirect(self.success_url)

        # determinar cabeceras
        if has_header:
            headers = [h.strip().lower() for h in rows[0]]
            data_rows = rows[1:]
        else:
            # si no hay cabecera necesita configuración previa
            messages.error(self.request, "CSV sin cabecera no soportado por defecto.")
            return redirect(self.success_url)

        # map headers a fields
        mapped = []
        for h in headers:
            key = h.replace('"', "").replace("'", "").strip().lower()
            mapped.append(HEADER_MAP.get(key, None))

        instances = []
        errors = []
        expected_cols = len(headers)
        with transaction.atomic():
            for i, row in enumerate(data_rows, start=2):
                # normalizar cantidad de columnas
                if len(row) < expected_cols:
                    row = row + [""] * (expected_cols - len(row))
                elif len(row) > expected_cols:
                    # recortar columnas extra para evitar IndexError
                    row = row[:expected_cols]
                kwargs = {}
                comedor_obj = None
                for col_idx, cell in enumerate(row):
                    field = mapped[col_idx]
                    if not field:
                        continue
                    val = (cell or "").strip()
                    if field == "monto":
                        kwargs[field] = self.parse_decimal(val)
                    elif field in ("fecha_pago_al_banco", "fecha_acreditacion"):
                        kwargs[field] = self.parse_date(val)
                    elif field == "comedor":
                        comedor_obj = self.resolve_comedor(val)
                    else:
                        kwargs[field] = val or None
                if comedor_obj:
                    kwargs["comedor"] = comedor_obj
                try:
                    inst = ExpedientePago(**kwargs)
                    inst.full_clean()
                    instances.append(inst)
                except Exception as e:
                    errors.append(f"Linea {i}: {e}")

            if instances:
                ExpedientePago.objects.bulk_create(instances)

        if errors:
            messages.warning(self.request, f"Import parcial: {len(instances)} creados, {len(errors)} errores.")
            for e in errors[:10]:
                messages.error(self.request, e)
        else:
            messages.success(self.request, f"{len(instances)} expedientes importados correctamente.")
        return redirect(self.success_url)
    
class ImportarExpedienteListView(LoginRequiredMixin, ListView):
    model = ArchivosImportados
    template_name = "importarexpedientes/list.html"
    context_object_name = "archivos_importados"
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get("busqueda")
        qs = super().get_queryset().order_by("-fecha_subida")
        if query:
            qs = qs.filter(usuario__username__icontains=query)
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("busqueda", "")
        return context
    
class ImportarExpedienteDetailView(LoginRequiredMixin, DetailView):
    model = ArchivosImportados
    template_name = "importarexpedientes/detail.html"
    context_object_name = "archivo_importado"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class ImportarExpedienteDeleteView(LoginRequiredMixin, DeleteView):
    model = ArchivosImportados
    template_name = "importarexpedientes/confirm_delete.html"
    success_url = reverse_lazy("importarexpedientes:list")
