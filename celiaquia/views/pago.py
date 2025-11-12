import io
import logging

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import FileResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.decorators.csrf import csrf_protect
from django.views.generic import ListView
from django.utils.decorators import method_decorator

from core.models import Provincia
from celiaquia.models import PagoExpediente
from celiaquia.forms import PagoRespuestaUploadForm
from celiaquia.services.pago_service import PagoService

logger = logging.getLogger("django")


class PagoExpedienteListView(ListView):
    """Lista los expedientes de pago de una provincia."""

    model = PagoExpediente
    template_name = "celiaquia/pago_expediente_list.html"
    context_object_name = "pagos"

    def get_queryset(self):
        provincia_id = self.kwargs.get("provincia_id")
        return PagoExpediente.objects.filter(provincia_id=provincia_id).order_by(
            "-creado_en"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["provincia"] = get_object_or_404(
            Provincia, pk=self.kwargs.get("provincia_id")
        )
        return context


class PagoExpedienteCreateView(View):
    """
    Genera el expediente de pago (toma la nómina consolidada activa) y crea Excel de envío.
    """

    @method_decorator(csrf_protect)
    def post(self, request, provincia_id: int):
        provincia = get_object_or_404(Provincia, pk=provincia_id)
        try:
            pago = PagoService.crear_expediente_pago(
                provincia=provincia, usuario=request.user
            )
        except ValidationError as ve:
            messages.error(request, str(ve))
            return redirect("cupo_provincia_detail", provincia_id=provincia.id)
        except Exception as e:
            logger.error("Error al crear expediente de pago: %s", e, exc_info=True)
            messages.error(request, "No se pudo crear el expediente de pago.")
            return redirect("cupo_provincia_detail", provincia_id=provincia.id)

        return HttpResponseRedirect(reverse("pago_expediente_detail", args=[pago.id]))


class PagoExpedienteDetailView(View):
    """
    Detalle del expediente de pago: link de descarga del Excel y formulario para subir respuesta.
    """

    def get(self, request, pago_id: int):
        pago = get_object_or_404(PagoExpediente, pk=pago_id)
        form = PagoRespuestaUploadForm()
        return render(
            request,
            "celiaquia/pago_expediente_detail.html",
            {"pago": pago, "form": form},
        )

    @method_decorator(csrf_protect)
    def post(self, request, pago_id: int):
        pago = get_object_or_404(PagoExpediente, pk=pago_id)
        form = PagoRespuestaUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            messages.error(request, "Subí un archivo válido.")
            return redirect("pago_expediente_detail", pago_id=pago.id)

        try:
            stats = PagoService.procesar_respuesta(
                pago=pago,
                archivo_respuesta=form.cleaned_data["archivo"],
                usuario=request.user,
            )
            messages.success(
                request,
                f"Respuesta procesada. Validados: {stats['validados']} — Excluidos: {stats['excluidos']}.",
            )
        except ValidationError as ve:
            messages.error(request, str(ve))
        except Exception as e:
            logger.error("Error al procesar respuesta de pago: %s", e, exc_info=True)
            messages.error(request, "No se pudo procesar la respuesta.")

        return redirect("pago_expediente_detail", pago_id=pago.id)


class PagoExpedienteExportView(View):
    """
    Descarga del archivo de envío guardado en el expediente de pago.
    """

    def get(self, request, pago_id: int):
        pago = get_object_or_404(PagoExpediente, pk=pago_id)
        if not pago.archivo_envio:
            messages.error(request, "El expediente no tiene archivo de envío.")
            return redirect("pago_expediente_detail", pago_id=pago.id)
        return FileResponse(
            pago.archivo_envio.open("rb"),
            as_attachment=True,
            filename=pago.archivo_envio.name.split("/")[-1],
        )


class PagoNominaExportActualView(View):
    """
    Exporta la nómina ACTUAL (aceptados activos) de la provincia del expediente de pago.
    No incluye suspendidos.
    """

    def get(self, request, pago_id: int):
        pago = get_object_or_404(PagoExpediente, pk=pago_id)
        content = PagoService.exportar_nomina_actual_excel(provincia=pago.provincia)
        filename = f"nomina_actual_{pago.provincia.id}_{pago.periodo}.xlsx"
        return FileResponse(io.BytesIO(content), as_attachment=True, filename=filename)
