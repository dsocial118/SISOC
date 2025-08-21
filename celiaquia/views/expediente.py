"""
celiaquia/views/expediente.py
"""

import json
import logging
import time
import traceback

from django.views import View
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.http import (
    JsonResponse,
    HttpResponseBadRequest,
    HttpResponseNotAllowed,
)
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
from celiaquia.services.cruce_service import CruceService

logger = logging.getLogger(__name__)


def _user_in_group(user, group_name: str) -> bool:
    return user.is_authenticated and user.groups.filter(name=group_name).exists()

def _is_admin(user) -> bool:

    return user.is_authenticated and user.is_superuser

def _is_ajax(request) -> bool:
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def _parse_limit(value, default=5, max_cap=5000):
    """
    Interpreta un parámetro de límite de filas para preview.
    - 'all', 'ALL', '0' o 0 -> None (sin tope)
    - número > 0 -> min(número, max_cap)
    - inválido -> default
    """
    if value is None:
        return default
    txt = str(value).strip().lower()
    if txt in ("all", "todos", "0", "none"):
        return None 
    try:
        n = int(txt)
        if n <= 0:
            return None
        return min(n, max_cap)
    except Exception:
        return default


class ExpedienteListView(ListView):
    """
    Descripción:
      - Única lista para todos los roles.
        * Admin (superuser): ve todos.
        * ProvinciaCeliaquia: lista sólo sus expedientes.
        * CoordinadorCeliaquia: lista CONFIRMACION_DE_ENVIO, RECEPCIONADO, ASIGNADO.
        * TecnicoCeliaquia: lista asignados a él.
      - Orden descendente por fecha_creacion.
    """

    model = Expediente
    template_name = "celiaquia/expediente_list.html"
    context_object_name = "expedientes"
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        qs = (
            Expediente.objects.select_related("estado", "asignacion_tecnico__tecnico")
            .only(
                "id",
                "codigo",
                "fecha_creacion",
                "estado__nombre",
                "usuario_provincia_id",
                "asignacion_tecnico__tecnico_id",
            )
        )


        if _is_admin(user):
            return qs.order_by("-fecha_creacion")

    
        if _user_in_group(user, "CoordinadorCeliaquia"):
            return qs.filter(
                estado__nombre__in=["CONFIRMACION_DE_ENVIO", "RECEPCIONADO", "ASIGNADO"]
            ).order_by("-fecha_creacion")


        if _user_in_group(user, "TecnicoCeliaquia"):
            return qs.filter(asignacion_tecnico__tecnico=user).order_by("-fecha_creacion")

       
        return qs.filter(usuario_provincia=user).order_by("-fecha_creacion")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        ctx["tecnicos"] = []
       
        if _is_admin(user) or _user_in_group(user, "CoordinadorCeliaquia"):
            ctx["tecnicos"] = User.objects.filter(
                groups__name="TecnicoCeliaquia"
            ).order_by("last_name", "first_name")
        return ctx


@method_decorator(csrf_exempt, name="dispatch")
class ProcesarExpedienteView(View):
    """
    Procesa Excel de nómina y crea/relaciona legajos.
    Cambia estados: CREADO -> PROCESADO -> EN_ESPERA (en service).
    Respuesta JSON (para botón en lista).
    """

    def post(self, request, pk):
        user = self.request.user
        if _is_admin(user):
            expediente = get_object_or_404(Expediente, pk=pk)
        else:
            expediente = get_object_or_404(Expediente, pk=pk, usuario_provincia=user)

        try:
            result = ExpedienteService.procesar_expediente(expediente, user)
            return JsonResponse(
                {"success": True, "creados": result["creados"], "errores": result["errores"]}
            )
        except ValidationError as ve:
            return JsonResponse({"success": False, "error": ve.message}, status=400)
        except Exception:
            tb = traceback.format_exc()
            logger.error("Error al procesar expediente %s:\n%s", pk, tb)
            return JsonResponse({"success": False, "error": tb}, status=500)


class CrearLegajosView(View):
    """
    Crea legajos (ExpedienteCiudadano) a partir de filas JSON.
    """

    def post(self, request, pk):
        user = self.request.user
        if _is_admin(user):
            expediente = get_object_or_404(Expediente, pk=pk)
        else:
            expediente = get_object_or_404(Expediente, pk=pk, usuario_provincia=user)

        try:
            payload = json.loads(request.body)
            rows = payload.get("rows", [])
        except json.JSONDecodeError:
            return HttpResponseBadRequest("JSON inválido.")

        estado_inicial, _ = EstadoLegajo.objects.get_or_create(nombre="DOCUMENTO_PENDIENTE")
        creados = existentes = 0
        for datos in rows:
            ciudadano = CiudadanoService.get_or_create_ciudadano(datos, user)
            _, was_created = ExpedienteCiudadano.objects.get_or_create(
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
    Devuelve headers y primeras filas del Excel de nómina (preview).
    Permite controlar la cantidad de filas con el parámetro 'limit' (GET o POST):
      - limit=all / 0 / none => todas las filas
      - limit=<número>        => n primeras filas (clamp al máximo)
      - omitido               => 5 filas por defecto
    """

    def post(self, request, *args, **kwargs):
        logger.debug("PREVIEW: %s %s", request.method, request.path)
        archivo = request.FILES.get("excel_masivo")
        if not archivo:
            return JsonResponse({"error": "No se recibió ningún archivo."}, status=400)

        raw_limit = request.POST.get("limit") or request.GET.get("limit")
        max_rows = _parse_limit(raw_limit, default=5, max_cap=5000)

        try:
            preview = ImportacionService.preview_excel(archivo, max_rows=max_rows)
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

    model = Expediente
    template_name = "celiaquia/expediente_detail.html"
    context_object_name = "expediente"

    def get_queryset(self):
        user = self.request.user
        base = (
            Expediente.objects.select_related("estado", "usuario_modificador", "asignacion_tecnico")
            .prefetch_related("expediente_ciudadanos__ciudadano", "expediente_ciudadanos__estado")
        )
        if _is_admin(user) or _user_in_group(user, "CoordinadorCeliaquia"):
            return base
        if _user_in_group(user, "TecnicoCeliaquia"):
            return base.filter(asignacion_tecnico__tecnico=user)
        return base.filter(usuario_provincia=user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        expediente = self.object
        user = self.request.user

        preview = preview_error = None
        preview_limit_actual = None  

        q = expediente.expediente_ciudadanos.select_related("ciudadano")
        ctx["legajos_aceptados"] = q.filter(revision_tecnico="APROBADO", resultado_sintys="MATCH")
        ctx["legajos_rech_tecnico"] = q.filter(revision_tecnico="RECHAZADO")
        ctx["legajos_rech_sintys"] = q.filter(revision_tecnico="APROBADO", resultado_sintys="NO_MATCH")

        ctx["c_aceptados"] = ctx["legajos_aceptados"].count()
        ctx["c_rech_tecnico"] = ctx["legajos_rech_tecnico"].count()
        ctx["c_rech_sintys"] = ctx["legajos_rech_sintys"].count()

        if expediente.estado.nombre == "CREADO" and expediente.excel_masivo:

            raw_limit = self.request.GET.get("preview_limit")
            max_rows = _parse_limit(raw_limit, default=5, max_cap=5000)
            preview_limit_actual = raw_limit if raw_limit is not None else "5"

            try:
                preview = ImportacionService.preview_excel(expediente.excel_masivo, max_rows=max_rows)

            except Exception as e:
                preview_error = str(e)

        preview_limit_opciones = ["5", "10", "20", "50", "100", "all"]

        tecnicos = []
        if _is_admin(user) or _user_in_group(user, "CoordinadorCeliaquia"):
            tecnicos = User.objects.filter(
                groups__name="TecnicoCeliaquia"
            ).order_by("last_name", "first_name")

        faltan_archivos = expediente.expediente_ciudadanos.filter(archivo__isnull=True).exists()

        ctx.update(
            {
                "legajos": expediente.expediente_ciudadanos.all(),
                "confirm_form": ConfirmarEnvioForm(),
                "preview": preview,                     
                "preview_error": preview_error,        
                "preview_limit_actual": str(preview_limit_actual or "5").lower(),
                "preview_limit_opciones": preview_limit_opciones,
                "tecnicos": tecnicos,
                "faltan_archivos": faltan_archivos,
            }
        )
        return ctx



class ExpedienteImportView(View):
    def post(self, request, pk):
        user = self.request.user
        if _is_admin(user):
            expediente = get_object_or_404(Expediente, pk=pk)
        else:
            expediente = get_object_or_404(Expediente, pk=pk, usuario_provincia=user)

        start = time.time()
        try:
            result = ImportacionService.importar_legajos_desde_excel(
                expediente, expediente.excel_masivo, user
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
    Provincia confirma envío (EN_ESPERA → CONFIRMACION_DE_ENVIO) con validación servidor.
    - Si es AJAX, responde JSON (para lista).
    - Si no, redirige con messages.
    Admin también puede confirmar.
    """

    def post(self, request, pk):
        user = self.request.user
        if _is_admin(user):
            expediente = get_object_or_404(Expediente, pk=pk)
        else:
            expediente = get_object_or_404(Expediente, pk=pk, usuario_provincia=user)

        try:
            result = ExpedienteService.confirmar_envio(expediente)
            if _is_ajax(request):
                return JsonResponse(
                    {
                        "success": True,
                        "message": "Expediente enviado a Subsecretaría.",
                        "validos": result["validos"],
                        "errores": result["errores"],
                    }
                )
            messages.success(
                request,
                f"Expediente enviado a Subsecretaría. Legajos: {result['validos']} (sin errores).",
            )
        except ValidationError as ve:
            if _is_ajax(request):
                return JsonResponse({"success": False, "error": ve.message}, status=400)
            messages.error(request, f"Error al confirmar: {ve.message}")
        except Exception as e:
            logger.error("Error inesperado al confirmar envío: %s", e, exc_info=True)
            if _is_ajax(request):
                return JsonResponse({"success": False, "error": str(e)}, status=500)
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
    Subsecretaría recepciona:
    CONFIRMACION_DE_ENVIO -> RECEPCIONADO.
    Responde JSON si es AJAX; si no, redirect con messages.
    Admin también puede recepcionar.
    """

    def post(self, request, pk):
        user = self.request.user
        if not (_is_admin(user) or _user_in_group(user, "CoordinadorCeliaquia")):
            if _is_ajax(request):
                return JsonResponse({"success": False, "error": "Permiso denegado."}, status=403)
            raise PermissionDenied("No tiene permisos para recepcionar este expediente.")

        expediente = get_object_or_404(Expediente, pk=pk)
        if expediente.estado.nombre != "CONFIRMACION_DE_ENVIO":
            msg = "El expediente no está pendiente de recepción."
            if _is_ajax(request):
                return JsonResponse({"success": False, "error": msg}, status=400)
            messages.warning(request, msg)
            return redirect("expediente_detail", pk=pk)

        estado_recep, _ = EstadoExpediente.objects.get_or_create(nombre="RECEPCIONADO")
        expediente.estado = estado_recep
        expediente.usuario_modificador = user
        expediente.save(update_fields=["estado", "usuario_modificador"])

        if _is_ajax(request):
            return JsonResponse({"success": True, "message": "Recepcionado correctamente."})
        messages.success(request, "Expediente recepcionado correctamente. Ahora puede asignar un técnico.")
        return redirect("expediente_detail", pk=pk)

    def get(self, *_a, **_k):
        return HttpResponseNotAllowed(["POST"])


class AsignarTecnicoView(View):
    """
    Subsecretaría asigna técnico:
    RECEPCIONADO -> ASIGNADO (o cambio de técnico manteniendo ASIGNADO).
    Responde JSON si es AJAX; si no, redirect con messages.
    Admin también puede asignar.
    """

    def post(self, request, pk):
        user = self.request.user
        if not (_is_admin(user) or _user_in_group(user, "CoordinadorCeliaquia")):
            if _is_ajax(request):
                return JsonResponse({"success": False, "error": "Permiso denegado."}, status=403)
            raise PermissionDenied("No tiene permisos para asignar técnico.")

        expediente = get_object_or_404(Expediente, pk=pk)

        tecnico_id = request.POST.get("tecnico_id")
        if not tecnico_id:
            msg = "No se seleccionó ningún técnico."
            if _is_ajax(request):
                return JsonResponse({"success": False, "error": msg}, status=400)
            messages.error(request, msg)
            return redirect("expediente_detail", pk=pk)

        tecnico_qs = User.objects.filter(groups__name="TecnicoCeliaquia")
        tecnico = get_object_or_404(tecnico_qs, pk=tecnico_id)

        estado_actual = expediente.estado.nombre
        if estado_actual not in ("RECEPCIONADO", "ASIGNADO"):
            msg = "Primero debe recepcionar el expediente."
            if _is_ajax(request):
                return JsonResponse({"success": False, "error": msg}, status=400)
            messages.error(request, msg)
            return redirect("expediente_detail", pk=pk)

        AsignacionTecnico.objects.update_or_create(
            expediente=expediente,
            defaults={"tecnico": tecnico},
        )

        estado_asignado, _ = EstadoExpediente.objects.get_or_create(nombre="ASIGNADO")
        expediente.estado = estado_asignado
        expediente.usuario_modificador = user
        expediente.save(update_fields=["estado", "usuario_modificador"])

        if _is_ajax(request):
            return JsonResponse(
                {
                    "success": True,
                    "message": "Técnico asignado correctamente. Estado: ASIGNADO.",
                }
            )
        messages.success(
            request,
            f"Técnico {tecnico.get_full_name() or tecnico.username} asignado correctamente. Estado: ASIGNADO.",
        )
        return redirect("expediente_detail", pk=pk)


class SubirCruceExcelView(View):


    def post(self, request, pk):
        user = self.request.user

        if not (_is_admin(user) or _user_in_group(user, "TecnicoCeliaquia")):
            return JsonResponse({"success": False, "error": "Permiso denegado."}, status=403)

        expediente = get_object_or_404(Expediente, pk=pk)


        if not _is_admin(user):
            asignacion = getattr(expediente, "asignacion_tecnico", None)
            if not asignacion or asignacion.tecnico_id != user.id:
                return JsonResponse({"success": False, "error": "No sos el técnico asignado a este expediente."}, status=403)

        archivo = request.FILES.get("archivo")
        if not archivo:
            return JsonResponse({"success": False, "error": "Debe adjuntar un Excel con columna 'cuit'."}, status=400)

        try:
            resumen = CruceService.procesar_cruce_por_cuit(expediente, archivo, user)
            return JsonResponse(
                {
                    "success": True,
                    "message": "Cruce finalizado. Se generó el PRD del expediente.",
                    "resumen": resumen,
                }
            )
        except ValidationError as ve:
            return JsonResponse({"success": False, "error": ve.message}, status=400)
        except Exception as e:
            logger.error("Error en cruce por CUIT: %s", e, exc_info=True)
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    def get(self, *_a, **_k):
        return HttpResponseNotAllowed(["POST"])
    
@method_decorator(csrf_exempt, name="dispatch")
class RevisarLegajoView(View):
    def post(self, request, pk, legajo_id):
        user = request.user
        expediente = get_object_or_404(Expediente, pk=pk)


        if not (_is_admin(user) or _user_in_group(user, "TecnicoCeliaquia")):
            return JsonResponse({"success": False, "error": "Permiso denegado."}, status=403)
        if not _is_admin(user):
            asig = getattr(expediente, "asignacion_tecnico", None)
            if not asig or asig.tecnico_id != user.id:
                return JsonResponse({"success": False, "error": "No sos el técnico asignado."}, status=403)

        leg = get_object_or_404(ExpedienteCiudadano, pk=legajo_id, expediente=expediente)

        accion = (request.POST.get("accion") or "").upper()  
        if accion not in ("APROBAR", "RECHAZAR"):
            return JsonResponse({"success": False, "error": "Acción inválida."}, status=400)

        leg.revision_tecnico = "APROBADO" if accion == "APROBAR" else "RECHAZADO"
        leg.save(update_fields=["revision_tecnico", "modificado_en"])

        return JsonResponse({"success": True, "estado": leg.revision_tecnico})

