import csv
import io

from decimal import Decimal
from datetime import datetime

from django.views.generic import FormView
from django.urls import reverse_lazy
from django.db import transaction
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.db.models import Q
from django.core.exceptions import ValidationError
from importarexpediente.forms import CSVUploadForm
from expedientespagos.models import ExpedientePago
from comedores.models import Comedor
from importarexpediente.models import (
    ArchivosImportados,
    ErroresImportacion,
    ExitoImportacion,
    RegistroImportado,
)


DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]

# mapeo de cabeceras posibles -> campo de modelo
HEADER_MAP = {
    # Expedientes
    "expediente": "expediente_pago",
    "expediente de pago": "expediente_pago",
    "expediente del convenio": "resolucion_pago",
    "resolucion": "resolucion_pago",
    "resolución de pago": "resolucion_pago",
    # Comedor identificación (por nombre o por id)
    "comedor": "anexo",
    "id": "comedor",
    # Monto total
    "monto": "monto",
    "total": "monto",
    # Orden de pago
    "numero orden pago": "numero_orden_pago",
    "número de orden de pago": "numero_orden_pago",
    # Fechas
    "fecha pago al banco": "fecha_pago_al_banco",
    "fecha de pago al banco": "fecha_pago_al_banco",
    "fecha acreditacion": "fecha_acreditacion",
    "fecha de acreditación": "fecha_acreditacion",
    # Otros
    "observaciones": "observaciones",
    "if cantidad de prestaciones": "if_cantidad_de_prestaciones",
    "if pagado": "if_pagado",
}

# Etiquetas amigables para usuarios no técnicos
FIELD_LABELS = {
    "expediente_pago": "Expediente de pago",
    "resolucion_pago": "Resolución de pago",
    "comedor": "Comedor",
    "anexo": "Comedor (anexo)",
    "monto": "Monto",
    "numero_orden_pago": "Número de orden de pago",
    "fecha_pago_al_banco": "Fecha de pago al banco",
    "fecha_acreditacion": "Fecha de acreditación",
    "observaciones": "Observaciones",
    "if_cantidad_de_prestaciones": "IF cantidad de prestaciones",
    "if_pagado": "IF pagado",
}


def _friendly_error_message(exc: Exception) -> str:
    """Convierte errores técnicos en mensajes claros para usuarios finales."""
    # ValidationError con detalles por campo
    if isinstance(exc, ValidationError):
        if hasattr(exc, "message_dict") and exc.message_dict:
            partes = []
            for campo, mensajes in exc.message_dict.items():
                etiqueta = FIELD_LABELS.get(campo, campo)
                detalle = "; ".join(str(m) for m in mensajes)
                partes.append(f"{etiqueta}: {detalle}")
            return ". ".join(partes)
        if hasattr(exc, "messages"):
            return "; ".join(str(m) for m in exc.messages)
    # Fallback genérico no técnico
    return (
        "No se pudo procesar la fila. Verifica que las fechas tengan formato DD/MM/AAAA, "
        "los montos sean numéricos y el comedor exista. Detalle: " + str(exc)
    )


class ImportExpedientesView(FormView):
    template_name = "upload.html"
    form_class = CSVUploadForm
    success_url = reverse_lazy("importarexpedientes_list")

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
        s = str(value)
        # Quitar símbolos de moneda, espacios y separadores de miles
        s = s.replace("$", "").replace(" ", "")
        s = s.replace(".", "")  # remover separador de miles
        s = s.replace(",", ".")  # usar punto como separador decimal
        s = s.strip()
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
        no_mapeadas = [h for (h, m) in zip(headers, mapped) if m is None]

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
                            parsed = self.parse_decimal(val)
                            kwargs[field] = parsed
                        elif field in ("fecha_pago_al_banco", "fecha_acreditacion"):
                            parsed = self.parse_date(val)
                            kwargs[field] = parsed
                        elif field == "comedor":
                            resolved_comedor = self.resolve_comedor(val)
                            if resolved_comedor is not None:
                                comedor_obj = resolved_comedor
                        else:
                            kwargs[field] = val or None

                    if comedor_obj:
                        kwargs["comedor"] = comedor_obj

                    # Validar sin guardar en ExpedientePago
                    inst = ExpedientePago(**kwargs)
                    try:
                        inst.full_clean()  # si falla, cae al except
                    except Exception as ve:
                        raise

                    # Registrar éxito (no se persiste ExpedientePago)
                    exito = ExitoImportacion.objects.create(
                        archivo_importado=base_upload,
                        fila=i,
                        mensaje="Fila válida",
                    )
                    success_count += 1

                except Exception as e:
                    # Registrar un error por cada fila inválida
                    friendly = _friendly_error_message(e)
                    msg = f"Fila {i} (Excel): {friendly}"
                    messages.error(self.request, msg)
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
                f"Validación parcial: {success_count} filas válidas, {error_count} errores.",
            )
        else:
            # Persistir contadores finales en el maestro
            try:
                base_upload.count_errores = error_count
                base_upload.count_exitos = success_count
                base_upload.save(update_fields=["count_errores", "count_exitos"])
            except Exception:
                pass
            messages.success(self.request, f"{success_count} filas válidas.")
        return redirect(self.success_url)


class ImportarExpedienteListView(LoginRequiredMixin, ListView):
    model = ArchivosImportados
    template_name = "importarexpediente_list.html"
    context_object_name = "archivos_importados"
    paginate_by = 10

    def get_queryset(self):
        qs = ArchivosImportados.objects.select_related("usuario").order_by(
            "-fecha_subida"
        )
        query = self.request.GET.get("busqueda", "").strip()
        if query:
            qs = qs.filter(
                Q(archivo__icontains=query) | Q(usuario__username__icontains=query)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("busqueda", "")
        return context


@login_required
def importarexpedientes_ajax(request):
    """
    Endpoint AJAX para búsqueda dinámica de importaciones.
    """
    query = request.GET.get("busqueda", "").strip()
    page = request.GET.get("page", 1)

    queryset = ArchivosImportados.objects.select_related("usuario").order_by(
        "-fecha_subida"
    )
    if query:
        queryset = queryset.filter(
            Q(archivo__icontains=query) | Q(usuario__username__icontains=query)
        )

    paginator = Paginator(queryset, 10)
    try:
        page_obj = paginator.get_page(page)
    except (ValueError, TypeError):
        page_obj = paginator.get_page(1)

    table_html = render_to_string(
        "partials/importarexpediente_list_rows.html",
        {"importarexpedientes": page_obj.object_list},
        request=request,
    )

    pagination_html = render_to_string(
        "components/pagination.html",
        {
            "is_paginated": page_obj.has_other_pages(),
            "page_obj": page_obj,
            "query": query,
            "prev_text": "Volver",
            "next_text": "Continuar",
        },
        request=request,
    )

    return JsonResponse(
        {
            "html": table_html,
            "pagination_html": pagination_html,
            "count": paginator.count,
            "current_page": page_obj.number,
            "total_pages": paginator.num_pages,
            "has_previous": page_obj.has_previous(),
            "has_next": page_obj.has_next(),
        }
    )


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
        query = self.request.GET.get("busqueda", "").strip()
        queryset = ErroresImportacion.objects.filter(
            archivo_importado_id=self.batch_id
        ).order_by("fila")
        if query:
            if query.isdigit():
                queryset = queryset.filter(fila=int(query))
            else:
                queryset = queryset.filter(mensaje__icontains=query)
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
        context["batch_id"] = self.batch_id
        context["error_count"] = errores.count()
        context["exito_count"] = exitos.count()
        return context


@login_required
def importarexpediente_detail_ajax(request, id_archivo):
    """
    Endpoint AJAX para búsqueda dinámica de errores por lote.
    """
    query = request.GET.get("busqueda", "").strip()
    page = request.GET.get("page", 1)

    queryset = (
        ErroresImportacion.objects.filter(archivo_importado_id=id_archivo)
        .select_related("archivo_importado")
        .order_by("fila")
    )
    if query:
        if query.isdigit():
            queryset = queryset.filter(fila=int(query))
        else:
            queryset = queryset.filter(mensaje__icontains=query)

    paginator = Paginator(queryset, 20)
    try:
        page_obj = paginator.get_page(page)
    except (ValueError, TypeError):
        page_obj = paginator.get_page(1)

    table_html = render_to_string(
        "partials/importarexpediente_detail_rows.html",
        {"importarexpedientes": page_obj.object_list},
        request=request,
    )

    pagination_html = render_to_string(
        "components/pagination.html",
        {
            "is_paginated": page_obj.has_other_pages(),
            "page_obj": page_obj,
            "query": query,
            "prev_text": "Volver",
            "next_text": "Continuar",
        },
        request=request,
    )

    return JsonResponse(
        {
            "html": table_html,
            "pagination_html": pagination_html,
            "count": paginator.count,
            "current_page": page_obj.number,
            "total_pages": paginator.num_pages,
            "has_previous": page_obj.has_previous(),
            "has_next": page_obj.has_next(),
        }
    )


class ImportDatosView(LoginRequiredMixin, FormView):
    """
    Vista para importar los datos validados en ExpedientePago.
    """

    template_name = "importar_datos.html"
    success_url = reverse_lazy("importarexpedientes_list")

    def dispatch(self, request, *args, **kwargs):
        # Tomar el id desde la URL
        self.batch_id = int(self.kwargs.get("id_archivo"))
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # Usar el id de la URL
        batch = get_object_or_404(ArchivosImportados, pk=self.batch_id)

        # Importar solo si el lote NO está marcado como completado
        if getattr(batch, "importacion_completada", False):
            messages.warning(
                request,
                "Este archivo ya fue importado. Primero borre los datos importados para reintentar.",
            )
            return redirect(self.success_url)

        # Abrir y decodificar el archivo CSV almacenado
        try:
            batch.archivo.open("rb")
            data = batch.archivo.read()
        finally:
            batch.archivo.close()

        try:
            decoded = data.decode("utf-8-sig")
        except Exception:
            decoded = data.decode("latin-1")

        # Intento simple de detección de delimitador (default ';', fallback ',')
        first_line = decoded.splitlines()[0] if decoded else ""
        delim = ";" if ";" in first_line else ","

        stream = io.StringIO(decoded)
        reader = csv.reader(stream, delimiter=delim)
        rows = list(reader)
        if not rows:
            messages.error(request, "El archivo CSV está vacío.")
            return redirect(self.success_url)

        # Cabeceras y mapeo
        headers = [h.strip().lower() for h in rows[0]]
        data_rows = rows[1:]
        mapped = []
        for h in headers:
            key = h.replace('"', "").replace("'", "").strip().lower()
            mapped.append(HEADER_MAP.get(key, None))

        expected_cols = len(headers)
        imported_count = 0
        error_count = 0

        with transaction.atomic():
            for i, row in enumerate(data_rows, start=2):
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
                            # Reutilizar parseo de moneda
                            s = val.replace("$", "").replace(" ", "")
                            s = s.replace(".", "")
                            s = s.replace(",", ".")
                            try:
                                kwargs[field] = Decimal(s)
                            except Exception:
                                kwargs[field] = None
                        elif field in ("fecha_pago_al_banco", "fecha_acreditacion"):
                            # Parseo de fechas (formatos comunes)
                            parsed = None
                            for fmt in DATE_FORMATS:
                                try:
                                    parsed = datetime.strptime(val, fmt).date()
                                    break
                                except Exception:
                                    continue
                            if parsed is None:
                                try:
                                    parsed = datetime.fromisoformat(val).date()
                                except Exception:
                                    parsed = None
                            kwargs[field] = parsed
                        elif field == "comedor":
                            # Resolver FK por id o nombre
                            r = val.strip()
                            resolved = None
                            if r:
                                if r.isdigit():
                                    try:
                                        resolved = Comedor.objects.get(pk=int(r))
                                    except Comedor.DoesNotExist:
                                        resolved = None
                                if resolved is None:
                                    resolved = Comedor.objects.filter(
                                        nombre__iexact=r
                                    ).first()
                            if resolved is not None:
                                comedor_obj = resolved
                        else:
                            kwargs[field] = val or None

                    if comedor_obj:
                        kwargs["comedor"] = comedor_obj

                    # Crear y validar instancia
                    inst = ExpedientePago(**kwargs)
                    inst.full_clean()
                    inst.save()

                    # Vincular con el éxito de la misma fila (si existe) y registrar el id
                    exito = ExitoImportacion.objects.filter(
                        archivo_importado=batch,
                        fila=i,
                    ).first()
                    if exito is None:
                        exito = ExitoImportacion.objects.create(
                            archivo_importado=batch,
                            fila=i,
                            mensaje="Importado",
                        )
                    RegistroImportado.objects.create(
                        exito_importacion=exito,
                        expediente_pago=inst,
                    )
                    imported_count += 1

                except Exception as e:
                    error_count += 1
                    friendly = _friendly_error_message(e)
                    messages.error(request, f"Fila {i} (Excel): {friendly}")

        # Marcar el lote como importado si se creó al menos un registro
        try:
            if imported_count > 0:
                batch.importacion_completada = True
                batch.save(update_fields=["importacion_completada"])
        except Exception as e:
            messages.error(request, f"No se pudo marcar el lote como completado: {e}")

        if error_count:
            messages.warning(
                request,
                f"Importación finalizada: {imported_count} registros importados, {error_count} errores.",
            )
        else:
            messages.success(
                request,
                f"Importación completada: {imported_count} registros importados.",
            )
        return redirect(self.success_url)

    # Permitir importación vía GET (desde el botón en el detalle)
    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


class BorrarDatosImportadosView(LoginRequiredMixin, FormView):
    """
    Vista para borrar los datos importados de un lote específico.
    """

    template_name = "borrar_datos_importados.html"
    success_url = reverse_lazy("importarexpedientes_list")

    def dispatch(self, request, *args, **kwargs):
        # Tomar el id desde la URL
        self.batch_id = int(self.kwargs.get("id_archivo"))
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # Usar el id de la URL
        batch = get_object_or_404(ArchivosImportados, pk=self.batch_id)

        registros_qs = RegistroImportado.objects.filter(
            exito_importacion__archivo_importado=batch
        )
        # Capturar los IDs de expedientes antes de borrar los registros
        expediente_ids = list(registros_qs.values_list("expediente_pago_id", flat=True))

        with transaction.atomic():
            # Primero borrar los registros hijos para respetar las FK (DO_NOTHING)
            reg_deleted, _ = registros_qs.delete()
            # Luego borrar los expedientes creados por el lote
            exp_deleted, _ = ExpedientePago.objects.filter(
                id__in=expediente_ids
            ).delete()

        # Resetear el estado de importación del lote
        try:
            batch.importacion_completada = False
            batch.save(update_fields=["importacion_completada"])
        except Exception as e:
            messages.error(request, f"No se pudo resetear importacion_completada: {e}")

        messages.success(
            request,
            f"Borrado completado: {reg_deleted} registros y {exp_deleted} expedientes eliminados.",
        )
        return redirect(self.success_url)

    # Permitir borrado vía GET (desde el botón en el detalle)
    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)
