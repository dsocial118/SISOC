from django import forms
from datetime import date
from .models import *


class Provincias_DatosForm(forms.ModelForm):
    class Meta:
        model = Provincias_Datos
        fields = '__all__'