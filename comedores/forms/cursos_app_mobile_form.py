from django import forms

from comedores.models import CursoAppMobile


class CursoAppMobileForm(forms.ModelForm):
    programa_objetivo = forms.ChoiceField(
        required=True,
        choices=(("", "Seleccionar programa"),) + CursoAppMobile.PROGRAMA_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    class Meta:
        model = CursoAppMobile
        fields = [
            "nombre",
            "link",
            "imagen",
            "descripcion",
            "programa_objetivo",
            "es_recomendado",
            "orden",
            "activo",
        ]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "link": forms.URLInput(attrs={"class": "form-control"}),
            "imagen": forms.FileInput(attrs={"class": "form-control"}),
            "descripcion": forms.TextInput(attrs={"class": "form-control"}),
            "es_recomendado": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "orden": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["nombre"].required = True
        self.fields["link"].required = True
        self.fields["programa_objetivo"].required = True
