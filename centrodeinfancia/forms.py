from django import forms

from ciudadanos.models import Ciudadano
from centrodeinfancia.models import (
    CentroDeInfancia,
    IntervencionCentroInfancia,
    NominaCentroInfancia,
)


class CentroDeInfanciaForm(forms.ModelForm):
    class Meta:
        model = CentroDeInfancia
        fields = ["nombre", "organizacion"]


class NominaCentroInfanciaForm(forms.ModelForm):
    class Meta:
        model = NominaCentroInfancia
        fields = ["estado", "observaciones"]
        widgets = {
            "observaciones": forms.Textarea(attrs={"rows": 3}),
        }


class NominaCentroInfanciaCreateForm(forms.ModelForm):
    ciudadano = forms.ModelChoiceField(
        queryset=Ciudadano.objects.all().order_by("apellido", "nombre"),
        empty_label="Seleccione un ciudadano",
    )

    class Meta:
        model = NominaCentroInfancia
        fields = ["ciudadano", "estado", "observaciones"]
        widgets = {
            "observaciones": forms.Textarea(attrs={"rows": 3}),
        }


class IntervencionCentroInfanciaForm(forms.ModelForm):
    class Meta:
        model = IntervencionCentroInfancia
        fields = [
            "tipo_intervencion",
            "subintervencion",
            "destinatario",
            "fecha",
            "forma_contacto",
            "observaciones",
            "tiene_documentacion",
            "documentacion",
        ]
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date"}),
            "observaciones": forms.Textarea(attrs={"rows": 4}),
        }
