import logging
from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.http import JsonResponse, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.core.exceptions import ValidationError

from ciudadanos.models import Provincia
from celiaquia.models import (
    CupoMovimiento,
    ProvinciaCupo,
    ExpedienteCiudadano,
    EstadoCupo,
)
from celiaquia.forms import CupoBajaLegajoForm, CupoSuspenderLegajoForm
from celiaquia.services.cupo_service import CupoService, CupoNoConfigurado

logger = logging.getLogger(__name__)


class CupoDashboardView(View):
    """
    Cuadro por provincia: total, usados, disponibles, fuera de cupo.
    """

    def get(self, request):
        rows = []
        qs = (
            ProvinciaCupo.objects
            .select_related("provincia")
            .all()
            .order_by("provincia__nombre")
        )
        for pc in qs:
            try:
                metrics = CupoService.metrics_por_provincia(pc.provincia)
            except CupoNoConfigurado:
                metrics = {"total_asignado": 0, "usados": 0, "disponibles": 0, "fuera": 0}
            rows.append(
                {
                    "provincia": pc.provincia,
                    "total_asignado": metrics.get("total_asignado", 0),
                    "usados": metrics.get("usados", 0),
                    "disponibles": metrics.get("disponibles", 0),
                    "fuera": metrics.get("fuera", 0),
                }
            )
        # Provincias sin registro de cupo (opcional: listarlas con 0)
        sin_cupo = Provincia.objects.exclude(id__in=qs.values_list("provincia_id", flat=True))
        for p in sin_cupo:
            rows.append(
                {"provincia": p, "total_asignado": None, "usados": None, "disponibles": None, "fuera": None}
            )
        return render(request, "celiaquia/cupo_dashboard.html", {"rows": rows})


class CupoProvinciaDetailView(View):
    def get(self, request, provincia_id: int):
        provincia = get_object_or_404(Provincia, pk=provincia_id)
        try:
            metrics = CupoService.metrics_por_provincia(provincia)
        except CupoNoConfigurado:
            metrics = None

        # Titulares activos (ocupan cupo)
        ocupados_qs = (
            CupoService.lista_ocupados_por_provincia(provincia)
            .select_related("ciudadano", "expediente", "expediente__usuario_provincia")
        )
        # Suspendidos: mantienen DENTRO (cupo ocupado) pero es_titular_activo = False
        suspendidos_qs = (
            ExpedienteCiudadano.objects
            .select_related("ciudadano", "expediente", "expediente__usuario_provincia")
            .filter(
                expediente__usuario_provincia__profile__provincia=provincia,
                estado_cupo=EstadoCupo.DENTRO,
                es_titular_activo=False,
            )
        )

        # Lista de espera: fuera de cupo
        lista_espera_qs = (
            ExpedienteCiudadano.objects
            .select_related("ciudadano", "expediente", "expediente__usuario_provincia")
            .filter(
                expediente__usuario_provincia__profile__provincia=provincia,
                estado_cupo=EstadoCupo.FUERA,
            )
        )

        # Histórico de movimientos para la provincia (incluye fallback por expediente)
        movimientos = (
            CupoMovimiento.objects
            .select_related("legajo", "legajo__ciudadano", "expediente", "usuario")
            .filter(
                Q(provincia=provincia) |
                Q(
                    provincia__isnull=True,
                    expediente__usuario_provincia__profile__provincia=provincia,
                )
            )
            .order_by("-creado_en")
        )

        ctx = {
            "provincia": provincia,
            "metrics": metrics,
            "ocupados": ocupados_qs,
            "suspendidos": suspendidos_qs,
            "lista_espera": lista_espera_qs,
            "form_baja": CupoBajaLegajoForm(),
            "form_suspender": CupoSuspenderLegajoForm(),
            "movimientos": movimientos,
        }
        return render(request, "celiaquia/cupo_provincia.html", ctx)

    @method_decorator(csrf_protect)
    def post(self, request, provincia_id: int):
        # Llamado por el modal “Configurar cupo”
        accion = (request.POST.get("accion") or "").strip().lower()
        if accion != "config":
            return JsonResponse({"success": False, "message": "Acción inválida."}, status=400)

        provincia = get_object_or_404(Provincia, pk=provincia_id)

        raw_total = request.POST.get("total_asignado")
        try:
            total = int(raw_total)
            if total < 0:
                raise ValueError
        except Exception:
            return JsonResponse({"success": False, "message": "Valor de cupo inválido."}, status=400)

        try:
            CupoService.configurar_total(provincia, total, request.user)
            metrics = CupoService.metrics_por_provincia(provincia)
            return JsonResponse({
                "success": True,
                "message": "Cupo actualizado correctamente.",
                "metrics": metrics,
            })
        except ValidationError as ve:
            return JsonResponse({"success": False, "message": str(ve)}, status=400)
        except Exception as e:
            logger.error("Error al configurar cupo: %s", e, exc_info=True)
            return JsonResponse({"success": False, "message": "Error inesperado."}, status=500)


class _BaseAccionLegajo(View):
    """
    Utilidad para validar pertenencia del legajo a la provincia.
    """

    def _get_legajo_validado(self, provincia_id: int, legajo_id: int) -> ExpedienteCiudadano:
        provincia = get_object_or_404(Provincia, pk=provincia_id)
        legajo = get_object_or_404(
            ExpedienteCiudadano.objects.select_related(
                "expediente", "expediente__usuario_provincia", "expediente__usuario_provincia__profile"
            ),
            pk=legajo_id,
        )
        leg_prov = getattr(legajo.expediente.usuario_provincia.profile, "provincia", None)
        if not leg_prov or leg_prov.id != provincia.id:
            raise ValidationError("El legajo no pertenece a la provincia indicada.")
        return legajo


class CupoBajaLegajoView(_BaseAccionLegajo):
    """
    Baja definitiva: libera cupo si estaba DENTRO, marca RECHAZADO y es_titular_activo=False.
    Responde JSON.
    """

    @method_decorator(csrf_protect)
    def post(self, request, provincia_id: int, legajo_id: int):
        form = CupoBajaLegajoForm(request.POST)
        if not form.is_valid():
            return JsonResponse({"success": False, "message": form.errors.as_json()}, status=400)

        motivo = form.cleaned_data["motivo"]
        try:
            legajo = self._get_legajo_validado(provincia_id, legajo_id)
        except ValidationError as ve:
            return JsonResponse({"success": False, "message": str(ve)}, status=400)

        try:
            CupoService.liberar_slot(
                legajo=legajo, usuario=request.user, motivo=f"Baja por coordinador: {motivo}"
            )
        except CupoNoConfigurado:
            logger.warning("Baja legajo %s sin cupo configurado.", legajo.id)
        except Exception as e:
            logger.error("Error al liberar cupo en baja legajo %s: %s", legajo.id, e, exc_info=True)
            return JsonResponse({"success": False, "message": "No se pudo liberar el cupo."}, status=500)

        legajo.es_titular_activo = False
        legajo.revision_tecnico = "RECHAZADO"
        legajo.save(update_fields=["es_titular_activo", "revision_tecnico", "modificado_en"])
        return JsonResponse({"success": True, "message": "Baja registrada y cupo actualizado."})

    def get(self, *_a, **_k):
        return HttpResponseNotAllowed(["POST"])


class CupoSuspenderLegajoView(_BaseAccionLegajo):
    """
    Suspensión: mantiene el cupo ocupado (estado_cupo=DENTRO) y marca es_titular_activo=False.
    No descuenta usados.
    Responde JSON.
    """

    @method_decorator(csrf_protect)
    def post(self, request, provincia_id: int, legajo_id: int):
        form = CupoSuspenderLegajoForm(request.POST)
        if not form.is_valid():
            return JsonResponse({"success": False, "message": form.errors.as_json()}, status=400)

        motivo = form.cleaned_data["motivo"]
        try:
            legajo = self._get_legajo_validado(provincia_id, legajo_id)
        except ValidationError as ve:
            return JsonResponse({"success": False, "message": str(ve)}, status=400)

        try:
            # IMPORTANTE: suspender (no liberar)
            CupoService.suspender_slot(
                legajo=legajo, usuario=request.user, motivo=f"Suspensión por coordinador: {motivo}"
            )
        except CupoNoConfigurado:
            logger.warning("Suspensión legajo %s sin cupo configurado.", legajo.id)
        except Exception as e:
            logger.error("Error al suspender legajo %s: %s", legajo.id, e, exc_info=True)
            return JsonResponse({"success": False, "message": "No se pudo suspender el legajo."}, status=500)

        return JsonResponse({"success": True, "message": "Suspensión registrada."})

    def get(self, *_a, **_k):
        return HttpResponseNotAllowed(["POST"])
    
class CupoReactivarLegajoView(_BaseAccionLegajo):
    """
    Reactivación: mantiene estado_cupo=DENTRO y pone es_titular_activo=True.
    No modifica 'usados'. Responde JSON.
    """
    @method_decorator(csrf_protect)
    def post(self, request, provincia_id: int, legajo_id: int):
        try:
            legajo = self._get_legajo_validado(provincia_id, legajo_id)
        except ValidationError as ve:
            return JsonResponse({"success": False, "message": str(ve)}, status=400)

        try:
            ok = CupoService.reactivar_slot(
                legajo=legajo,
                usuario=request.user,
                motivo="Reactivación por coordinador"
            )
            if not ok:
                return JsonResponse({
                    "success": False,
                    "message": "El legajo no está suspendido o no está dentro de cupo."
                }, status=400)
        except CupoNoConfigurado:
            logger.warning("Reactivación legajo %s sin cupo configurado.", legajo.id)
            return JsonResponse({"success": False, "message": "Provincia sin cupo configurado."}, status=400)
        except Exception as e:
            logger.error("Error al reactivar legajo %s: %s", legajo.id, e, exc_info=True)
            return JsonResponse({"success": False, "message": "No se pudo reactivar el legajo."}, status=500)

        return JsonResponse({"success": True, "message": "Titular reactivado."})

    def get(self, *_a, **_k):
        return HttpResponseNotAllowed(["POST"])

