from django import forms
from .models import Expediente, PersonaFormulario, ArchivoCruce, InformePago

class ExpedienteForm(forms.ModelForm):
    class Meta:
        model = Expediente
        fields = ['provincia', 'observaciones']


class PersonaFormularioForm(forms.ModelForm):
    class Meta:
        model = PersonaFormulario
        fields = ['nombre', 'apellido', 'dni', 'sexo', 'fecha_nacimiento', 'datos_complementarios']


class ArchivoCruceForm(forms.ModelForm):
    class Meta:
        model = ArchivoCruce
        fields = ['archivo', 'organismo', 'tipo']


class InformePagoForm(forms.ModelForm):
    class Meta:
        model = InformePago
        fields = ['fecha_pago', 'monto', 'observaciones']
