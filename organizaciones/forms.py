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
        fields = ["nombre", "rol", "cuit"]

    def clean(self):
        cleaned_data = super().clean()
        rol = cleaned_data.get("rol")
        cuit = cleaned_data.get("cuit")

        if rol == "aval" and not cuit:
            self.add_error("cuit", "El CUIT es obligatorio para el rol Aval")


FirmanteFormset = inlineformset_factory(
    Organizacion, Firmante, form=FirmanteForm, extra=0, can_delete=True
)
