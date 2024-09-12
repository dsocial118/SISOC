from datetime import date

from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator

from legajos.models import (
    CHOICE_ESTADO_RELACION,
    CHOICE_SINO,
    CHOICE_VINCULO_FAMILIAR,
    LegajoGrupoFamiliar,
    Legajos,
)


class LegajoGrupoFamiliarForm(forms.ModelForm):
    class Meta:
        model = LegajoGrupoFamiliar
        fields = "__all__"


class NuevoLegajoFamiliarForm(forms.ModelForm):
    vinculo = forms.ChoiceField(choices=CHOICE_VINCULO_FAMILIAR, required=True)
    estado_relacion = forms.ChoiceField(choices=CHOICE_ESTADO_RELACION, required=True)
    conviven = forms.ChoiceField(choices=CHOICE_SINO, required=True)
    cuidador_principal = forms.ChoiceField(choices=CHOICE_SINO, required=True)
    documento = forms.IntegerField(
        required=False,
        validators=[MinValueValidator(3000000), MaxValueValidator(100000000)],
        widget=forms.NumberInput(),
    )

    class Meta:
        model = Legajos
        fields = [
            "apellido",
            "nombre",
            "fecha_nacimiento",
            "tipo_doc",
            "documento",
            "sexo",
            "vinculo",
            "estado_relacion",
            "conviven",
            "cuidador_principal",
        ]
        widgets = {
            "fecha_nacimiento": forms.DateInput(
                attrs={"type": "date"}, format="%Y-%m-%d"
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        tipo_doc = cleaned_data.get("tipo_doc")
        documento = cleaned_data.get("documento")
        fecha_nacimiento = cleaned_data.get("fecha_nacimiento")

        # Validación de campo único, combinación de DNI + Tipo DNI
        if Legajos.objects.filter(tipo_doc=tipo_doc, documento=documento).exists():
            self.add_error(
                "documento", "Ya existe un legajo con ese TIPO y NÚMERO de documento."
            )

        # Validación de fecha de nacimiento
        if fecha_nacimiento:
            if not isinstance(fecha_nacimiento, date):
                self.add_error(
                    "fecha_nacimiento",
                    "La fecha de nacimiento debe ser una fecha válida.",
                )
            elif fecha_nacimiento > date.today():
                self.add_error(
                    "fecha_nacimiento",
                    "La fecha de nacimiento debe ser menor o igual al día de hoy.",
                )

        return cleaned_data
