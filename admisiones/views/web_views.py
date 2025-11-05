from django.contrib import messages
from django.db.models import Q
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, ListView, UpdateView, DetailView
from django.core.paginator import Paginator
import logging

logger = logging.getLogger(__name__)
from admisiones.forms.admisiones_forms import (
    AdmisionForm,
    LegalesRectificarForm,
    LegalesNumIFForm,
)
from admisiones.models.admisiones import (
    Admision,
    ArchivoAdmision,
    InformeComplementario,
)
from admisiones.services.admisiones_service import AdmisionService
from admisiones.services.informes_service import InformeService
from admisiones.services.legales_service import LegalesService
from django.views.generic.edit import FormMixin
from django.template.loader import render_to_string
from django.urls import reverse
from acompanamientos.acompanamiento_service import AcompanamientoService
from expedientespagos.services import ExpedientesPagosService
from rendicioncuentasmensual.services import RendicionCuentaMensualService
from rendicioncuentasfinal.models import RendicionCuentasFinal
from rendicioncuentasfinal.rendicion_cuentas_final_service import (
    RendicionCuentasFinalService,
)
from historial.services.historial_service import HistorialService


@login_required
@require_POST
def subir_archivo_admision(request, admision_id, documentacion_id):
    archivo = request.FILES.get("archivo")
    if not archivo:
        return JsonResponse(
            {"success": False, "error": "No se recibio un archivo"}, status=400
        )

    archivo_admision, created = AdmisionService.handle_file_upload(
        admision_id, documentacion_id, archivo
    )
    if not archivo_admision:
        return JsonResponse(
            {"success": False, "error": "No se pudo guardar el archivo"}, status=400
        )

    documento = AdmisionService._serialize_documentacion(
        archivo_admision.documentacion, archivo_admision
    )
    html = render_to_string(
        "admisiones/includes/documento_row.html",
        {"doc": documento, "admision": archivo_admision.admision},
        request=request,
    )

    return JsonResponse(
        {
            "success": True,
            "html": html,
            "row_id": documento.get("row_id"),
            "documento": documento,
            "estado_display": documento.get("estado"),
            "estado_valor": documento.get("estado_valor"),
            "archivo_id": archivo_admision.id,
        }
    )


@login_required
def eliminar_archivo_admision(request, admision_id, documentacion_id):
    if request.method != "DELETE":
        return JsonResponse(
            {"success": False, "error": "Metodo no permitido"}, status=405
        )

    admision = get_object_or_404(Admision, pk=admision_id)

    if not request.user.is_superuser:
        comedor = admision.comedor
        if not comedor:
            return JsonResponse(
                {"success": False, "error": "Admision sin comedor asociado."},
                status=403,
            )

        if not AdmisionService._verificar_permiso_dupla(request.user, comedor):
            return JsonResponse(
                {
                    "success": False,
                    "error": "Sin permisos para modificar esta admision.",
                },
                status=403,
            )

    archivo = (
        ArchivoAdmision.objects.filter(
            admision_id=admision_id, documentacion_id=documentacion_id
        ).first()
        or ArchivoAdmision.objects.filter(
            admision_id=admision_id, id=request.GET.get("archivo_id")
        ).first()
        or get_object_or_404(
            ArchivoAdmision, admision_id=admision_id, id=documentacion_id
        )
    )

    estado_actual = (archivo.estado or "").strip().lower()
    if estado_actual in {"aceptado", "a validar abogado"}:
        return JsonResponse(
            {
                "success": False,
                "error": "No se puede eliminar un documento en estado aceptado o a validar abogado.",
            },
            status=400,
        )

    documentacion = archivo.documentacion
    nombre_documento = (
        documentacion.nombre
        if documentacion
        else archivo.nombre_personalizado or "Documento adicional"
    )
    es_personalizado = documentacion is None

    documento_serializado = (
        AdmisionService._serialize_documentacion(documentacion, None)
        if documentacion
        else None
    )
    AdmisionService.delete_admision_file(archivo)

    response_data = {
        "success": True,
        "nombre": nombre_documento,
        "personalizado": es_personalizado,
    }

    if documento_serializado:
        html = render_to_string(
            "admisiones/includes/documento_row.html",
            {"doc": documento_serializado, "admision": admision},
            request=request,
        )
        response_data.update(
            {"html": html, "row_id": documento_serializado.get("row_id")}
        )

    return JsonResponse(response_data)


@login_required
def actualizar_estado_archivo(request):
    resultado = AdmisionService.actualizar_estado_ajax(request)

    if resultado.get("success"):
        return JsonResponse(
            {
                "success": True,
                "nuevo_estado": resultado.get("nuevo_estado"),
                "grupo_usuario": resultado.get("grupo_usuario"),
                "mostrar_select": resultado.get("mostrar_select", False),
                "opciones": resultado.get("opciones", []),
            }
        )
    else:
        return JsonResponse(
            {"success": False, "error": resultado.get("error", "Error desconocido")},
            status=400,
        )


@login_required
@require_POST
def actualizar_numero_gde_archivo(request):
    resultado = AdmisionService.actualizar_numero_gde_ajax(request)

    response_data = {
        "success": resultado.get("success"),
        "numero_gde": resultado.get("numero_gde"),
        "valor_anterior": resultado.get("valor_anterior"),
    }

    if not resultado.get("success"):
        response_data["error"] = resultado.get("error", "Error desconocido")
        return JsonResponse(response_data, status=400)

    return JsonResponse(response_data)


@login_required
@require_POST
def crear_documento_personalizado(request, admision_id):
    archivo = request.FILES.get("archivo")
    nombre = request.POST.get("nombre", "")

    archivo_admision, error = AdmisionService.crear_documento_personalizado(
        admision_id, nombre, archivo, request.user
    )

    if not archivo_admision:
        status_code = 403 if error and "permiso" in error.lower() else 400
        return JsonResponse(
            {"success": False, "error": error or "No se pudo guardar el documento."},
            status=status_code,
        )

    documento = AdmisionService.serialize_documento_personalizado(archivo_admision)
    html = render_to_string(
        "admisiones/includes/documento_row.html",
        {"doc": documento, "admision": archivo_admision.admision},
        request=request,
    )

    return JsonResponse(
        {"success": True, "documento": documento, "html": html}, status=201
    )


class AdmisionesTecnicosListView(LoginRequiredMixin, ListView):
    model = Admision
    template_name = "admisiones/admisiones_tecnicos_list.html"
    context_object_name = "admisiones"
    paginate_by = 10

    def get_queryset(self):
        return AdmisionService.get_admisiones_tecnicos_queryset(
            self.request.user, self.request.GET.get("busqueda", "")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        table_items = AdmisionService.get_admisiones_tecnicos_table_data(
            context["admisiones"], self.request.user
        )

        context.update(
            {
                "query": self.request.GET.get("busqueda", ""),
                "breadcrumb_items": [
                    {"name": "Admisiones", "url": "admisiones_tecnicos_listar"},
                    {"name": "Listar", "active": True},
                ],
                "table_headers": [
                    {"title": "Nombre"},
                    {"title": "Tipo Comedor"},
                    {"title": "Ubicación"},
                    {"title": "Convenio"},
                    {"title": "Tipo"},
                    {"title": "Estado"},
                ],
                "table_items": table_items,
            }
        )
        return context


class AdmisionesTecnicosCreateView(LoginRequiredMixin, CreateView):
    model = Admision
    template_name = "admisiones/admisiones_tecnicos_form.html"
    form_class = AdmisionForm
    context_object_name = "admision"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(AdmisionService.get_admision_create_context(self.kwargs["pk"]))
        return context

    def post(self, request, *args, **kwargs):
        tipo_convenio_id = request.POST.get("tipo_convenio")
        if tipo_convenio_id:
            admision = AdmisionService.create_admision(
                self.kwargs["pk"], tipo_convenio_id
            )
            return redirect("admisiones_tecnicos_editar", pk=admision.pk)
        return self.get(request, *args, **kwargs)


class AdmisionesTecnicosUpdateView(LoginRequiredMixin, UpdateView):
    model = Admision
    template_name = "admisiones/admisiones_tecnicos_form.html"
    form_class = AdmisionForm
    context_object_name = "admision"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(AdmisionService.get_admision_update_context(self.get_object()))
        return context

    def post(self, request, *args, **kwargs):
        admision = self.get_object()
        success, message = AdmisionService.procesar_post_update(request, admision)

        if success is not None:
            if success:
                messages.success(request, message)
            else:
                messages.error(request, message)
            return redirect(self.request.path_info)

        return super().post(request, *args, **kwargs)


class AdmisionDetailView(LoginRequiredMixin, DetailView):
    model = Admision
    template_name = "admisiones/admisiones_detalle.html"
    context_object_name = "admision"

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .select_related(
                "comedor",
                "comedor__provincia",
                "comedor__municipio",
                "comedor__localidad",
                "comedor__dupla",
                "comedor__dupla__abogado",
                "estado",
                "tipo_convenio",
            )
            .prefetch_related("comedor__dupla__tecnico", "historial__usuario")
        )
        return queryset

    def get_object(self, queryset=None):
        admision = super().get_object(queryset)
        comedor_pk = self.kwargs.get("comedor_pk")
        if comedor_pk and admision.comedor_id != comedor_pk:
            raise Http404("La admisiA3n no pertenece al comedor solicitado.")
        return admision

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        admision = self.object
        comedor = admision.comedor

        dupla = getattr(comedor, "dupla", None)
        if dupla:
            tecnicos_dupla = [
                (usuario.get_full_name() or usuario.username or str(usuario))
                for usuario in dupla.tecnico.all()
            ]
        else:
            tecnicos_dupla = []

        admision_context = AdmisionService.get_admision_update_context(admision) or {}

        informes_complementarios_queryset = (
            InformeComplementario.objects.filter(admision=admision)
            .select_related("informe_tecnico", "creado_por")
            .prefetch_related("pdf_final")
        )
        informes_complementarios = list(informes_complementarios_queryset)

        acompanamiento_data = (
            AcompanamientoService.obtener_datos_admision(comedor) if comedor else {}
        )
        prestaciones_detalle = AcompanamientoService.obtener_prestaciones_detalladas(
            acompanamiento_data.get("anexo")
        )

        expedientes_pagos = []
        if comedor:
            expedientes_pagos = list(
                ExpedientesPagosService.obtener_expedientes_pagos(comedor)
            )

        rendiciones_mensuales = []
        if comedor:
            rendiciones_mensuales = list(
                RendicionCuentaMensualService.obtener_rendiciones_cuentas_mensuales(
                    comedor
                )
            )

        rendicion_final = (
            RendicionCuentasFinal.objects.filter(comedor=comedor)
            .prefetch_related("documentos__tipo", "documentos__estado")
            .first()
            if comedor
            else None
        )

        rendicion_final_documentos = []
        rendicion_final_historial = []
        if rendicion_final:
            rendicion_final_documentos = list(
                RendicionCuentasFinalService.get_documentos_rendicion_cuentas_final(
                    rendicion_final
                )
            )
            rendicion_final_historial = list(
                HistorialService.get_historial_documentos_by_rendicion_cuentas_final(
                    rendicion_final
                )
            )

        historial_records = list(
            admision.historial.select_related("usuario").order_by("-fecha")
        )
        historial_page_param = "historial_page"
        historial_page_number = self.request.GET.get(historial_page_param) or 1
        historial_paginator = Paginator(historial_records, 10)
        historial_page = historial_paginator.get_page(historial_page_number)

        historial_headers = [
            {"title": "Fecha"},
            {"title": "Usuario"},
            {"title": "Campo"},
            {"title": "Valor nuevo"},
            {"title": "Valor anterior"},
        ]
        historial_items = []
        for record in historial_page.object_list:
            usuario = record.usuario
            usuario_display = (
                getattr(usuario, "get_full_name", lambda: "")()
                or getattr(usuario, "username", None)
                if usuario
                else "-"
            )
            historial_items.append(
                {
                    "cells": [
                        {
                            "content": (
                                record.fecha.strftime("%d/%m/%Y %H:%M")
                                if record.fecha
                                else "-"
                            )
                        },
                        {"content": usuario_display or "-"},
                        {"content": record.campo or "-"},
                        {"content": record.valor_nuevo or "-"},
                        {"content": record.valor_anterior or "-"},
                    ]
                }
            )

        context.update(
            {
                "comedor": comedor,
                "dupla": dupla,
                "dupla_tecnicos": tecnicos_dupla,
                "dupla_abogado": getattr(dupla, "abogado", None),
                "documentos": admision_context.get("documentos", []),
                "documentos_personalizados": admision_context.get(
                    "documentos_personalizados", []
                ),
                "informe_tecnico": admision_context.get("informe_tecnico"),
                "informe_tecnico_pdf": admision_context.get("pdf"),
                "informes_complementarios": informes_complementarios,
                "acompanamiento_info": acompanamiento_data.get("info_relevante"),
                "acompanamiento_numero_if": acompanamiento_data.get("numero_if"),
                "acompanamiento_numero_disposicion": acompanamiento_data.get(
                    "numero_disposicion"
                ),
                "prestaciones_por_dia": prestaciones_detalle.get(
                    "prestaciones_por_dia", []
                ),
                "prestaciones_dias": prestaciones_detalle.get("prestaciones_dias", []),
                "dias_semana": prestaciones_detalle.get("dias_semana", []),
                "expedientes_pagos": expedientes_pagos,
                "rendiciones_mensuales": rendiciones_mensuales,
                "rendicion_final": rendicion_final,
                "rendicion_final_documentos": rendicion_final_documentos,
                "rendicion_final_historial": rendicion_final_historial,
                "admision_historial_headers": historial_headers,
                "admision_historial_items": historial_items,
                "admision_historial_page_obj": historial_page,
                "admision_historial_is_paginated": historial_page.has_other_pages(),
                "admision_historial_page_param": historial_page_param,
            }
        )

        return context


class AdmisionDetailView(DetailView):
    model = Admision
    template_name = "admisiones/admisiones_detalle.html"
    context_object_name = "admision"

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .select_related(
                "comedor",
                "comedor__provincia",
                "comedor__municipio",
                "comedor__localidad",
                "comedor__dupla",
                "comedor__dupla__abogado",
                "estado",
                "tipo_convenio",
            )
            .prefetch_related("comedor__dupla__tecnico", "historial__usuario")
        )
        return queryset

    def get_object(self, queryset=None):
        admision = super().get_object(queryset)
        comedor_pk = self.kwargs.get("comedor_pk")
        if comedor_pk and admision.comedor_id != comedor_pk:
            raise Http404("La admisiA3n no pertenece al comedor solicitado.")
        return admision

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        admision = self.object
        comedor = admision.comedor

        dupla = getattr(comedor, "dupla", None)
        if dupla:
            tecnicos_dupla = [
                (usuario.get_full_name() or usuario.username or str(usuario))
                for usuario in dupla.tecnico.all()
            ]
        else:
            tecnicos_dupla = []

        admision_context = AdmisionService.get_admision_update_context(admision) or {}

        informes_complementarios_queryset = (
            InformeComplementario.objects.filter(admision=admision)
            .select_related("informe_tecnico", "creado_por")
            .prefetch_related("pdf_final")
        )
        informes_complementarios = list(informes_complementarios_queryset)

        acompanamiento_data = (
            AcompanamientoService.obtener_datos_admision(comedor) if comedor else {}
        )
        prestaciones_detalle = AcompanamientoService.obtener_prestaciones_detalladas(
            acompanamiento_data.get("anexo")
        )

        expedientes_pagos = []
        if comedor:
            expedientes_pagos = list(
                ExpedientesPagosService.obtener_expedientes_pagos(comedor)
            )

        rendiciones_mensuales = []
        if comedor:
            rendiciones_mensuales = list(
                RendicionCuentaMensualService.obtener_rendiciones_cuentas_mensuales(
                    comedor
                )
            )

        rendicion_final = (
            RendicionCuentasFinal.objects.filter(comedor=comedor)
            .prefetch_related("documentos__tipo", "documentos__estado")
            .first()
            if comedor
            else None
        )

        rendicion_final_documentos = []
        rendicion_final_historial = []
        if rendicion_final:
            rendicion_final_documentos = list(
                RendicionCuentasFinalService.get_documentos_rendicion_cuentas_final(
                    rendicion_final
                )
            )
            rendicion_final_historial = list(
                HistorialService.get_historial_documentos_by_rendicion_cuentas_final(
                    rendicion_final
                )
            )

        historial_records = list(
            admision.historial.select_related("usuario").order_by("-fecha")
        )
        historial_page_param = "historial_page"
        historial_page_number = self.request.GET.get(historial_page_param) or 1
        historial_paginator = Paginator(historial_records, 10)
        historial_page = historial_paginator.get_page(historial_page_number)

        historial_headers = [
            {"title": "Fecha"},
            {"title": "Usuario"},
            {"title": "Campo"},
            {"title": "Valor nuevo"},
            {"title": "Valor anterior"},
        ]
        historial_items = []
        for record in historial_page.object_list:
            usuario = record.usuario
            usuario_display = (
                getattr(usuario, "get_full_name", lambda: "")()
                or getattr(usuario, "username", None)
                if usuario
                else "-"
            )
            historial_items.append(
                {
                    "cells": [
                        {
                            "content": (
                                record.fecha.strftime("%d/%m/%Y %H:%M")
                                if record.fecha
                                else "-"
                            )
                        },
                        {"content": usuario_display or "-"},
                        {"content": record.campo or "-"},
                        {"content": record.valor_nuevo or "-"},
                        {"content": record.valor_anterior or "-"},
                    ]
                }
            )

        context.update(
            {
                "comedor": comedor,
                "dupla": dupla,
                "dupla_tecnicos": tecnicos_dupla,
                "dupla_abogado": getattr(dupla, "abogado", None),
                "documentos": admision_context.get("documentos", []),
                "documentos_personalizados": admision_context.get(
                    "documentos_personalizados", []
                ),
                "informe_tecnico": admision_context.get("informe_tecnico"),
                "informe_tecnico_pdf": admision_context.get("pdf"),
                "informes_complementarios": informes_complementarios,
                "acompanamiento_info": acompanamiento_data.get("info_relevante"),
                "acompanamiento_numero_if": acompanamiento_data.get("numero_if"),
                "acompanamiento_numero_disposicion": acompanamiento_data.get(
                    "numero_disposicion"
                ),
                "prestaciones_por_dia": prestaciones_detalle.get(
                    "prestaciones_por_dia", []
                ),
                "prestaciones_dias": prestaciones_detalle.get("prestaciones_dias", []),
                "dias_semana": prestaciones_detalle.get("dias_semana", []),
                "expedientes_pagos": expedientes_pagos,
                "rendiciones_mensuales": rendiciones_mensuales,
                "rendicion_final": rendicion_final,
                "rendicion_final_documentos": rendicion_final_documentos,
                "rendicion_final_historial": rendicion_final_historial,
                "admision_historial_headers": historial_headers,
                "admision_historial_items": historial_items,
                "admision_historial_page_obj": historial_page,
                "admision_historial_is_paginated": historial_page.has_other_pages(),
                "admision_historial_page_param": historial_page_param,
            }
        )

        return context


class InformeTecnicosCreateView(LoginRequiredMixin, CreateView):
    template_name = "admisiones/informe_tecnico_form.html"
    context_object_name = "informe_tecnico"
    tipos_permitidos = {"base", "juridico"}

    def dispatch(self, request, *args, **kwargs):
        self.admision_obj, self.tipo = InformeService.get_admision_y_tipo_from_kwargs(
            self.kwargs
        )
        if not self.admision_obj:
            raise Http404("La admisión indicada no existe.")

        if self.tipo not in self.tipos_permitidos:
            messages.error(
                request,
                "El tipo de informe seleccionado no está disponible para carga online.",
            )
            return HttpResponseRedirect(
                reverse("admisiones_tecnicos_editar", args=[self.admision_obj.id])
            )

        return super().dispatch(request, *args, **kwargs)

    def get_form_class(self):
        return InformeService.get_form_class_por_tipo(self.tipo)

    def get_queryset(self):
        return InformeService.get_queryset_informe_por_tipo(self.tipo)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        action = (
            self.request.POST.get("action") if self.request.method == "POST" else None
        )
        kwargs.update(
            {"admision": self.admision_obj, "require_full": action == "submit"}
        )
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "admision": self.admision_obj,
                "tipo": self.tipo,
                "comedor": getattr(self.admision_obj, "comedor", None),
            }
        )
        return context

    def form_valid(self, form):
        form.instance.tipo = self.tipo
        action = self.request.POST.get("action")

        resultado = InformeService.guardar_informe(
            form, self.admision_obj, es_creacion=True, action=action
        )

        if not resultado.get("success"):
            error_message = resultado.get(
                "error", "No se pudo guardar el informe técnico."
            )
            messages.error(self.request, error_message)
            return self.render_to_response(self.get_context_data(form=form))

        self.object = resultado.get("informe")
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        errores = []
        for field_name, field_errors in form.errors.items():
            if field_name == "__all__":
                errores.extend(field_errors)
                continue
            field = form.fields.get(field_name)
            etiqueta_base = field.label if field and field.label else field_name
            etiqueta = str(etiqueta_base).strip()
            errores.append(f"{etiqueta}: {', '.join(field_errors)}")

        if errores:
            messages.error(
                self.request,
                "No se pudo guardar el informe. Revisá los campos: "
                + " | ".join(errores),
            )
        else:
            messages.error(
                self.request,
                "No se pudo guardar el informe. Verificá que los campos obligatorios estén completos.",
            )
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse("admisiones_tecnicos_editar", args=[self.object.admision.id])


class InformeTecnicosUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "admisiones/informe_tecnico_form.html"
    context_object_name = "informe_tecnico"
    tipos_permitidos = {"base", "juridico"}

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.tipo not in self.tipos_permitidos:
            messages.error(
                request,
                "El tipo de informe seleccionado no está disponible para carga online.",
            )
            return HttpResponseRedirect(
                reverse("admisiones_tecnicos_editar", args=[self.object.admision.id])
            )
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return InformeService.get_queryset_informe_por_tipo(
            InformeService.get_tipo_from_kwargs(self.kwargs)
        )

    def get_form_class(self):
        return InformeService.get_form_class_por_tipo(
            InformeService.get_tipo_from_kwargs(self.kwargs)
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        action = (
            self.request.POST.get("action") if self.request.method == "POST" else None
        )
        kwargs.update(
            {"admision": self.object.admision, "require_full": action == "submit"}
        )
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tipo = InformeService.get_tipo_from_kwargs(self.kwargs)
        context.update(InformeService.get_informe_update_context(self.object, tipo))
        return context

    def form_valid(self, form):
        resultado = InformeService.guardar_informe(
            form,
            form.instance.admision,
            es_creacion=False,
            action=self.request.POST.get("action"),
        )

        if not resultado.get("success"):
            error_message = resultado.get(
                "error", "No se pudo guardar el informe técnico."
            )
            messages.error(self.request, error_message)
            return self.render_to_response(self.get_context_data(form=form))

        self.object = resultado.get("informe")
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        errores = []
        for field_name, field_errors in form.errors.items():
            if field_name == "__all__":
                errores.extend(field_errors)
                continue
            field = form.fields.get(field_name)
            etiqueta_base = field.label if field and field.label else field_name
            etiqueta = str(etiqueta_base).strip()
            errores.append(f"{etiqueta}: {', '.join(field_errors)}")

        if errores:
            messages.error(
                self.request,
                "No se pudo guardar el informe. Revisá los campos: "
                + " | ".join(errores),
            )
        else:
            messages.error(
                self.request,
                "No se pudo guardar el informe. Verificá que los campos obligatorios estén completos.",
            )
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse("admisiones_tecnicos_editar", args=[self.object.admision.id])


class InformeTecnicoDetailView(LoginRequiredMixin, DetailView):
    template_name = "admisiones/informe_tecnico_detalle.html"
    context_object_name = "informe_tecnico"

    def get_queryset(self):
        return InformeService.get_queryset_informe_por_tipo(
            self.kwargs.get("tipo", "base")
        )

    def post(self, request, *args, **kwargs):
        tipo = self.kwargs.get("tipo", "base")
        informe = InformeService.get_informe_por_tipo_y_pk(tipo, kwargs["pk"])
        InformeService.procesar_revision_informe(request, tipo, informe)
        return HttpResponseRedirect(
            reverse("admisiones_tecnicos_editar", args=[informe.admision.id])
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            InformeService.get_context_informe_detail(
                self.object, self.kwargs.get("tipo", "base")
            )
        )
        return context


class AdmisionesLegalesListView(LoginRequiredMixin, ListView):
    model = Admision
    template_name = "admisiones/admisiones_legales_list.html"
    context_object_name = "admisiones"
    paginate_by = 10

    def get_queryset(self):
        return LegalesService.get_admisiones_legales_filtradas(
            self.request.GET.get("busqueda", "")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "query": self.request.GET.get("busqueda", ""),
                "breadcrumb_items": [
                    {"name": "Expedientes", "url": "admisiones_legales_listar"},
                    {"name": "Listar", "active": True},
                ],
            }
        )
        return context


class AdmisionesLegalesDetailView(LoginRequiredMixin, FormMixin, DetailView):
    model = Admision
    template_name = "admisiones/admisiones_legales_detalle.html"
    context_object_name = "admision"
    form_class = LegalesRectificarForm

    def get_success_url(self):
        return reverse("admisiones_legales_ver", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            LegalesService.get_legales_context(self.get_object(), self.request)
        )
        context.setdefault("form", self.get_form())
        context.setdefault(
            "form_legales_num_if", LegalesNumIFForm(instance=self.get_object())
        )
        return context

    def post(self, request, *args, **kwargs):
        return LegalesService.procesar_post_legales(request, self.get_object())


class InformeTecnicoComplementarioReviewView(LoginRequiredMixin, DetailView):
    model = Admision
    template_name = "admisiones/revisar_informe_complementario.html"
    context_object_name = "admision"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from admisiones.models.admisiones import (
            InformeComplementario,
            InformeComplementarioCampos,
        )

        informe_complementario = InformeComplementario.objects.filter(
            admision=self.object, estado="enviado_validacion"
        ).first()

        if informe_complementario:
            context.update(
                {
                    "informe_complementario": informe_complementario,
                    "campos_modificados": InformeComplementarioCampos.objects.filter(
                        informe_complementario=informe_complementario
                    ),
                }
            )

        return context

    def post(self, request, *args, **kwargs):
        return LegalesService.revisar_informe_complementario(request, self.get_object())


class InformeTecnicoComplementarioDetailView(LoginRequiredMixin, DetailView):
    template_name = "admisiones/informe_tecnico_complementario_detalle.html"
    context_object_name = "informe_tecnico"

    def get_queryset(self):
        tipo = self.kwargs.get("tipo", "base")
        return InformeService.get_queryset_informe_por_tipo(tipo)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        campos_modificados = {
            key.replace("campo_", ""): value.strip()
            for key, value in request.POST.items()
            if key.startswith("campo_") and value.strip()
        }

        if not campos_modificados:
            messages.error(request, "No se han realizado cambios en el informe.")
            return HttpResponseRedirect(request.path_info)

        informe_complementario = InformeService.guardar_campos_complementarios(
            informe_tecnico=self.object,
            campos_dict=campos_modificados,
            usuario=request.user,
        )

        if not informe_complementario:
            messages.error(
                request, "Error al guardar los cambios del informe complementario."
            )
            return HttpResponseRedirect(request.path_info)

        informe_complementario.estado = "enviado_validacion"
        informe_complementario.save()

        from admisiones.services.legales_service import LegalesService

        LegalesService.actualizar_estado_por_accion(
            self.object.admision, "enviar_informe_complementario"
        )

        messages.success(request, "Informe complementario enviado para validación.")
        return HttpResponseRedirect(
            reverse("admisiones_tecnicos_editar", args=[self.object.admision.id])
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tipo = self.kwargs.get("tipo", "base")
        context.update(InformeService.get_context_informe_detail(self.object, tipo))

        from admisiones.models.admisiones import (
            InformeComplementario,
            InformeComplementarioCampos,
        )

        informe_complementario = InformeComplementario.objects.filter(
            admision=self.object.admision, estado__in=["borrador", "rectificar"]
        ).first()

        if informe_complementario:
            campos_modificados = InformeComplementarioCampos.objects.filter(
                informe_complementario=informe_complementario
            )
            context.update(
                {
                    "campos_modificados_existentes": {
                        campo.campo: campo.value for campo in campos_modificados
                    },
                    "observaciones_legales": informe_complementario.observaciones_legales,
                }
            )

        return context


def admisiones_legales_ajax(request):
    """Endpoint AJAX para búsqueda filtrada de admisiones legales"""
    from django.template.loader import render_to_string
    from django.core.paginator import Paginator
    from core.decorators import group_required

    @group_required(["Abogado Dupla"])
    def _ajax_handler(request):
        query = request.GET.get("busqueda", "")
        page = request.GET.get("page", 1)

        admisiones = LegalesService.get_admisiones_legales_filtradas(query)
        paginator = Paginator(admisiones, 10)
        page_obj = paginator.get_page(page)

        html = render_to_string(
            "partials/admisiones_legales_rows.html",
            {"admisiones": page_obj, "request": request},
            request=request,
        )
        pagination_html = render_to_string(
            "components/pagination.html",
            {"page_obj": page_obj, "is_paginated": page_obj.has_other_pages()},
            request=request,
        )

        return JsonResponse(
            {
                "html": html,
                "pagination_html": pagination_html,
                "count": paginator.count,
                "num_pages": paginator.num_pages,
                "has_previous": page_obj.has_previous(),
                "has_next": page_obj.has_next(),
                "current_page": page_obj.number,
            }
        )

    return _ajax_handler(request)
