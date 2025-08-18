from django.contrib import messages
from django.db.models.base import Model
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import DetailView, ListView
from django.views.decorators.http import require_POST

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


@require_POST
def switch_rendicion_final_fisicamente_presentrendicionada(request, rendicion_id):
    rendicion_final = get_object_or_404(RendicionCuentasFinal, id=rendicion_id)
    rendicion_final.fisicamente_presentada = not rendicion_final.fisicamente_presentada
    rendicion_final.save()

    messages.success(request, "Estado de revisión actualizado.")

    return redirect(request.META.get("HTTP_REFERER", "/"))


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

    return redirect(request.META.get("HTTP_REFERER", "/"))


class DocumentosRendicionCuentasFinalListView(ListView):
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
    if next_url:
        return redirect(next_url)
    return redirect(request.META.get("HTTP_REFERER", "/"))


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

    return redirect(request.META.get("HTTP_REFERER", "/"))


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

    return redirect(request.META.get("HTTP_REFERER", "/"))


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

    return redirect(request.META.get("HTTP_REFERER", "/"))


class RendicionCuentasFinalDetailView(DetailView):
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


@require_POST
def switch_rendicion_final_fisicamente_presentada(request, rendicion_id):
    rendicion_final = get_object_or_404(RendicionCuentasFinal, id=rendicion_id)
    rendicion_final.fisicamente_presentada = not rendicion_final.fisicamente_presentada
    rendicion_final.save()

    messages.success(request, "Estado de revisión actualizado.")

    return redirect(request.META.get("HTTP_REFERER", "/"))
