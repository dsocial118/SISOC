# views/expediente.py
import json
import logging
import time
import traceback

from django.views import View
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from celiaquia.forms import ExpedienteForm, ConfirmarEnvioForm
from celiaquia.models import EstadoLegajo, Expediente, ExpedienteCiudadano
from celiaquia.services.ciudadano_service import CiudadanoService
from celiaquia.services.expediente_service import ExpedienteService
from celiaquia.services.importacion_service import ImportacionService

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class ProcesarExpedienteView(View):
    """
    POST AJAX: crea/enlaza legajos desde el Excel y cambia estado a 'PROCESADO'.
    Devuelve JSON {'success', 'creados', 'errores'}.
    """

    def post(self, request, pk):
        expediente = get_object_or_404(
            Expediente, pk=pk, usuario_provincia=request.user
        )
        try:
            result = ExpedienteService.procesar_expediente(expediente)
            return JsonResponse(
                {
                    "success": True,
                    "creados": result["creados"],
                    "errores": result["errores"],
                }
            )
        except ValidationError as ve:
            return JsonResponse({"success": False, "error": ve.message}, status=400)
        except Exception:
            tb = traceback.format_exc()
            logger.error("Error al procesar expediente %s:\n%s", pk, tb)
            return JsonResponse(
                {"success": False, "error": "Error inesperado al procesar."}, status=500
            )


class CrearLegajosView(View):
    """
    POST AJAX: crea/enlaza legajos a partir de JSON 'rows'.
    Devuelve JSON {'creados', 'existentes'}.
    """

    def post(self, request, pk):
        expediente = get_object_or_404(
            Expediente, pk=pk, usuario_provincia=request.user
        )
        try:
            payload = json.loads(request.body)
            rows = payload.get("rows", [])
        except json.JSONDecodeError:
            return HttpResponseBadRequest("JSON inválido.")

        estado_inicial = EstadoLegajo.objects.get(nombre="DOCUMENTO_PENDIENTE")
        creados = existentes = 0
        for datos in rows:
            ciudadano = CiudadanoService.get_or_create_ciudadano(datos)
            obj, was_created = ExpedienteCiudadano.objects.get_or_create(
                expediente=expediente,
                ciudadano=ciudadano,
                defaults={"estado": estado_inicial},
            )
            if was_created:
                creados += 1
            else:
                existentes += 1
        return JsonResponse({"creados": creados, "existentes": existentes})


@method_decorator(csrf_exempt, name="dispatch")
class ExpedientePreviewExcelView(View):
    """
    POST AJAX exento CSRF: recibe Excel y devuelve JSON con preview {headers, rows}.
    """

    def post(self, request, *args, **kwargs):
        logger.debug("PREVIEW: %s %s", request.method, request.path)
        archivo = request.FILES.get("excel_masivo")
        if not archivo:
            return JsonResponse({"error": "No se recibió ningún archivo."}, status=400)
        try:
            preview = ImportacionService.preview_excel(archivo)
            return JsonResponse(preview)
        except ValidationError as e:
            return JsonResponse({"error": str(e)}, status=400)
        except Exception:
            tb = traceback.format_exc()
            logger.error("PREVIEW error:\n%s", tb)
            return JsonResponse({"error": "Error inesperado al procesar."}, status=500)


class ExpedienteListView(ListView):
    model = Expediente
    template_name = "celiaquia/expediente_list.html"
    context_object_name = "expedientes"
    paginate_by = 20

    def get_queryset(self):
        return (
            Expediente.objects.filter(usuario_provincia=self.request.user)
            .select_related("estado")
            .only("id", "codigo", "fecha_creacion", "estado__nombre")
        )


class ExpedienteCreateView(CreateView):
    model = Expediente
    form_class = ExpedienteForm
    template_name = "celiaquia/expediente_form.html"

    def form_valid(self, form):
        expediente = ExpedienteService.create_expediente(
            usuario_provincia=self.request.user,
            datos_metadatos=form.cleaned_data,
            excel_masivo=form.cleaned_data["excel_masivo"],
        )
        messages.success(self.request, "Expediente creado correctamente.")
        return redirect("expediente_detail", pk=expediente.pk)


class ExpedienteDetailView(DetailView):
    model = Expediente
    template_name = "celiaquia/expediente_detail.html"
    context_object_name = "expediente"

    def get_queryset(self):
        return (
            Expediente.objects.filter(usuario_provincia=self.request.user)
            .select_related("estado", "usuario_modificador")
            .prefetch_related(
                "expediente_ciudadanos__ciudadano", "expediente_ciudadanos__estado"
            )
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        expediente = self.object
        preview = preview_error = None
        if expediente.estado.nombre == "CREADO" and expediente.excel_masivo:
            try:
                preview = ImportacionService.preview_excel(expediente.excel_masivo)
            except Exception as e:
                preview_error = str(e)
        ctx.update(
            {
                "legajos": expediente.expediente_ciudadanos.all(),
                "confirm_form": ConfirmarEnvioForm(),
                "preview": preview,
                "preview_error": preview_error,
            }
        )
        return ctx


class ExpedienteImportView(View):
    """Procesa la importación masiva de legajos desde el Excel guardado."""

    def post(self, request, pk):
        expediente = get_object_or_404(
            Expediente, pk=pk, usuario_provincia=request.user
        )
        start = time.time()
        try:
            result = ImportacionService.importar_legajos_desde_excel(
                expediente, expediente.excel_masivo
            )
            elapsed = time.time() - start
            messages.success(
                request,
                f"Importación: {result['validos']} válidos, {result['errores']} errores en {elapsed:.2f}s.",
            )
        except ValidationError as ve:
            messages.error(request, f"Error de validación: {ve.message}")
        except Exception as e:
            messages.error(request, f"Error inesperado: {e}")
        return redirect("expediente_detail", pk=pk)


class ExpedienteConfirmView(View):
    def post(self, request, pk):
        expediente = get_object_or_404(
            Expediente, pk=pk, usuario_provincia=request.user
        )
        try:
            result = ExpedienteService.confirmar_envio(expediente)
            messages.success(
                request,
                f"Expediente enviado: {result['validos']} legajos creados, {result['errores']} errores.",
            )
        except ValidationError as ve:
            messages.error(request, f"Error al confirmar: {ve.message}")
        except Exception as e:
            messages.error(request, f"Error inesperado: {e}")
        return redirect("expediente_detail", pk=pk)


class ExpedienteUpdateView(UpdateView):
    model = Expediente
    form_class = ExpedienteForm
    template_name = "celiaquia/expediente_form.html"

    def get_success_url(self):
        return reverse_lazy("expediente_detail", args=[self.object.pk])


class AsignarTecnicoView(View):
    def post(self, request, pk):
        expediente = get_object_or_404(Expediente, pk=pk)
        tecnico_id = request.POST.get("tecnico")
        ExpedienteService.asignar_tecnico(expediente, tecnico_id)
        messages.success(request, "Técnico asignado correctamente.")
        return redirect("expediente_detail", pk=pk)


class ClosePaymentView(View):
    def post(self, request, pk):
        expediente = get_object_or_404(Expediente, pk=pk)
        # lógic ade pago…
        return redirect("expediente_detail", pk=pk)
