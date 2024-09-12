#############HOGAR###########


from datetime import date

from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator

from legajos.models import CHOICE_VINCULO_FAMILIAR, LegajoGrupoHogar, Legajos


class LegajoGrupoHogarForm(forms.ModelForm):
    vinculo = forms.ChoiceField(choices=CHOICE_VINCULO_FAMILIAR, required=True)
    documento = forms.IntegerField(
        required=False,
        validators=[MinValueValidator(3000000), MaxValueValidator(100000000)],
        widget=forms.NumberInput(),
    )

    class Meta:
        model = LegajoGrupoHogar
        fields = ["vinculo", "documento", "estado_relacion"]
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
        print(
            fecha_nacimiento > date.today(), "--------------*********-----------------"
        )

        # Validación de campo unico, combinación de DNI + Tipo DNI
        if Legajos.objects.filter(tipo_doc=tipo_doc, documento=documento).exists():
            self.add_error(
                "documento", "Ya existe un legajo con ese TIPO y NÚMERO de documento."
            )
        # validación de fecha de nacimiento
        if fecha_nacimiento and fecha_nacimiento > date.today():
            self.add_error(
                "fecha_nacimiento", "La fecha de termino debe ser menor al día de hoy."
            )

        return cleaned_data
