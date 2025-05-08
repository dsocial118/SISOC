from django import forms

from organizaciones.models import Organizacion, FirmanteHecho, FirmanteEclesiastica, FirmanteJuridica


class OrganizacionForm(forms.ModelForm):
    class Meta:
        model = Organizacion
        fields = "__all__"

class OrganizacionJuridicaForm(forms.ModelForm):
    class Meta:
        model = FirmanteJuridica 
        fields = "__all__"

class OrganizacionEclesiasticaForm(forms.ModelForm):
    class Meta:
        model = FirmanteEclesiastica
        fields = "__all__"


class OrganizacionHechoForm(forms.ModelForm):
    class Meta:
        model = FirmanteHecho
        fields = "__all__"
        labels = {
            "firmante1": "Firmante 1",
            "firmante2": "Firmante 2",
            "aval1": "Aval 1",
            "cuitaval1": "CUIT Aval 1",
            "aval2": "Aval 2",
            "cuitaval2": "CUIT Aval 2",
        }