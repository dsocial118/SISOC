from django import forms
from django.forms import inlineformset_factory
from organizaciones.models import (
    Organizacion,
    Firmante,
    Aval1,
    Aval2,
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


class Aval1Form(forms.ModelForm):
    class Meta:
        model = Aval1
        fields = ["nombre", "cuit"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["nombre"].required = False
        self.fields["cuit"].required = False


class Aval2Form(forms.ModelForm):
    class Meta:
        model = Aval2
        fields = ["nombre", "cuit"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["nombre"].required = False
        self.fields["cuit"].required = False


Aval1Formset = inlineformset_factory(
    Organizacion, Aval1, form=Aval1Form, extra=1, max_num=1, can_delete=True
)
Aval2Formset = inlineformset_factory(
    Organizacion, Aval2, form=Aval2Form, extra=1, max_num=1, can_delete=True
)

FirmanteFormset = inlineformset_factory(
    Organizacion, Firmante, form=FirmanteForm, extra=0, can_delete=True
)
