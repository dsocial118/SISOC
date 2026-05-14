from django import forms

from centrodeinfancia.models import ObservacionCentroInfancia


class ObservacionCentroInfanciaForm(forms.ModelForm):
    class Meta:
        model = ObservacionCentroInfancia
        fields = ["observacion"]
        labels = {"observacion": "Observación"}
        widgets = {
            "observacion": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Describa la observación",
                }
            )
        }
