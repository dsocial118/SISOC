from django import forms

from admisiones.models.admisiones import (
    Admision,
    DuplaContacto,
    InformeTecnicoJuridico,
    InformeTecnicoBase
)


class AdmisionForm(forms.ModelForm):
    class Meta:
        model = Admision
        fields = "__all__"


class DuplaContactoForm(forms.ModelForm):
    class Meta:
        model = DuplaContacto
        fields = "__all__"

class InformeTecnicoJuridicoForm(forms.ModelForm):
    class Meta:
        model = InformeTecnicoJuridico
        exclude = ["admision", "estado"] 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True

class InformeTecnicoBaseForm(forms.ModelForm):
    class Meta:
        model = InformeTecnicoBase
        exclude = ["admision", "estado"] 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True
