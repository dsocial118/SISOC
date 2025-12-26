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
from .models import (
    ArchivosImportados,
    ErroresImportacion,
    ExitoImportacion,
    RegistroImportado,
)


DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]

# mapeo de cabeceras posibles -> campo de modelo
HEADER_MAP = {
    "expediente": "expediente_pago",
    "expediente de pago": "expediente_pago",
    "resolucion": "resolucion_pago",
    "resolución de pago": "resolucion_pago",
    "COMEDOR": "anexo",
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
    "ID": "comedor",
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
            # Identificador único del lote = PK del maestro (si el modelo tiene el campo id_archivo, lo seteamos)
            batch_id = base_upload.pk
            if hasattr(base_upload, "id_archivo"):
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
            # Registrar error por archivo vacío (no se guardan datos en ExpedientePago)
            err_msg = "CSV vacío."
            ErroresImportacion.objects.create(
                archivo_importado=base_upload,
                fila=0,
                mensaje=err_msg,
            )
            # Actualizar contadores en el maestro
            try:
                base_upload.count_errores = 1
                base_upload.count_exitos = 0
                base_upload.save(update_fields=["count_errores", "count_exitos"])
            except Exception:
                pass
            messages.error(self.request, err_msg)
            return redirect(self.success_url)

        # determinar cabeceras
        if has_header:
            headers = [h.strip().lower() for h in rows[0]]
            data_rows = rows[1:]
        else:
            err_msg = "CSV sin cabecera no soportado por defecto."
            ErroresImportacion.objects.create(
                archivo_importado=base_upload,
                fila=0,
                mensaje=err_msg,
            )
            # Actualizar contadores en el maestro
            try:
                base_upload.count_errores = 1
                base_upload.count_exitos = 0
                base_upload.save(update_fields=["count_errores", "count_exitos"])
            except Exception:
                pass
            messages.error(self.request, err_msg)
            return redirect(self.success_url)

        # map headers a fields
        mapped = []
        for h in headers:
            key = h.replace('"', "").replace("'", "").strip().lower()
            mapped.append(HEADER_MAP.get(key, None))

        success_count = 0
        error_count = 0
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

                    # Validar sin guardar en ExpedientePago
                    inst = ExpedientePago(**kwargs)
                    inst.full_clean()  # si falla, cae al except

                    # Registrar éxito (no se persiste ExpedientePago)
                    exito = ExitoImportacion.objects.create(
                        archivo_importado=base_upload,
                        fila=i,
                        mensaje="Fila válida",
                    )
                    success_count += 1

                except Exception as e:
                    # Registrar un error por cada fila inválida
                    msg = f"Línea {i}: {e}"
                    ErroresImportacion.objects.create(
                        archivo_importado=base_upload,
                        fila=i,
                        mensaje=msg,
                    )
                    error_count += 1

            # No se guarda nada en ExpedientePago por requerimiento

        if error_count:
            # Persistir contadores finales en el maestro
            try:
                base_upload.count_errores = error_count
                base_upload.count_exitos = success_count
                base_upload.save(update_fields=["count_errores", "count_exitos"])
            except Exception:
                pass
            messages.warning(
                self.request,
                f"Validación parcial: {success_count} filas válidas, {error_count} errores."
            )
        else:
            # Persistir contadores finales en el maestro
            try:
                base_upload.count_errores = error_count
                base_upload.count_exitos = success_count
                base_upload.save(update_fields=["count_errores", "count_exitos"])
            except Exception:
                pass
            messages.success(
                self.request, f"{success_count} filas válidas."
            )
        return redirect(self.success_url)
    
class ImportarExpedienteListView(LoginRequiredMixin, ListView):
    model = ArchivosImportados
    template_name = "importarexpediente_list.html"
    context_object_name = "archivos_importados"
    paginate_by = 10

    def get_queryset(self):
        qs = (
            ArchivosImportados.objects
            .select_related("usuario")
            .order_by("-fecha_subida")
        )
        query = self.request.GET.get("busqueda", "").strip()
        if query:
            qs = qs.filter(archivo__icontains=query)
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("busqueda", "")
        return context
    
class ImportarExpedienteDetalleListView(LoginRequiredMixin, ListView):
    """
    Lista todos los registros (maestro + errores) de un mismo lote (id_archivo).
    """
    model = ErroresImportacion
    template_name = "importarexpediente_detail.html"
    context_object_name = "registros_del_archivo"
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        self.batch_id = int(self.kwargs.get("id_archivo"))
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        # Mostrar solo el archivo maestro correspondiente al id recibido en la URL
        query = self.request.GET.get("busqueda")
        if query:
            queryset = ErroresImportacion.objects.filter(archivo_importado_id=self.batch_id)
            return queryset
        else:
            queryset = ErroresImportacion.objects.filter(archivo_importado_id=self.batch_id)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        errores = ErroresImportacion.objects.filter(
            archivo_importado_id=self.batch_id
        ).order_by("fila")
        exitos = ExitoImportacion.objects.filter(
            archivo_importado_id=self.batch_id
        ).order_by("fila")
        context["query"] = self.request.GET.get("busqueda", "")
        context["error_count"] = errores.count()
        context["exito_count"] = exitos.count()
        return context