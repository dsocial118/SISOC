"""
Vistas para el flujo de Informe Cabal en el módulo Centro de Familia.

- InformeCabalUploadView: formulario de carga de expediente.
- InformeCabalPreviewView: previsualización de datos antes de procesar.
- InformeCabalProcessView: procesamiento final y creación de movimientos.
"""
from django.views.generic import FormView, View
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django import forms
from django.urls import reverse

from centrodefamilia.models import Expediente, Centro
from centrodefamilia.services.cabal_service import CabalService


class InformeCabalForm(forms.Form):
    periodo = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Periodo Informe"
    )
    archivo = forms.FileField(label="Archivo Excel")


class InformeCabalUploadView(FormView):
    form_class = InformeCabalForm
    template_name = 'centrodefamilia/informe_cabal_upload.html'

    def dispatch(self, request, *args, **kwargs):
        self.centro = get_object_or_404(Centro, pk=self.kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['centro'] = self.centro
        return context

    def form_valid(self, form):
        # Crear Expediente sin procesar aún
        expediente = Expediente.objects.create(
            centro=self.centro,
            periodo=form.cleaned_data['periodo'],
            archivo=form.cleaned_data['archivo'],
            usuario=self.request.user
        )
        # Redirigir a preview con parámetro de expediente
        url = (f"{reverse('centro_informe_cabal_preview', args=[self.centro.pk])}"
               f"?expediente={expediente.pk}")
        return redirect(url)


class InformeCabalPreviewView(View):
    template_name = 'centrodefamilia/informe_cabal_preview.html'

    def get(self, request, *args, **kwargs):
        centro = get_object_or_404(Centro, pk=self.kwargs['pk'])
        expediente_pk = request.GET.get('expediente')
        expediente = get_object_or_404(Expediente, pk=expediente_pk, centro=centro)

        # Recalcular previsualización
        validos, errores = CabalService.previsualizar_informe(expediente, expediente.archivo)

        context = {
            'centro': centro,
            'expediente': expediente,
            'validos': validos,
            'errores': errores
        }
        return render(request, self.template_name, context)


class InformeCabalProcessView(View):
    def post(self, request, *args, **kwargs):
        centro = get_object_or_404(Centro, pk=self.kwargs['pk'])
        expediente_pk = request.POST.get('expediente')
        expediente = get_object_or_404(Expediente, pk=expediente_pk, centro=centro)

        # Volver a validar y procesar
        validos, errores = CabalService.previsualizar_informe(expediente, expediente.archivo)
        CabalService.procesar_informe(expediente, validos, errores)

        messages.success(
            request,
            f"Informe Cabal procesado: {len(validos)} movimientos, {len(errores)} errores."
        )
        # Redirigir a la lista de centros o detalle
        return redirect('centro_list')
