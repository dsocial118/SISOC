# centrodefamilia/views/informecabal.py

from django.db.models import F
import logging
from django.views import View
from django.views.generic import ListView, DetailView, TemplateView
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404, render
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from core.decorators import group_required
from centrodefamilia.services.informe_cabal_reprocess import (
    ReprocessError,
    reprocesar_registros_rechazados_por_codigo,
)

from centrodefamilia.models import CabalArchivo, Centro, InformeCabalRegistro
from centrodefamilia.services.informe_cabal_service import (
    read_excel_preview,
    persist_file_and_rows,
)

logger = logging.getLogger(__name__)


@method_decorator(ensure_csrf_cookie, name="dispatch")
class InformeCabalListView(LoginRequiredMixin, TemplateView):
    template_name = "informecabal/list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        archivos = CabalArchivo.objects.select_related("usuario").order_by(
            "-fecha_subida"
        )
        ctx["archivos"] = Paginator(archivos, 10).get_page(self.request.GET.get("page"))
        return ctx


@method_decorator(csrf_protect, name="dispatch")
class InformeCabalPreviewAjaxView(LoginRequiredMixin, TemplateView):

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
                }
                for r in rows
            ]
            return JsonResponse(
                {"ok": True, "rows": data, "not_matching": not_matching, "total": total}
            )
        except ValueError as ve:
            logger.warning("ValueError en preview CABAL: %s", ve, exc_info=True)
            return JsonResponse(
                {
                    "ok": False,
                    "error": "El archivo no tiene el formato esperado o está dañado.",
                },
                status=400,
            )
        except Exception as e:
            logger.exception("Error en preview CABAL: %s", e, exc_info=True)
            return JsonResponse(
                {"ok": False, "error": "Error inesperado al previsualizar."}, status=500
            )


@method_decorator(csrf_protect, name="dispatch")
class InformeCabalProcessAjaxView(LoginRequiredMixin, TemplateView):

    def post(self, request, *args, **kwargs):
        f = request.FILES.get("file")
        force = request.POST.get("force", "false") == "true"
        if not f:
            return HttpResponseBadRequest("No se envió archivo.")
        try:
            archivo, total, validas, not_matching = persist_file_and_rows(
                f, request.user, force_proceed=force
            )
            messages.success(request, "Informe CABAL procesado correctamente.")
            return JsonResponse(
                {
                    "ok": True,
                    "archivo_id": archivo.id,
                    "total": total,
                    "validas": validas,
                    "invalidas": total - validas,
                    "not_matching": not_matching,
                }
            )
        except FileExistsError as dup:
            if str(dup) == "DUPLICATE_NAME":
                return JsonResponse({"ok": False, "duplicate_name": True}, status=409)
            return JsonResponse(
                {"ok": False, "error": "Archivo duplicado."}, status=409
            )
        except ValueError as ve:
            # Entrada inválida (formato de Excel, headers, etc.)
            logger.warning(
                "ValueError al procesar CABAL (process): %s", ve, exc_info=True
            )
            return JsonResponse(
                {
                    "ok": False,
                    "error": "El archivo no tiene el formato esperado o está dañado.",
                },
                status=400,
            )
        except Exception as e:
            logger.exception("Error inesperado al procesar CABAL: %s", e, exc_info=True)
            return JsonResponse(
                {"ok": False, "error": "Error inesperado al procesar."}, status=500
            )


class InformeCabalRegistroDetailView(LoginRequiredMixin, DetailView):
    model = CabalArchivo
    template_name = "informecabal/registro_detail.html"
    context_object_name = "archivo"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        registros = InformeCabalRegistro.objects.filter(archivo=self.object)

        ctx["total"] = registros.count()
        return ctx


class InformeCabalArchivoDetailView(LoginRequiredMixin, DetailView):
    model = CabalArchivo
    template_name = "informecabal/archivo_detail.html"
    context_object_name = "archivo"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["registros"] = InformeCabalRegistro.objects.filter(
            archivo=self.object
        ).order_by("id")
        return ctx


@method_decorator(csrf_protect, name="dispatch")
class InformeCabalReprocessCenterAjaxView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        codigo = (request.POST.get("codigo") or "").strip()
        if not codigo:
            return JsonResponse(
                {"ok": False, "error": "Falta código de centro"}, status=400
            )
        try:
            res = reprocesar_registros_rechazados_por_codigo(
                codigo=codigo, dry_run=False
            )
            return JsonResponse({"ok": True, **res})
        except ReprocessError as e:
            logger.warning(
                "ReprocessError al reprocesar CABAL (codigo=%s): %s",
                codigo,
                e,
                exc_info=True,
            )
            return JsonResponse(
                {
                    "ok": False,
                    "error": "No se pudo reprocesar el centro. Revise los datos e intente nuevamente.",
                },
                status=400,
            )

        except Exception as e:
            logger.exception(
                "Error inesperado al reprocesar CABAL (codigo=%s): %s",
                codigo,
                e,
                exc_info=True,
            )
            return JsonResponse(
                {"ok": False, "error": "Error inesperado al reprocesar el centro."},
                status=500,
            )
