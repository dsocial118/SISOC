from django import forms
from django.core.exceptions import ValidationError

from .models import Dispositivo

class DispositivoForm(forms.ModelForm):
    class Meta:
        model = Dispositivo
        fields = ['nombre', 'descripcion']

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if Dispositivo.objects.filter(nombre=nombre).exists():
            raise ValidationError("Ya existe un dispositivo con este nombre.")
        return nombre

