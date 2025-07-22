from django.shortcuts import get_object_or_404, redirect
from django.views.generic.edit import FormView
from django.contrib import messages
from configuraciones.decorators import group_required

from celiaquia.models import ExpedienteCiudadano
from celiaquia.forms import LegajoArchivoForm
from celiaquia.services.legajo_service import LegajoService


class LegajoArchivoUploadView(FormView):
    form_class = LegajoArchivoForm
    template_name = "celiaquia/legajo_upload.html"

    def dispatch(self, request, expediente_id, pk, *args, **kwargs):
        self.exp_ciud = get_object_or_404(
            ExpedienteCiudadano,
            pk=pk,
            expediente__pk=expediente_id,
            expediente__usuario_provincia=request.user,
        )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        LegajoService.subir_archivo_individual(
            self.exp_ciud, form.cleaned_data["archivo"]
        )
        messages.success(self.request, "Archivo cargado correctamente.")
        return redirect("expediente_detail", pk=self.exp_ciud.expediente.pk)
