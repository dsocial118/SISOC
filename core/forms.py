from django import forms
from core.models import MontoPrestacionPrograma, Programa


class MontoPrestacionProgramaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["programa"].queryset = Programa.objects.order_by("nombre")

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
            "programa": forms.Select(attrs={"class": "form-control"}),
            "desayuno_valor": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
            "almuerzo_valor": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
            "merienda_valor": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
            "cena_valor": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
        }
