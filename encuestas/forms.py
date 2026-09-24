from django import forms

from .models import Encuesta


class EncuestaForm(forms.ModelForm):
    modalidad = forms.ChoiceField(
        choices=[
            ("obligatoria", "Obligatoria"),
            ("opcional", "Opcional"),
            ("postergable", "Postergable"),
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
        initial="postergable",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.initial["modalidad"] = self.instance.modalidad

    def clean(self):
        cleaned = super().clean()
        modalidad = cleaned.pop("modalidad", None)
        if not modalidad:
            modalidad = (
                "obligatoria"
                if cleaned.get("es_obligatoria")
                else "opcional" if cleaned.get("es_opcional") else "postergable"
            )
        cleaned["es_obligatoria"] = modalidad == "obligatoria"
        cleaned["es_opcional"] = modalidad == "opcional"
        if modalidad != "postergable":
            cleaned["intervalo_recordatorio_dias"] = None
        return cleaned

    class Meta:
        model = Encuesta
        fields = [
            "titulo",
            "descripcion",
            "es_anonima",
            "es_obligatoria",
            "es_opcional",
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
