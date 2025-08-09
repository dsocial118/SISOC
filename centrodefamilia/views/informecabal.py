# centrodefamilia/views/informecabal.py
"""
[Informe Cabal - Views]
- Lista de historial (solo CDF SSE por URL).
- Endpoints AJAX: preview (paginado 25) y process (persistencia completa).
- Detail de un registro.
Mensajería: usa messages y JSON con errores controlados. 
"""
import logging
from django.views import View
from django.views.generic import ListView, DetailView, TemplateView
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404, render
from django.contrib import messages

from centrodefamilia.models import CabalArchivo, Centro, InformeCabalRegistro
from centrodefamilia.services.informe_cabal_reprocess import reprocesar_registros_rechazados
from centrodefamilia.services.informe_cabal_service import (
    read_excel_preview,
    persist_file_and_rows,
)

logger = logging.getLogger(__name__)

class InformeCabalListView(LoginRequiredMixin, TemplateView):
    template_name = "informecabal/list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        archivos = CabalArchivo.objects.select_related("usuario").order_by("-fecha_subida")
        ctx["archivos"] = Paginator(archivos, 10).get_page(self.request.GET.get("page"))
        return ctx

@method_decorator(csrf_exempt, name="dispatch")
class InformeCabalPreviewAjaxView(LoginRequiredMixin, TemplateView):
    """
    POST con 'file' y 'page' para previsualizar 25 filas.
    Retorna JSON: rows, not_matching, total
    """
    def post(self, request, *args, **kwargs):
        f = request.FILES.get("file")
        page = int(request.POST.get("page", 1))
        if not f:
            return HttpResponseBadRequest("No se envió archivo.")
        try:
            rows, not_matching, total = read_excel_preview(f, page=page, per_page=25)
            data = [
                {
                    "fila": r.fila,
                    "no_coincidente": r.no_coincidente,
                    "data": r.data,
                } for r in rows
            ]
            return JsonResponse({"ok": True, "rows": data, "not_matching": not_matching, "total": total})
        except ValueError as ve:
            return JsonResponse({"ok": False, "error": str(ve)}, status=400)
        except Exception as e:
            logger.error("Error en preview CABAL: %s", e, exc_info=True)
            return JsonResponse({"ok": False, "error": "Error inesperado al previsualizar."}, status=500)

@method_decorator(csrf_exempt, name="dispatch")
class InformeCabalProcessAjaxView(LoginRequiredMixin, TemplateView):
    """
    POST con 'file' y 'force' (opcional) para persistir.
    - Si nombre duplicado y no 'force', devuelve {duplicate_name: True}
    """
    def post(self, request, *args, **kwargs):
        f = request.FILES.get("file")
        force = request.POST.get("force", "false") == "true"
        if not f:
            return HttpResponseBadRequest("No se envió archivo.")
        try:
            archivo, total, validas, not_matching = persist_file_and_rows(f, request.user, force_proceed=force)
            messages.success(request, "Informe CABAL procesado correctamente.")
            return JsonResponse({
                "ok": True,
                "archivo_id": archivo.id,
                "total": total,
                "validas": validas,
                "invalidas": total - validas,
                "not_matching": not_matching
            })
        except FileExistsError as dup:
            if str(dup) == "DUPLICATE_NAME":
                return JsonResponse({"ok": False, "duplicate_name": True}, status=409)
            return JsonResponse({"ok": False, "error": "Archivo duplicado."}, status=409)
        except ValueError as ve:
            return JsonResponse({"ok": False, "error": str(ve)}, status=400)
        except Exception as e:
            logger.error("Error al procesar CABAL: %s", e, exc_info=True)
            return JsonResponse({"ok": False, "error": "Error inesperado al procesar."}, status=500)

class InformeCabalRegistroDetailView(LoginRequiredMixin, DetailView):
    model = CabalArchivo
    template_name = "informecabal/registro_detail.html"
    context_object_name = "archivo"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        registros = InformeCabalRegistro.objects.filter(archivo=self.object)

        ctx["validos"] = registros.filter(estado="Impactado")
        ctx["rechazados"] = registros.filter(estado="Rechazado")
        ctx["creados"] = registros.filter(estado="Creado")
        ctx["total"] = registros.count()
        return ctx


class InformeCabalArchivoDetailView(LoginRequiredMixin, DetailView):
    model = CabalArchivo
    template_name = "informecabal/archivo_detail.html"
    context_object_name = "archivo"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["registros"] = InformeCabalRegistro.objects.filter(archivo=self.object).order_by("id")
        return ctx

@method_decorator(csrf_exempt, name="dispatch")
class InformeCabalReprocessCenterAjaxView(LoginRequiredMixin, View):
    """
    POST: codigo (centro.codigo) y optional only_pago_rechazado ('1'/'0')
    Ejecuta el reproceso para ese centro.
    """
    def post(self, request, *args, **kwargs):
        codigo = (request.POST.get("codigo") or "").strip()
        only_rej = request.POST.get("only_pago_rechazado") == "1"
        if not codigo:
            return JsonResponse({"ok": False, "error": "Falta el código."}, status=400)
        # buscar centro por código (case-insensitive)
        try:
            centro = Centro.objects.get(codigo__iexact=codigo)
        except Centro.DoesNotExist:
            return JsonResponse({"ok": False, "error": "No existe un centro con ese código."}, status=404)
        try:
            res = reprocesar_registros_rechazados(
                centro_id=centro.id,
                only_pago_rechazado=only_rej,
                dry_run=False,   # commit
            )
            return JsonResponse(res)
        except Exception as e:
            logger.exception("Error reprocesando centro %s", centro.id)
            return JsonResponse({"ok": False, "error": "Error inesperado en el reproceso."}, status=500)