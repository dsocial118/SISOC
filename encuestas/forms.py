from django import forms

from .models import Encuesta


class EncuestaForm(forms.ModelForm):
    class Meta:
        model = Encuesta
        fields = [
            "titulo",
            "descripcion",
            "es_anonima",
            "es_obligatoria",
            "intervalo_recordatorio_dias",
            "es_recurrente",
            "intervalo_recurrencia_dias",
            "duracion_ronda_dias",
        ]
        widgets = {
            "titulo": forms.TextInput(attrs={"class": "form-control"}),
            "descripcion": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "es_anonima": forms.CheckboxInput(
                attrs={"class": "form-check-input", "role": "switch"}
            ),
            "es_obligatoria": forms.CheckboxInput(
                attrs={"class": "form-check-input", "role": "switch"}
            ),
            "es_recurrente": forms.CheckboxInput(
                attrs={"class": "form-check-input", "role": "switch"}
            ),
            "intervalo_recordatorio_dias": forms.NumberInput(
                attrs={"class": "form-control"}
            ),
            "intervalo_recurrencia_dias": forms.NumberInput(
                attrs={"class": "form-control"}
            ),
            "duracion_ronda_dias": forms.NumberInput(attrs={"class": "form-control"}),
        }
