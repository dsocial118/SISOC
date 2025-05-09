from django import forms
from django.forms import inlineformset_factory
from organizaciones.models import (
    Organizacion,
    Firmante,
)

class OrganizacionForm(forms.ModelForm):
    class Meta:
        model = Organizacion
        fields = "__all__"

class FirmanteForm(forms.ModelForm):
    class Meta:
        model = Firmante
        fields = ["nombre", "rol"]

FirmanteFormset = inlineformset_factory(
    Organizacion, Firmante, form=FirmanteForm, extra=1, can_delete=True
)