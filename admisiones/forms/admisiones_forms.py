from django import forms

from admisiones.models.admisiones import (
    Admision,
    DuplaContacto,
)


class AdmisionForm(forms.ModelForm):
    class Meta:
        model = Admision
        fields = "__all__"


class DuplaContactoForm(forms.ModelForm):
    class Meta:
        model = DuplaContacto
        fields = "__all__"
