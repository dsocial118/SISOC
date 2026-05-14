from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseNotAllowed, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views.generic import FormView, ListView

from expedientespagos.models import ExpedientePago
from importarexpediente.forms import CSVUploadForm
from importarexpediente.models import (
    ArchivosImportados,
    ErroresImportacion,
    ExitoImportacion,
    RegistroImportado,
)
from importarexpediente.services import (
    EmptyImportFileError,
    HeaderlessImportFileError,
    aplicar_estados_por_lote,
    ensure_import_required_defaults,
    expediente_pago_from_row,
    extract_numero_expediente_pago,
    friendly_error_message,
    parse_import_file,
)


MAX_ERROR_MESSAGES = 20


def _register_batch_file_error(batch, message):
    ErroresImportacion.objects.create(
        archivo_importado=batch,
        fila=0,
        mensaje=message,
    )
    batch.count_errores = 1
    batch.count_exitos = 0
    batch.save(update_fields=["count_errores", "count_exitos"])


class ImportExpedientesView(LoginRequiredMixin, FormView):
    template_name = "upload.html"
    form_class = CSVUploadForm
    success_url = reverse_lazy("importarexpedientes_list")

    # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    def form_valid(self, form):
        uploaded_file = form.cleaned_data["file"]
        delimiter = form.cleaned_data["delimiter"]
        has_header = form.cleaned_data["has_header"]

        try:
            try:
                uploaded_file.seek(0)
            except Exception:
                pass
            base_upload = ArchivosImportados(
                usuario=self.request.user,
                delimiter=delimiter,
            )
            base_upload.archivo.save(uploaded_file.name, uploaded_file, save=True)
            if hasattr(base_upload, "id_archivo"):
                base_upload.id_archivo = base_upload.pk
                base_upload.save(update_fields=["id_archivo"])
        except Exception as e:
            messages.error(self.request, f"No se pudo guardar el archivo: {e}")
            return redirect(self.success_url)

        try:
            uploaded_file.seek(0)
            data = uploaded_file.read()
        except Exception:
            data = b""

        try:
            parsed_file = parse_import_file(
                data,
                uploaded_file.name,
                delimiter,
                has_header,
            )
        except (EmptyImportFileError, HeaderlessImportFileError) as e:
            error_message = str(e)
            _register_batch_file_error(base_upload, error_message)
            messages.error(self.request, error_message)
            return redirect(self.success_url)
        except Exception as e:
            error_message = f"No se pudo leer el archivo: {e}"
            _register_batch_file_error(base_upload, error_message)
            messages.error(self.request, error_message)
            return redirect(self.success_url)

        detected_delimiter = parsed_file.detected_delimiter
        if (
            parsed_file.file_format == "csv"
            and detected_delimiter
            and detected_delimiter != delimiter
        ):
            messages.warning(
                self.request,
                (
                    f"El delimitador seleccionado fue '{delimiter}', pero el archivo "
                    f"parece usar '{detected_delimiter}'. Se usar\u00e1 '{detected_delimiter}'."
                ),
            )
            delimiter = detected_delimiter
            base_upload.delimiter = delimiter
            base_upload.save(update_fields=["delimiter"])

        numero_expediente_guardado = False
        success_count = 0
        error_count = 0

        with transaction.atomic():
            for row_number, row in parsed_file.rows:
                try:
                    kwargs, specific_errors = expediente_pago_from_row(
                        parsed_file,
                        row,
                    )
                    numero_expediente = extract_numero_expediente_pago(
                        parsed_file,
                        row,
                    )
                    if not numero_expediente_guardado and numero_expediente:
                        base_upload.numero_expediente_pago = numero_expediente
                        base_upload.save(update_fields=["numero_expediente_pago"])
                        numero_expediente_guardado = True

                    if specific_errors:
                        for message in specific_errors:
                            if error_count < MAX_ERROR_MESSAGES:
                                messages.error(
                                    self.request,
                                    f"Fila {row_number} (Excel): {message}",
                                )
                            ErroresImportacion.objects.create(
                                archivo_importado=base_upload,
                                fila=row_number,
                                mensaje=message,
                            )
                        error_count += len(specific_errors)
                        continue

                    instance = ExpedientePago(**kwargs)
                    instance.full_clean()
                    ExitoImportacion.objects.create(
                        archivo_importado=base_upload,
                        fila=row_number,
                        mensaje="Fila v\u00e1lida",
                    )
                    success_count += 1
                except Exception as e:
                    friendly = friendly_error_message(e)
                    message = f"Fila {row_number} (Excel): {friendly}"
                    if error_count < MAX_ERROR_MESSAGES:
                        messages.error(self.request, message)
                    ErroresImportacion.objects.create(
                        archivo_importado=base_upload,
                        fila=row_number,
                        mensaje=message,
                    )
                    error_count += 1

        base_upload.count_errores = error_count
        base_upload.count_exitos = success_count
        base_upload.save(update_fields=["count_errores", "count_exitos"])
        if error_count:
            messages.warning(
                self.request,
                (
                    f"Validaci\u00f3n parcial: {success_count} filas v\u00e1lidas, "
                    f"{error_count} errores."
                ),
            )
        else:
            messages.success(self.request, f"{success_count} filas v\u00e1lidas.")
        return redirect(self.success_url)


class ImportarExpedienteListView(LoginRequiredMixin, ListView):
    model = ArchivosImportados
    template_name = "importarexpediente_list.html"
    context_object_name = "archivos_importados"
    paginate_by = 10

    def get_queryset(self):
        queryset = ArchivosImportados.objects.select_related("usuario").order_by(
            "-fecha_subida"
        )
        queryset = queryset.filter(usuario=self.request.user)
        query = self.request.GET.get("busqueda", "").strip()
        if query:
            queryset = queryset.filter(
                Q(archivo__icontains=query) | Q(usuario__username__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("busqueda", "")
        return context


@login_required
def importarexpedientes_ajax(request):
    query = request.GET.get("busqueda", "").strip()
    page = request.GET.get("page", 1)

    queryset = (
        ArchivosImportados.objects.select_related("usuario")
        .filter(usuario=request.user)
        .order_by("-fecha_subida")
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
    model = ErroresImportacion
    template_name = "importarexpediente_detail.html"
    context_object_name = "registros_del_archivo"
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        self.batch_id = int(self.kwargs.get("id_archivo"))
        self.batch = get_object_or_404(
            ArchivosImportados, pk=self.batch_id, usuario=request.user
        )
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        query = self.request.GET.get("busqueda", "").strip()
        queryset = ErroresImportacion.objects.filter(
            archivo_importado=self.batch
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
            archivo_importado=self.batch
        ).order_by("fila")
        exitos = ExitoImportacion.objects.filter(archivo_importado=self.batch).order_by(
            "fila"
        )
        context["query"] = self.request.GET.get("busqueda", "")
        context["batch_id"] = self.batch_id
        context["batch"] = self.batch
        context["error_count"] = errores.count()
        context["exito_count"] = exitos.count()
        return context


@login_required
def importarexpediente_detail_ajax(request, id_archivo):
    query = request.GET.get("busqueda", "").strip()
    page = request.GET.get("page", 1)

    queryset = (
        ErroresImportacion.objects.filter(
            archivo_importado_id=id_archivo,
            archivo_importado__usuario=request.user,
        )
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
    template_name = "importar_datos.html"
    success_url = reverse_lazy("importarexpedientes_list")

    def dispatch(self, request, *args, **kwargs):
        self.batch_id = int(self.kwargs.get("id_archivo"))
        return super().dispatch(request, *args, **kwargs)

    # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    def post(self, request, *args, **kwargs):
        batch = get_object_or_404(
            ArchivosImportados, pk=self.batch_id, usuario=request.user
        )

        try:
            batch.archivo.open("rb")
            data = batch.archivo.read()
        finally:
            batch.archivo.close()

        chosen_delimiter = getattr(batch, "delimiter", ",") or ","
        try:
            parsed_file = parse_import_file(
                data,
                batch.archivo.name,
                chosen_delimiter,
                has_header=True,
            )
        except (EmptyImportFileError, HeaderlessImportFileError) as e:
            messages.error(request, str(e))
            return redirect(self.success_url)
        except Exception as e:
            messages.error(request, f"No se pudo leer el archivo: {e}")
            return redirect(self.success_url)

        detected_delimiter = parsed_file.detected_delimiter
        if (
            parsed_file.file_format == "csv"
            and detected_delimiter
            and detected_delimiter != chosen_delimiter
        ):
            messages.warning(
                request,
                (
                    f"El delimitador seleccionado fue '{chosen_delimiter}', pero el archivo "
                    f"parece usar '{detected_delimiter}'. Se usar\u00e1 '{detected_delimiter}'."
                ),
            )

        imported_count = 0
        error_count = 0
        estados_actualizados = 0

        try:
            with transaction.atomic():
                batch = ArchivosImportados.objects.select_for_update().get(
                    pk=self.batch_id, usuario=request.user
                )
                if getattr(batch, "importacion_completada", False):
                    messages.warning(
                        request,
                        (
                            "Este archivo ya fue importado. Primero borre los datos "
                            "importados para reintentar."
                        ),
                    )
                    return redirect(self.success_url)

                for row_number, row in parsed_file.rows:
                    try:
                        kwargs, specific_errors = expediente_pago_from_row(
                            parsed_file,
                            row,
                        )
                        if specific_errors:
                            for message in specific_errors:
                                if error_count < MAX_ERROR_MESSAGES:
                                    messages.error(
                                        request,
                                        f"Fila {row_number} (Excel): {message}",
                                    )
                                ErroresImportacion.objects.create(
                                    archivo_importado=batch,
                                    fila=row_number,
                                    mensaje=message,
                                )
                            error_count += len(specific_errors)
                            continue

                        ensure_import_required_defaults(kwargs)
                        instance = ExpedientePago(**kwargs)
                        instance.full_clean()
                        instance.save()

                        exito = ExitoImportacion.objects.filter(
                            archivo_importado=batch,
                            fila=row_number,
                        ).first()
                        if exito is None:
                            exito = ExitoImportacion.objects.create(
                                archivo_importado=batch,
                                fila=row_number,
                                mensaje="Importado",
                            )
                        RegistroImportado.objects.create(
                            exito_importacion=exito,
                            expediente_pago=instance,
                        )
                        imported_count += 1
                    except Exception as e:
                        friendly = friendly_error_message(e)
                        if error_count < MAX_ERROR_MESSAGES:
                            messages.error(
                                request,
                                f"Fila {row_number} (Excel): {friendly}",
                            )
                        error_count += 1

                if imported_count > 0:
                    batch.importacion_completada = True
                    batch.save(update_fields=["importacion_completada"])
                    estados_actualizados = aplicar_estados_por_lote(batch, request.user)
        except Exception as e:
            messages.error(request, f"No se pudo completar la importaci\u00f3n: {e}")
            return redirect(self.success_url)

        if error_count:
            messages.warning(
                request,
                (
                    f"Importaci\u00f3n finalizada: {imported_count} registros "
                    f"importados, {error_count} errores."
                ),
            )
        else:
            messages.success(
                request,
                (
                    f"Importaci\u00f3n completada: {imported_count} registros importados. "
                    f"Estados actualizados: {estados_actualizados}."
                ),
            )
        return redirect(self.success_url)

    def get(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(["POST"])


class BorrarDatosImportadosView(LoginRequiredMixin, FormView):
    template_name = "borrar_datos_importados.html"
    success_url = reverse_lazy("importarexpedientes_list")

    def dispatch(self, request, *args, **kwargs):
        self.batch_id = int(self.kwargs.get("id_archivo"))
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        batch = get_object_or_404(
            ArchivosImportados, pk=self.batch_id, usuario=request.user
        )

        registros_qs = RegistroImportado.objects.filter(
            exito_importacion__archivo_importado=batch
        )
        expediente_ids = list(registros_qs.values_list("expediente_pago_id", flat=True))

        with transaction.atomic():
            registros_eliminados, _ = registros_qs.delete()
            expedientes_eliminados, _ = ExpedientePago.all_objects.filter(
                id__in=expediente_ids
            ).hard_delete()

        try:
            batch.importacion_completada = False
            batch.save(update_fields=["importacion_completada"])
        except Exception as e:
            messages.error(request, f"No se pudo resetear importacion_completada: {e}")

        messages.success(
            request,
            (
                f"Borrado completado: {registros_eliminados} registros y "
                f"{expedientes_eliminados} expedientes eliminados."
            ),
        )
        return redirect(self.success_url)

    def get(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(["POST"])
