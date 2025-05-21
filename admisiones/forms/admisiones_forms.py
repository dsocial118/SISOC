from django import forms

from admisiones.models.admisiones import (
    Admision,
    InformeTecnicoJuridico,
    InformeTecnicoBase,
    FormularioRESO,
    FormularioProyectoDeConvenio,   
    DocumentosExpediente, 
)


class AdmisionForm(forms.ModelForm):
    class Meta:
        model = Admision
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

class CaratularForm(forms.ModelForm):

    num_expediente = forms.CharField(required=True, label="Número de Expediente")
    num_if = forms.CharField(required=True, label="Número de IF")

    class Meta:
        model = Admision
        fields = ["num_expediente", "num_if"]

class LegalesRectificarForm(forms.ModelForm):
    class Meta:
        model = Admision
        fields = ["observaciones"]
        widgets = {
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Detalle sus observaciones.',
                'rows': 4
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True

class ResoForm(forms.ModelForm):
    class Meta:
        model = FormularioRESO
        exclude = ["admision", "creado", "creado_por"] 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True

class ProyectoConvenioForm(forms.ModelForm):
    class Meta:
        model = FormularioProyectoDeConvenio
        exclude = ["admision", "creado", "creado_por"] 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True

class LegalesNumIFForm(forms.ModelForm):
    class Meta:
        model = Admision
        fields = ["legales_num_if"]
        labels = {
            "legales_num_if":"Numero IF",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True

class DocumentosExpedienteForm(forms.ModelForm):
    class Meta:
        model = DocumentosExpediente
        fields = ["value", "tipo"]
        labels = {
            "value":"",
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True