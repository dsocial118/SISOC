from django.shortcuts import get_object_or_404, redirect
from django.views.generic import View, FormView
from django.contrib import messages
from configuraciones.decorators import group_required

from celiaquia.models import Expediente
from celiaquia.forms import CruceUploadForm
from celiaquia.services.cruce_service import CruceService


class CruceUploadView(FormView):
    form_class    = CruceUploadForm
    template_name = 'celiaquia/cruce_upload.html'

    def dispatch(self, request, pk, *args, **kwargs):
        self.expediente = get_object_or_404(Expediente, pk=pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        CruceService.subir_archivo_cruce(
            self.expediente,
            form.cleaned_data['organismo'].pk,
            form.cleaned_data['tipo'].pk,
            form.cleaned_data['archivo']
        )
        messages.success(self.request, "Archivo de cruce subido correctamente.")
        return redirect('cruce_procesar', pk=self.expediente.pk)



class CruceProcesarView(View):
    def post(self, request, pk):
        expediente = get_object_or_404(Expediente, pk=pk)
        result = CruceService.procesar_todos_los_cruces(expediente)
        messages.success(
            request,
            f"{result.get('procesados', 0)} procesados, "
            f"{result.get('errores', 0)} con error."
        )
        return redirect('cruce_finalizar', pk=pk)


class CruceFinalizarView(View):
    def post(self, request, pk):
        expediente = get_object_or_404(Expediente, pk=pk)
        CruceService.finalizar_cruce(expediente)
        messages.success(request, "Cruce finalizado correctamente.")
        return redirect('expediente_detail', pk=pk)
