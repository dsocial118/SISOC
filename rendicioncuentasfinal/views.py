from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models.base import Model
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_stringW
from django.utils import timezone
from django.views.generic import DetailView, ListView
from django.views.decorators.http import require_POST

from core.decorators import group_required
from core.security import safe_redirect

from comedores.models import Comedor
from historial.services.historial_service import HistorialService

from rendicioncuentasfinal.models import (
    DocumentoRendicionFinal,
    EstadoDocumentoRendicionFinal,
    RendicionCuentasFinal,
)
from rendicioncuentasfinal.rendicion_cuentas_final_service import (
    RendicionCuentasFinalService,
)


@login_required
@require_POST
def subsanar_documento_rendicion_cuentas_final(request, documento_id):
    documento = get_object_or_404(DocumentoRendicionFinal, id=documento_id)

    documento.observaciones = request.POST.get("observacion", "")
    documento.estado = EstadoDocumentoRendicionFinal.objects.get(nombre="Subsanar")
    documento.fecha_modificacion = timezone.now()
    documento.save()

    HistorialService.registrar_historial(
        accion="Enviar a subsanar documento",
        instancia=documento,
    )

    messages.success(request, "Documento enviado a subsanar correctamente.")

    return safe_redirect(
        request,
        default="rendicion_cuentas_final_listar",
        target=request.META.get("HTTP_REFERER"),
    )


class DocumentosRendicionCuentasFinalListView(LoginRequiredMixin, ListView):
    model = DocumentoRendicionFinal
    template_name = "comedor/rendicion_cuentas_final_list.html"
    context_object_name = "documentos"

    def get_queryset(self):
        user = self.request.user
        query = self.request.GET.get("busqueda")

        qs = RendicionCuentasFinalService.filter_documentos_por_area(user, query)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Agregar contexto para el search_bar.html
        context["query"] = self.request.GET.get("busqueda", "")
        context["reset_url"] = "rendicion_cuentas_final_listar"

        return context


@login_required
@require_POST
def validar_documento_rendicion_cuentas_final(request, documento_id):
    documento = get_object_or_404(DocumentoRendicionFinal, id=documento_id)
    documento.estado = EstadoDocumentoRendicionFinal.objects.get(nombre="Validado")
    documento.fecha_modificacion = timezone.now()
    documento.save()

    HistorialService.registrar_historial(
        accion="Validar documento",
        instancia=documento,
    )

    messages.success(request, "Documento validado correctamente.")

    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER")
    return safe_redirect(
        request,
        default="rendicion_cuentas_final_listar",
        target=next_url,
    )


@login_required
@require_POST
def eliminar_documento_rendicion_cuentas_final(request, documento_id):
    documento = get_object_or_404(DocumentoRendicionFinal, id=documento_id)

    if documento.documento:
        documento.documento.delete(save=False)

    estado_no_presentado = EstadoDocumentoRendicionFinal.objects.get(
        nombre="No presentado"
    )
    documento.estado = estado_no_presentado
    documento.fecha_modificacion = timezone.now()
    documento.save()

    HistorialService.registrar_historial(
        accion="Documento eliminado",
        instancia=documento,
    )

    messages.success(request, "Documento eliminado correctamente.")

    return safe_redirect(
        request,
        default="rendicion_cuentas_final_listar",
        target=request.META.get("HTTP_REFERER"),
    )


@login_required
@require_POST
def crear_documento_rendicion_cuentas_final(request, rendicion_id):
    rendicion = get_object_or_404(RendicionCuentasFinal, id=rendicion_id)
    nombre = request.POST.get("nombre", "").strip()
    archivo = request.FILES.get("archivo")

    documento = rendicion.add_documento_personalizado(nombre)

    if archivo:
        HistorialService.registrar_historial(
            accion="Crear documento personalizado",
            instancia=documento,
        )

        RendicionCuentasFinalService.actualizar_documento_con_archivo(
            documento, archivo
        )

    return safe_redirect(
        request,
        default="rendicion_cuentas_final_listar",
        target=request.META.get("HTTP_REFERER"),
    )


@login_required
@require_POST
def adjuntar_documento_rendicion_cuenta_final(request):
    doc_id = request.POST.get("documento_id")
    archivo = request.FILES.get("archivo")

    ok, _documento = RendicionCuentasFinalService.adjuntar_archivo_a_documento(
        doc_id, archivo
    )

    if not ok:
        messages.error(request, "No se seleccionó ningún archivo.")
    else:
        messages.success(request, "Archivo adjuntado correctamente.")

    return safe_redirect(
        request,
        default="rendicion_cuentas_final_listar",
        target=request.META.get("HTTP_REFERER"),
    )


class RendicionCuentasFinalDetailView(LoginRequiredMixin, DetailView):
    model = RendicionCuentasFinal
    context_object_name = "rendicion"
    template_name = "comedor/rendicion_cuentas_final_detail.html"

    def get_object(self, queryset=None) -> Model:
        comedor = get_object_or_404(
            Comedor.objects.only("id", "nombre"),  # Trae solo lo que vas a usar
            pk=self.kwargs["pk"],
        )
        rendicion, _ = RendicionCuentasFinal.objects.select_related(
            "comedor"
        ).get_or_create(comedor=comedor)

        return rendicion

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rendicion = self.object

        context["documentos"] = (
            RendicionCuentasFinalService.get_documentos_rendicion_cuentas_final(
                rendicion
            )
        )

        context["historial"] = (
            HistorialService.get_historial_documentos_by_rendicion_cuentas_final(
                rendicion
            )
        )

        context["comedor_id"] = rendicion.comedor.id
        context["comedor_nombre"] = rendicion.comedor.nombre
        context["fisicamente_presentada"] = rendicion.fisicamente_presentada

        return context


@login_required
@require_POST
def switch_rendicion_final_fisicamente_presentada(request, rendicion_id):
    rendicion_final = get_object_or_404(RendicionCuentasFinal, id=rendicion_id)
    rendicion_final.fisicamente_presentada = not rendicion_final.fisicamente_presentada
    rendicion_final.save()

    messages.success(request, "Estado de revisión actualizado.")

    return safe_redirect(
        request,
        default="rendicion_cuentas_final_listar",
        target=request.META.get("HTTP_REFERER"),
    )


def documentos_rendicion_cuentas_final_ajax(request):
    """Endpoint AJAX para búsqueda filtrada de documentos de rendición de cuentas final"""

    # Aplicar el decorador manualmente para mantener permisos
    @group_required(
        [
            "Area Contable",
            "Area Legales",
            "Tecnico Comedor",
            "Coordinador Equipo Tecnico",
        ]
    )
    def _documentos_rendicion_ajax(request):
        query = request.GET.get("busqueda", "")
        page = request.GET.get("page", 1)

        # Obtener documentos filtrados usando el mismo servicio que la vista principal
        documentos = RendicionCuentasFinalService.filter_documentos_por_area(
            request.user, query
        )

        # Paginación - usar la misma paginación que la vista principal
        paginator = Paginator(documentos, 25)  # Usar paginación por defecto de ListView
        page_obj = paginator.get_page(page)

        # Renderizar las filas de la tabla
        html = render_to_string(
            "partials/rendicion_cuentas_final_rows.html",
            {"documentos": page_obj, "request": request},
        )

        # Renderizar paginación
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

    return _documentos_rendicion_ajax(request)
