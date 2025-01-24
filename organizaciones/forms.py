from django import forms

from organizaciones.models import Organizacion


class OrganizacionForm(forms.ModelForm):
    class Meta:
        model = Organizacion
        fields = "__all__"
