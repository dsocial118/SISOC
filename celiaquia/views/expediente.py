"""
celiaquia/views/expediente.py

Breve descripción del cambio:
- Centraliza ExpedienteListView para que una única lista sirva a Provincia, Subsecretaría (Coordinador) y Técnico.
- Provincia: ve sólo sus expedientes.
- CoordinadorCeliaquia: ve CONFIRMACION_DE_ENVIO, RECEPCIONADO y ASIGNADO (bandeja completa).
- TecnicoCeliaquia: ve los expedientes donde es técnico asignado (ASIGNADO, y futuros estados técnicos).

Estados y flujos impactados:
- Provincia: CREADO -> PROCESADO -> EN_ESPERA -> CONFIRMACION_DE_ENVIO (sin cambios)
- Subsecretaría:
    * Recepcionar: CONFIRMACION_DE_ENVIO -> RECEPCIONADO
    * Asignar técnico: RECEPCIONADO -> ASIGNADO (o cambiar técnico manteniendo ASIGNADO)

Dependencias con otros archivos:
- templates/celiaquia/expediente_list.html (acciones por rol/estado; badges para RECEPCIONADO)
- static/custom/js/celiaquia_list.js (handlers para recepcionar/asignar)
- services/* para acciones puntuales (procesar, confirmar)
"""

import json
import logging
import time
import traceback

from django.views import View
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.contrib import messages
from django.core.exceptions import ValidationError, PermissionDenied
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.models import User

from celiaquia.forms import ExpedienteForm, ConfirmarEnvioForm
from celiaquia.models import (
    AsignacionTecnico,
    EstadoLegajo,
    EstadoExpediente,
    Expediente,
    ExpedienteCiudadano,
)
from celiaquia.services.ciudadano_service import CiudadanoService
from celiaquia.services.expediente_service import ExpedienteService
from celiaquia.services.importacion_service import ImportacionService

logger = logging.getLogger(__name__)


# ===== utilidades de permiso locales =====
def _user_in_group(user, group_name: str) -> bool:
    return user.is_authenticated and user.groups.filter(name=group_name).exists()


class ExpedienteListView(ListView):
    """
    Descripción:
      - Única lista para todos los roles.
        * ProvinciaCeliaquia: lista sólo sus expedientes.
        * CoordinadorCeliaquia: lista expedientes en CONFIRMACION_DE_ENVIO, RECEPCIONADO o ASIGNADO.
        * TecnicoCeliaquia: lista expedientes donde es técnico asignado.
      - Orden descendente por fecha_creacion.

    Nota: el template consume 'expedientes' y, para Coordinador, 'tecnicos'.
    """

    model = Expediente
    template_name = "celiaquia/expediente_list.html"
    context_object_name = "expedientes"
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user

        # Base con joins necesarios para no pegar en N+1 cuando mostremos técnico/estado
        qs = (
            Expediente.objects
            .select_related("estado", "asignacion_tecnico__tecnico")
            .only(
                "id",
                "codigo",
                "fecha_creacion",
                "estado__nombre",
                "usuario_provincia_id",
                "asignacion_tecnico__tecnico_id",
            )
        )

        # Coordinador: bandeja de entrada y seguimiento
        if _user_in_group(user, "CoordinadorCeliaquia"):
            return qs.filter(
                estado__nombre__in=["CONFIRMACION_DE_ENVIO", "RECEPCIONADO", "ASIGNADO"]
            ).order_by("-fecha_creacion")

        # Técnico: sus expedientes asignados (incluye distintos estados del ciclo técnico)
        if _user_in_group(user, "TecnicoCeliaquia"):
            return qs.filter(asignacion_tecnico__tecnico=user).order_by("-fecha_creacion")

        # Provincia (default): sólo los suyos
        return qs.filter(usuario_provincia=user).order_by("-fecha_creacion")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        # Para el selector inline de técnico en la lista del Coordinador
        ctx["tecnicos"] = []
        if _user_in_group(user, "CoordinadorCeliaquia"):
            ctx["tecnicos"] = User.objects.filter(
                groups__name="TecnicoCeliaquia"
            ).order_by("last_name", "first_name")
        return ctx


@method_decorator(csrf_exempt, name="dispatch")
class ProcesarExpedienteView(View):
    """
    Descripción:
      - Procesa el Excel masivo del expediente y crea/relaciona legajos.
      - Cambia estado a PROCESADO y luego EN_ESPERA (lo hace el service).
    Estados impactados:
      CREADO -> PROCESADO -> EN_ESPERA
    Dependencias:
      ExpedienteService.procesar_expediente
    """

    def post(self, request, pk):
        expediente = get_object_or_404(Expediente, pk=pk, usuario_provincia=request.user)
        try:
            result = ExpedienteService.procesar_expediente(expediente, request.user)
            return JsonResponse({"success": True, "creados": result["creados"], "errores": result["errores"]})
        except ValidationError as ve:
            return JsonResponse({"success": False, "error": ve.message}, status=400)
        except Exception:
            tb = traceback.format_exc()
            logger.error("Error al procesar expediente %s:\n%s", pk, tb)
            return JsonResponse({"success": False, "error": tb}, status=500)


class CrearLegajosView(View):
    """
    Descripción:
      - Crea legajos (ExpedienteCiudadano) a partir de filas JSON.
    """

    def post(self, request, pk):
        expediente = get_object_or_404(Expediente, pk=pk, usuario_provincia=request.user)
        try:
            payload = json.loads(request.body)
            rows = payload.get("rows", [])
        except json.JSONDecodeError:
            return HttpResponseBadRequest("JSON inválido.")
        estado_inicial, _ = EstadoLegajo.objects.get_or_create(nombre="DOCUMENTO_PENDIENTE")
        creados = existentes = 0
        for datos in rows:
            ciudadano = CiudadanoService.get_or_create_ciudadano(datos, request.user)
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
    Descripción:
      - Devuelve headers y primeras filas del Excel para preview.
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
    """
    Descripción:
      - Provincia: puede ver su expediente.
      - Coordinador: puede ver expedientes para recepción/asignación.
      - Técnico: puede ver expedientes propios asignados.
    """

    model = Expediente
    template_name = "celiaquia/expediente_detail.html"
    context_object_name = "expediente"

    def get_queryset(self):
        user = self.request.user
        base = (
            Expediente.objects.select_related("estado", "usuario_modificador", "asignacion_tecnico")
            .prefetch_related("expediente_ciudadanos__ciudadano", "expediente_ciudadanos__estado")
        )
        if _user_in_group(user, "CoordinadorCeliaquia"):
            return base
        if _user_in_group(user, "TecnicoCeliaquia"):
            return base.filter(asignacion_tecnico__tecnico=user)
        return base.filter(usuario_provincia=user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        expediente = self.object
        user = self.request.user

        preview = preview_error = None
        if expediente.estado.nombre == "CREADO" and expediente.excel_masivo:
            try:
                preview = ImportacionService.preview_excel(expediente.excel_masivo)
            except Exception as e:
                preview_error = str(e)

        tecnicos = []
        if _user_in_group(user, "CoordinadorCeliaquia"):
            tecnicos = User.objects.filter(groups__name="TecnicoCeliaquia").order_by("last_name", "first_name")

        faltan_archivos = expediente.expediente_ciudadanos.filter(archivo__isnull=True).exists()

        ctx.update(
            {
                "legajos": expediente.expediente_ciudadanos.all(),
                "confirm_form": ConfirmarEnvioForm(),
                "preview": preview,
                "preview_error": preview_error,
                "tecnicos": tecnicos,
                "faltan_archivos": faltan_archivos,
            }
        )
        return ctx


class ExpedienteImportView(View):
    def post(self, request, pk):
        expediente = get_object_or_404(Expediente, pk=pk, usuario_provincia=request.user)
        start = time.time()
        try:
            result = ImportacionService.importar_legajos_desde_excel(
                expediente, expediente.excel_masivo, request.user
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
    """
    Descripción:
      - Provincia confirma envío (EN_ESPERA → CONFIRMACION_DE_ENVIO) con validación en servidor.
    """

    def post(self, request, pk):
        expediente = get_object_or_404(Expediente, pk=pk, usuario_provincia=request.user)
        try:
            result = ExpedienteService.confirmar_envio(expediente)
            messages.success(
                request,
                f"Expediente enviado a Subsecretaría. Legajos: {result['validos']} (sin errores).",
            )
        except ValidationError as ve:
            logger.warning("Error al confirmar: %s", ve)
            messages.error(request, f"Error al confirmar: {ve.message}")
        except Exception as e:
            logger.error("Error inesperado al confirmar envío: %s", e, exc_info=True)
            messages.error(request, f"Error inesperado: {e}")
        return redirect("expediente_detail", pk=pk)


class ExpedienteUpdateView(UpdateView):
    model = Expediente
    form_class = ExpedienteForm
    template_name = "celiaquia/expediente_form.html"

    def get_success_url(self):
        return reverse_lazy("expediente_detail", args=[self.object.pk])


class RecepcionarExpedienteView(View):
    """
    Descripción:
      - Subsecretaría (Coordinador) recepciona el expediente.
      - Cambia estado: CONFIRMACION_DE_ENVIO -> RECEPCIONADO.
      - Registra usuario_modificador y muestra mensaje.
    """

    def post(self, request, pk):
        if not _user_in_group(request.user, "CoordinadorCeliaquia"):
            raise PermissionDenied("No tiene permisos para recepcionar este expediente.")
        expediente = get_object_or_404(Expediente, pk=pk)
        if expediente.estado.nombre != "CONFIRMACION_DE_ENVIO":
            messages.warning(request, "El expediente no está pendiente de recepción.")
            return redirect("expediente_detail", pk=pk)

        estado_recep, _ = EstadoExpediente.objects.get_or_create(nombre="RECEPCIONADO")
        expediente.estado = estado_recep
        expediente.usuario_modificador = request.user
        expediente.save(update_fields=["estado", "usuario_modificador"])

        messages.success(request, "Expediente recepcionado correctamente. Ahora puede asignar un técnico.")
        return redirect("expediente_detail", pk=pk)

    def get(self, *_a, **_k):
        return HttpResponseNotAllowed(["POST"])


class AsignarTecnicoView(View):
    """
    Descripción:
      - Subsecretaría (Coordinador) asigna un técnico. Al asignar, el expediente pasa a ASIGNADO.
    Reglas:
      - Solo desde RECEPCIONADO o si ya estaba ASIGNADO (cambio de técnico).
      - Técnico debe pertenecer al grupo TecnicoCeliaquia.
    """

    def post(self, request, pk):
        if not _user_in_group(request.user, "CoordinadorCeliaquia"):
            raise PermissionDenied("No tiene permisos para asignar técnico.")

        expediente = get_object_or_404(Expediente, pk=pk)

        tecnico_id = request.POST.get("tecnico_id")
        if not tecnico_id:
            messages.error(request, "No se seleccionó ningún técnico.")
            return redirect("expediente_detail", pk=pk)

        tecnico_qs = User.objects.filter(groups__name="TecnicoCeliaquia")
        tecnico = get_object_or_404(tecnico_qs, pk=tecnico_id)

        estado_actual = expediente.estado.nombre
        if estado_actual not in ("RECEPCIONADO", "ASIGNADO"):
            messages.error(request, "Primero debe recepcionar el expediente.")
            return redirect("expediente_detail", pk=pk)

        AsignacionTecnico.objects.update_or_create(
            expediente=expediente,
            defaults={"tecnico": tecnico},
        )

        estado_asignado, _ = EstadoExpediente.objects.get_or_create(nombre="ASIGNADO")
        expediente.estado = estado_asignado
        expediente.usuario_modificador = request.user
        expediente.save(update_fields=["estado", "usuario_modificador"])

        messages.success(
            request,
            f"Técnico {tecnico.get_full_name() or tecnico.username} asignado correctamente. Estado: ASIGNADO.",
        )
        return redirect("expediente_detail", pk=pk)
