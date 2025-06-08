from django import forms
from .models import ActividadCentro, ParticipanteActividad, Actividad
from centrodefamilia.services.participante_service import validar_cuit

class ActividadCentroForm(forms.ModelForm):
    class Meta:
        model = ActividadCentro
        fields = ['actividad', 'cantidad_personas', 'dias', 'horarios']

    def __init__(self, *args, **kwargs):
        centro = kwargs.pop('centro', None)
        super().__init__(*args, **kwargs)
        if centro:
            self.fields['actividad'].queryset = Actividad.objects.all()
        self.fields['dias'].widget = forms.TextInput(attrs={'placeholder': 'Ej: Lunes, Miércoles, Viernes'})
        self.fields['horarios'].widget = forms.TextInput(attrs={'placeholder': 'Ej: 10:00 a 12:00'})

class ParticipanteActividadForm(forms.ModelForm):
    class Meta:
        model = ParticipanteActividad
        fields = ['cuit']

    def clean_cuit(self):
        cuit = self.cleaned_data['cuit']
        if not validar_cuit(cuit):
            raise forms.ValidationError("El CUIT ingresado no es válido.")
        return cuit
