from django import forms
from django.core.exceptions import ValidationError
from .models import Centro, ActividadCentro, ParticipanteActividad

from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from centrodefamilia.models import Centro


class CentroForm(forms.ModelForm):
    class Meta:
        model = Centro
        fields = [
            "nombre",
            "direccion",
            "contacto",
            "tipo",
            "activo",
            "faro_asociado",
            "referente",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo usuarios que estén en el grupo 'ReferenteCentro'
        self.fields["referente"].queryset = User.objects.filter(
            groups__name="ReferenteCentro"
        )

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get("tipo")
        faro_asociado = cleaned_data.get("faro_asociado")

        if tipo == "adherido" and not faro_asociado:
            raise ValidationError(
                "Debe asociar un Centro FARO activo si el centro es ADHERIDO."
            )
        if tipo == "faro" and faro_asociado:
            raise ValidationError("Un Centro FARO no puede tener un FARO asociado.")

        return cleaned_data


class ActividadCentroForm(forms.ModelForm):
    class Meta:
        model = ActividadCentro
        fields = ["actividad", "cantidad_personas", "dias", "horarios", "estado"]
        exclude = ["centro"]


class ParticipanteActividadForm(forms.ModelForm):
    class Meta:
        model = ParticipanteActividad
        fields = [
            "actividad_centro",
            "nombre",
            "apellido",
            "dni",
            "edad",
            "genero",
            "cuit",
        ]

    def clean_cuit(self):
        cuit = self.cleaned_data["cuit"]
        if not cuit.isdigit() or len(cuit) not in [10, 11]:
            raise ValidationError("El CUIT debe tener entre 10 y 11 dígitos numéricos.")
        return cuit

    def clean(self):
        cleaned_data = super().clean()
        actividad = cleaned_data.get("actividad_centro")
        cuit = cleaned_data.get("cuit")

        if actividad and cuit:
            if ParticipanteActividad.objects.filter(
                actividad_centro=actividad, cuit=cuit
            ).exists():
                raise ValidationError(
                    "Este CUIT ya está registrado para esta actividad."
                )

        return cleaned_data
