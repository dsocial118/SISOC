# intervenciones/forms.py
from django import forms
from intervenciones.models.intervenciones import (
    Intervencion,
)  # Adjust the import path if necessary

from django import forms
from intervenciones.models.intervenciones import Intervencion


class IntervencionForm(forms.ModelForm):
    class Meta:
        model = Intervencion
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
            "fecha": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        }
        labels = {
            "tipo_intervencion": "Tipo de Intervención",
            "subintervencion": "Subtipo de Intervención",
            "destinatario": "Destinatario",
            "fecha": "Fecha",
            "forma_contacto": "Forma de Contacto",
            "observaciones": "Descripción",
            "tiene_documentacion": "Documentación Adjunta",
            "documentacion": "Cargar Documentación",
        }
