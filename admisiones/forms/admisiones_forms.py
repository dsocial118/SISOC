from django import forms

from comedores.models.comedor import (
    Admisiones,
    DuplaContacto,
)


class AdmisionesForm(forms.ModelForm):
    class Meta:
        model = Admisiones
        fields = "__all__"


class DuplaContactoForm(forms.ModelForm):
    class Meta:
        model = DuplaContacto
        fields = "__all__"