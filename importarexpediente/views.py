from decimal import Decimal
import csv
import io
from datetime import datetime

from django.views.generic import FormView
from django.urls import reverse_lazy
from django.db import transaction
from django.contrib import messages
from django.shortcuts import redirect,get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (
    ListView
)
from django.http import Http404
from django.db.models import Max, Subquery
from django.db.models import OuterRef, Q, Count
from django.db.models.functions import Coalesce
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

        # 1) Guardar el archivo subido una sola vez (registro "maestro")
        try:
            try:
                f.seek(0)
            except Exception:
                pass
            base_upload = ArchivosImportados(usuario=self.request.user)
            base_upload.archivo.save(f.name, f, save=True)
            # Identificador único del lote = PK del maestro
            batch_id = base_upload.pk
            base_upload.id_archivo = batch_id
            base_upload.save(update_fields=["id_archivo"])
        except Exception as e:
            messages.error(self.request, f"No se pudo guardar el archivo: {e}")
            return redirect(self.success_url)

        # 2) Volver al inicio del stream para procesar el CSV
        try:
            f.seek(0)
            decoded = f.read().decode("utf-8-sig")
        except Exception:
            f.seek(0)
            decoded = f.read().decode("latin-1")

        stream = io.StringIO(decoded)
        reader = csv.reader(stream, delimiter=delim)
        rows = list(reader)

        if not rows:
            # Registrar error por archivo vacío
            err_msg = "CSV vacío."
            err = ArchivosImportados(usuario=self.request.user, error=err_msg, id_archivo=batch_id)
            err.archivo.name = base_upload.archivo.name
            err.save()
            messages.error(self.request, err_msg)
            return redirect(self.success_url)

        # determinar cabeceras
        if has_header:
            headers = [h.strip().lower() for h in rows[0]]
            data_rows = rows[1:]
        else:
            err_msg = "CSV sin cabecera no soportado por defecto."
            err = ArchivosImportados(usuario=self.request.user, error=err_msg, id_archivo=batch_id)
            err.archivo.name = base_upload.archivo.name
            err.save()
            messages.error(self.request, err_msg)
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
                    row = row[:expected_cols]

                kwargs = {}
                comedor_obj = None
                try:
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

                    inst = ExpedientePago(**kwargs)
                    inst.full_clean()
                    instances.append(inst)

                except Exception as e:
                    # 3) Guardar un registro por cada error
                    msg = f"Línea {i}: {e}"
                    errors.append(msg)
                    err = ArchivosImportados(
                        usuario=self.request.user,
                        error=msg,
                        id_archivo=batch_id,
                    )
                    # Reutilizamos el mismo archivo sin duplicarlo en el storage
                    err.archivo.name = base_upload.archivo.name
                    err.save()

            if instances:
                ExpedientePago.objects.bulk_create(instances)

        if errors:
            messages.warning(
                self.request,
                f"Import parcial: {len(instances)} creados, {len(errors)} errores."
            )
        else:
            messages.success(
                self.request, f"{len(instances)} expedientes importados correctamente."
            )
        return redirect(self.success_url)
    
class ImportarExpedienteListView(LoginRequiredMixin, ListView):
    model = ArchivosImportados
    template_name = "importarexpediente_list.html"
    context_object_name = "archivos_importados"
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get("busqueda")
        base_qs = ArchivosImportados.objects.all()
        if query:
            base_qs = base_qs.filter(usuario__username__icontains=query)

            # subquery con el id más reciente por cada archivo
            latest_ids = (
                base_qs.order_by()  # importante: limpiar order_by para la agregación
                .values("archivo")
                .annotate(latest_id=Max("id"))
                .values("latest_id")
            )
            error_count_sq = (
            ArchivosImportados.objects.filter(archivo=OuterRef("archivo"))
            .order_by()
            .values("archivo")
            .annotate(
                errs=Count(
                    "id",
                    filter=Q(error__isnull=False) & ~Q(error=""),
                )
            )
            .values("errs")
        )
            queryset = ArchivosImportados.objects.filter(id__in=Subquery(latest_ids)).annotate(error_count=Coalesce(Subquery(error_count_sq), 0)).order_by("-fecha_subida")
        else:
            latest_ids = (
                base_qs.order_by()  # importante: limpiar order_by para la agregación
                .values("archivo")
                .annotate(latest_id=Max("id"))
                .values("latest_id")
            )
            error_count_sq = (
            ArchivosImportados.objects.filter(archivo=OuterRef("archivo"))
            .order_by()
            .values("archivo")
            .annotate(
                errs=Count(
                    "id",
                    filter=Q(error__isnull=False) & ~Q(error=""),
                )
            )
            .values("errs")
        )
            queryset = ArchivosImportados.objects.filter(id__in=Subquery(latest_ids)).annotate(error_count=Coalesce(Subquery(error_count_sq), 0)).order_by("-fecha_subida")
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("busqueda", "")
        return context
    
class ImportarExpedienteDetalleListView(LoginRequiredMixin, ListView):
    """
    Lista todos los registros (maestro + errores) de un mismo lote (id_archivo).
    """
    model = ArchivosImportados
    template_name = "importarexpediente_detail.html"
    context_object_name = "registros_del_archivo"
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        self.batch_id = int(self.kwargs.get("id_archivo"))
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = (
            ArchivosImportados.objects
            .filter(id_archivo=self.batch_id)
            .select_related("usuario")
            .order_by("-fecha_subida")
        )
        if not qs.exists():
            # Intentar caer al “maestro” por PK si no hubo registros con id_archivo
            maestro = ArchivosImportados.objects.filter(id=self.batch_id).first()
            if maestro:
                qs = (
                    ArchivosImportados.objects
                    .filter(id_archivo=maestro.id_archivo or maestro.id)
                    .select_related("usuario")
                    .order_by("-fecha_subida")
                )
        if not qs.exists():
            raise Http404("Lote no encontrado")
        self._qs = qs
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        maestro = ArchivosImportados.objects.filter(id=self.batch_id).first()
        ctx["batch_id"] = self.batch_id
        ctx["archivo_maestro"] = maestro
        # cantidad total de errores en el lote
        qs = getattr(self, "_qs", self.get_queryset())
        ctx["error_count"] = qs.exclude(error__isnull=True).exclude(error="").count()
        return ctx