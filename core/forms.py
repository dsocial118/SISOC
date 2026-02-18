from django import forms
from core.models import MontoPrestacionPrograma


class MontoPrestacionProgramaForm(forms.ModelForm):
    class Meta:
        model = MontoPrestacionPrograma
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
