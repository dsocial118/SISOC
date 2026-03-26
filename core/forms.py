from django import forms

from core.models import MontoPrestacionPrograma, Programa


class ProgramaForm(forms.ModelForm):
    class Meta:
        model = Programa
        fields = ["nombre", "estado", "observaciones", "organismo", "descripcion"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "estado": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "observaciones": forms.TextInput(attrs={"class": "form-control"}),
            "organismo": forms.Select(attrs={"class": "form-control"}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


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


class TrashFilterForm(forms.Form):
    """Filtros del listado global de papelera."""

    model = forms.ChoiceField(
        label="Modelo",
        required=False,
        choices=(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    q = forms.CharField(
        label="Búsqueda",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "ID o texto",
            }
        ),
    )
    deleted_by = forms.CharField(
        label="Eliminado por",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Usuario o nombre",
            }
        ),
    )
    deleted_from = forms.DateField(
        label="Desde",
        required=False,
        input_formats=["%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"],
        widget=forms.DateInput(
            attrs={
                "class": "form-control",
                "type": "date",
            },
            format="%Y-%m-%d",
        ),
    )
    deleted_to = forms.DateField(
        label="Hasta",
        required=False,
        input_formats=["%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"],
        widget=forms.DateInput(
            attrs={
                "class": "form-control",
                "type": "date",
            },
            format="%Y-%m-%d",
        ),
    )

    def __init__(self, *args, **kwargs):
        model_choices = kwargs.pop("model_choices", ())
        super().__init__(*args, **kwargs)
        all_choices = [("", "Todos los modelos")]
        all_choices.extend(model_choices)
        self.fields["model"].choices = all_choices

    def clean(self):
        cleaned_data = super().clean()
        deleted_from = cleaned_data.get("deleted_from")
        deleted_to = cleaned_data.get("deleted_to")
        if deleted_from and deleted_to and deleted_from > deleted_to:
            raise forms.ValidationError(
                "La fecha 'Desde' no puede ser posterior a la fecha 'Hasta'."
            )
        return cleaned_data
