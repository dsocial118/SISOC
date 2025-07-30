from django.shortcuts import get_object_or_404
from django.views import View
from django.http import JsonResponse, HttpResponseNotAllowed
from django.contrib import messages

from celiaquia.models import ExpedienteCiudadano
from celiaquia.forms import LegajoArchivoForm
from celiaquia.services.legajo_service import LegajoService


class LegajoArchivoUploadView(View):
    """
    Vista encargada de recibir un archivo PDF o imagen y asociarlo
    a un legajo específico (ExpedienteCiudadano), identificado por
    expediente_id y pk. Utiliza LegajoArchivoForm para validar y
    LegajoService.subir_archivo_individual() para guardar el archivo.

    Esta vista NO acepta GET, solo POST.
    """

    def dispatch(self, request, *args, **kwargs):
        self.exp_ciud = get_object_or_404(
            ExpedienteCiudadano,
            pk=self.kwargs['pk'],
            expediente__pk=self.kwargs['expediente_id'],
            expediente__usuario_provincia=request.user,
        )
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = LegajoArchivoForm(request.POST, request.FILES, instance=self.exp_ciud)

        if form.is_valid():
            LegajoService.subir_archivo_individual(
                self.exp_ciud, form.cleaned_data["archivo"]
            )
            return JsonResponse({
                "success": True,
                "message": "Archivo cargado correctamente."
            })

        # Si hay errores de validación
        errores = form.errors.get_json_data()
        errores_msg = " ".join(
            [e["message"] for campo in errores.values() for e in campo]
        )
        return JsonResponse({
            "success": False,
            "message": f"Error de validación: {errores_msg}"
        }, status=400)

    def get(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(["POST"])
