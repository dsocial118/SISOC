from django import forms

from comedores.models import Observacion


class ObservacionForm(forms.ModelForm):

    class Meta:
        model = Observacion
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
