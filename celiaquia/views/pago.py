from urllib import request
from django.shortcuts import get_object_or_404, redirect
from django.views.generic.edit import FormView
from django.contrib import messages
from configuraciones.decorators import group_required

from celiaquia.models import Expediente
from celiaquia.forms import PagoForm
from celiaquia.services.expediente_service import ExpedienteService



class OpenPaymentView(FormView):
    form_class    = PagoForm
    template_name = 'celiaquia/payment_open.html'

    def dispatch(self, request, pk, *args, **kwargs):
        self.expediente = get_object_or_404(Expediente, pk=pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        ExpedienteService.open_payment(self.expediente)
        messages.success(self.request, "Proceso de pago abierto correctamente.")
        return redirect('expediente_detail', pk=self.expediente.pk)



class ClosePaymentView(FormView):
    form_class    = PagoForm
    template_name = 'celiaquia/payment_close.html'

    def dispatch(self, request, pk, *args, **kwargs):
        self.expediente = get_object_or_404(Expediente, pk=pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        data = form.cleaned_data
        ExpedienteService.close_payment(
            self.expediente,
            usuario       = request.user,
            fecha_pago    = data['fecha_pago'],
            monto         = data['monto'],
            observaciones = data.get('observaciones', '')
        )
        messages.success(self.request, "Pago cerrado correctamente.")
        return redirect('expediente_detail', pk=self.expediente.pk)
