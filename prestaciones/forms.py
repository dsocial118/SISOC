from django import forms
from prestaciones.models import Prestacion


class PrestacionForm(forms.ModelForm):
    class Meta:
        model = Prestacion
        fields = [
            "programa",
            "desayuno_valor",
            "almuerzo_valor",
            "merienda_valor",
            "cena_valor",
        ]
        widgets = {
            "programa": forms.TextInput(attrs={"class": "form-control"}),
            "desayuno_valor": forms.NumberInput(attrs={"class": "form-control"}),
            "almuerzo_valor": forms.NumberInput(attrs={"class": "form-control"}),
            "merienda_valor": forms.NumberInput(attrs={"class": "form-control"}),
            "cena_valor": forms.NumberInput(attrs={"class": "form-control"}),
        }
