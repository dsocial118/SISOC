from django import forms

from legajos.models import LegajosDerivaciones


class LegajosDerivacionesForm(forms.ModelForm):
    archivos = forms.FileField(
        widget=forms.ClearableFileInput(
            attrs={
                "multiple": True,
            }
        ),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = LegajosDerivaciones
        fields = "__all__"
        exclude = ["motivo_rechazo", "obs_rechazo", "fecha_rechazo"]
        widgets = {
            "detalles": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                }
            ),
        }
        labels = {
            "fk_legajo": "Legajo",
            "fk_organismo": "Organismo relacionado",
            "m2m_alertas": "Alertas detectadas",
            "fk_programa": "Derivar a",
            "fk_programa_solicitante": "Derivar de",
        }


class DerivacionesRechazoForm(forms.ModelForm):
    class Meta:
        model = LegajosDerivaciones
        fields = ["motivo_rechazo", "obs_rechazo", "fecha_rechazo"]
        widgets = {
            "obs_rechazo": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
        }
        labels = {
            "motivo_rechazo": "Motivo de rechazo",
            "obs_rechazo": "Observaciones",
        }
