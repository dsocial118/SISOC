from django import forms
from django.core.exceptions import ValidationError

from intervenciones.constants import PROGRAMA_ALIASES_COMEDORES
from intervenciones.models.intervenciones import Intervencion, TipoIntervencion


class IntervencionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        selected_tipo_id = getattr(self.instance, "tipo_intervencion_id", None)
        self.fields["tipo_intervencion"].queryset = TipoIntervencion.para_programas(
            *PROGRAMA_ALIASES_COMEDORES,
            include_ids=[selected_tipo_id] if selected_tipo_id else None,
        )

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
            "tipo_intervencion": forms.Select(attrs={"class": "form-control"}),
            "subintervencion": forms.Select(attrs={"class": "form-control"}),
            "destinatario": forms.Select(attrs={"class": "form-control"}),
            "fecha": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "forma_contacto": forms.Select(attrs={"class": "form-control"}),
            "observaciones": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "documentacion": forms.FileInput(attrs={"class": "form-control"}),
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
