# intervenciones/forms.py
from django import forms
from intervenciones.models.intervenciones import Intervencion # Adjust the import path if necessary

class IntervencionForm(forms.ModelForm):
    class Meta:
        model = Intervencion
        fields = "__all__"
        widgets = {
            "detalles": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            "subintervencion": forms.Select(
                attrs={"class": "select2 subintervencion-select"}
            ),
            "tipo_intervencion": forms.Select(
                attrs={"class": "select2 tipo_intervencion-select"}
            ),
            "destinatario": forms.TextInput(attrs={"class": "form-control"}),
            "forma_contacto": forms.TextInput(attrs={"class": "form-control"}),
            "tiene_documentacion": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "detalles": "Detalles de la intervención",
            "subintervencion": "Subintervención",
            "tipo_intervencion": "Tipo de intervención",
            "estado": "Estado",
            "direccion": "Dirección",
            "destinatario": "Destinatario",
            "forma_contacto": "Forma de contacto",
            "tiene_documentacion": "Documentación adjunta",
        }