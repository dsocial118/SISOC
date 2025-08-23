"""
[celiaquia/views/legajo.py]

- Se mantiene LegajoArchivoUploadView (carga de archivo).
- Se agregan/usan vistas POST para operar sobre el legajo y liberar cupo cuando aplica:
  * LegajoRechazarView: cambia revision_tecnico a RECHAZADO y, si estaba DENTRO, libera cupo.
  * LegajoSuspenderView: marca es_titular_activo=False y libera cupo si estaba DENTRO.
  * LegajoBajaView: baja definitiva; es_titular_activo=False, RECHAZADO y libera cupo si estaba DENTRO.

Nota: Se quitaron decoradores de roles; los permisos se controlan por URL/routers.
"""

import logging

from django.shortcuts import get_object_or_404
from django.views import View
from django.http import JsonResponse, HttpResponseNotAllowed
from django.contrib import messages  # Compatibilidad con UI que use mensajes
from django.core.exceptions import ValidationError
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect

from celiaquia.models import ExpedienteCiudadano
from celiaquia.forms import LegajoArchivoForm
from celiaquia.services.legajo_service import LegajoService
from celiaquia.services.cupo_service import CupoService, CupoNoConfigurado

logger = logging.getLogger(__name__)


class LegajoArchivoUploadView(View):
    """
    Recibe un archivo PDF/imagen y lo asocia a un legajo (ExpedienteCiudadano),
    validando con LegajoArchivoForm y usando LegajoService.subir_archivo_individual().
    """

    def dispatch(self, request, *args, **kwargs):
        self.exp_ciud = get_object_or_404(
            ExpedienteCiudadano,
            pk=self.kwargs["pk"],
            expediente__pk=self.kwargs["expediente_id"],
            expediente__usuario_provincia=request.user,
        )
        return super().dispatch(request, *args, **kwargs)

    @method_decorator(csrf_protect)
    def post(self, request, *args, **kwargs):
        form = LegajoArchivoForm(request.POST, request.FILES, instance=self.exp_ciud)

        if form.is_valid():
            try:
                LegajoService.subir_archivo_individual(
                    self.exp_ciud, form.cleaned_data["archivo"]
                )
                return JsonResponse(
                    {"success": True, "message": "Archivo cargado correctamente."}
                )
            except ValidationError as ve:
                return JsonResponse(
                    {"success": False, "message": f"Error de validación: {ve}"}, status=400
                )
            except Exception as e:
                logger.error("Error al subir archivo de legajo %s: %s", self.exp_ciud.pk, e, exc_info=True)
                return JsonResponse(
                    {"success": False, "message": "Ocurrió un error al subir el archivo."}, status=500
                )

        errores = form.errors.get_json_data()
        errores_msg = " ".join([e["message"] for campo in errores.values() for e in campo])
        return JsonResponse({"success": False, "message": f"Error de validación: {errores_msg}"}, status=400)

    def get(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(["POST"])


class LegajoRechazarView(View):
    """
    Rechazo del legajo.
    - revision_tecnico -> 'RECHAZADO'
    - Si estaba DENTRO, libera cupo (idempotente).
    """

    @method_decorator(csrf_protect)
    def post(self, request, *args, **kwargs):
        expediente_id = kwargs.get("expediente_id")
        pk = kwargs.get("pk")
        legajo = get_object_or_404(ExpedienteCiudadano, pk=pk, expediente__pk=expediente_id)

        try:
            CupoService.liberar_slot(
                legajo=legajo, usuario=request.user, motivo="Rechazo por técnico/coordinador"
            )
            legajo.revision_tecnico = "RECHAZADO"
            legajo.save()
            return JsonResponse(
                {"success": True, "message": "Legajo rechazado y cupo liberado (si correspondía)."}
            )
        except CupoNoConfigurado as e:
            logger.warning(
                "Rechazo legajo %s: provincia sin cupo configurado. Detalle: %s", legajo.pk, e
            )
            legajo.revision_tecnico = "RECHAZADO"
            legajo.save()
            return JsonResponse(
                {"success": True, "message": "Legajo rechazado. Provincia sin cupo configurado."}
            )
        except ValidationError as ve:
            return JsonResponse({"success": False, "message": f"Error de validación: {ve}"}, status=400)
        except Exception as e:
            logger.error("Error al rechazar legajo %s: %s", legajo.pk, e, exc_info=True)
            return JsonResponse({"success": False, "message": "Error al rechazar el legajo."}, status=500)

    def get(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(["POST"])


class LegajoSuspenderView(View):
    """
    Suspensión administrativa.
    - es_titular_activo=False
    - Si estaba DENTRO, libera cupo.
    - No fuerza RECHAZADO.
    """

    @method_decorator(csrf_protect)
    def post(self, request, *args, **kwargs):
        expediente_id = kwargs.get("expediente_id")
        pk = kwargs.get("pk")
        legajo = get_object_or_404(ExpedienteCiudadano, pk=pk, expediente__pk=expediente_id)

        try:
            CupoService.liberar_slot(
                legajo=legajo, usuario=request.user, motivo="Suspensión administrativa"
            )
            legajo.es_titular_activo = False
            legajo.save()
            return JsonResponse(
                {"success": True, "message": "Legajo suspendido y cupo liberado (si correspondía)."}
            )
        except CupoNoConfigurado as e:
            logger.warning(
                "Suspensión legajo %s: provincia sin cupo configurado. Detalle: %s", legajo.pk, e
            )
            legajo.es_titular_activo = False
            legajo.save()
            return JsonResponse(
                {"success": True, "message": "Legajo suspendido. Provincia sin cupo configurado."}
            )
        except ValidationError as ve:
            return JsonResponse({"success": False, "message": f"Error de validación: {ve}"}, status=400)
        except Exception as e:
            logger.error("Error al suspender legajo %s: %s", legajo.pk, e, exc_info=True)
            return JsonResponse({"success": False, "message": "Error al suspender el legajo."}, status=500)

    def get(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(["POST"])


class LegajoBajaView(View):
    """
    Baja definitiva.
    - es_titular_activo=False
    - revision_tecnico='RECHAZADO'
    - Si estaba DENTRO, libera cupo.
    """

    @method_decorator(csrf_protect)
    def post(self, request, *args, **kwargs):
        expediente_id = kwargs.get("expediente_id")
        pk = kwargs.get("pk")
        legajo = get_object_or_404(ExpedienteCiudadano, pk=pk, expediente__pk=expediente_id)

        try:
            CupoService.liberar_slot(
                legajo=legajo, usuario=request.user, motivo="Baja definitiva por coordinador"
            )
            legajo.es_titular_activo = False
            legajo.revision_tecnico = "RECHAZADO"
            legajo.save()
            return JsonResponse({"success": True, "message": "Baja registrada y cupo liberado (si correspondía)."})
        except CupoNoConfigurado as e:
            logger.warning(
                "Baja legajo %s: provincia sin cupo configurado. Detalle: %s", legajo.pk, e
            )
            legajo.es_titular_activo = False
            legajo.revision_tecnico = "RECHAZADO"
            legajo.save()
            return JsonResponse({"success": True, "message": "Baja registrada. Provincia sin cupo configurado."})
        except ValidationError as ve:
            return JsonResponse({"success": False, "message": f"Error de validación: {ve}"}, status=400)
        except Exception as e:
            logger.error("Error al dar de baja legajo %s: %s", legajo.pk, e, exc_info=True)
            return JsonResponse({"success": False, "message": "Error al dar de baja el legajo."}, status=500)

    def get(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(["POST"])
