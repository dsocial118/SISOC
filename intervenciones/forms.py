from django import forms
from django.core.exceptions import ValidationError
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

    def clean_fecha(self):
        """Validar que la fecha esté entre los años 2000 y 2100."""
        fecha = self.cleaned_data.get("fecha")

        if fecha:
            anio = fecha.year

            if anio < 2000:
                raise ValidationError(
                    "El año de la fecha debe ser mayor o igual a 2000."
                )

            if anio > 2100:
                raise ValidationError(
                    "El año de la fecha debe ser menor o igual a 2100."
                )

        return fecha
