from django import forms

from cdi.models import CentroDesarrolloInfantil


class CentroDesarrolloInfantilForm(forms.ModelForm):
    class Meta:
        model = CentroDesarrolloInfantil
        fields = "__all__"
        widgets = {
            "direccion": forms.TextInput(attrs={"class": "form-control"}),
            "barrio": forms.TextInput(attrs={"class": "form-control"}),
            "codigo_postal": forms.TextInput(attrs={"class": "form-control"}),
        }
