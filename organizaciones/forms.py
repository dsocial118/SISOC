from django import forms

from organizaciones.models import Organizacion


class OrganizacionForm(forms.ModelForm):
    class Meta:
        model = Organizacion
        fields = "__all__"


class OrganizacionJuridicaForm(forms.ModelForm):
    class Meta:
        model = Organizacion
        fields = [
            "firmante1",
            "firmante2",
            "firmante3",
        ]
        labels = {
            "firmante1": "Presidente",
            "firmante2": "Tesorero",
            "firmante3": "Secretario",
        }
        widgets = {
            "firmante1": forms.TextInput(attrs={"placeholder": "Presidente"}),
            "firmante2": forms.TextInput(attrs={"placeholder": "Tesorero"}),
            "firmante3": forms.TextInput(attrs={"placeholder": "Secretario"}),
        }


class OrganizacionEclesiasticaForm(forms.ModelForm):
    class Meta:
        model = Organizacion
        fields = [
            "firmante1",
            "firmante2",
            "firmante3",
        ]
        labels = {
            "firmante1": "Obispo",
            "firmante2": "Apoderado 1",
            "firmante3": "Apoderado 2",
        }
        widgets = {
            "firmante1": forms.TextInput(attrs={"placeholder": "Obispo"}),
            "firmante2": forms.TextInput(attrs={"placeholder": "Apoderado 1"}),
            "firmante3": forms.TextInput(attrs={"placeholder": "Apoderado 2"}),
        }


class OrganizacionHechoForm(forms.ModelForm):
    class Meta:
        model = Organizacion
        fields = [
            "firmante1",
            "firmante2",
            "aval1",
            "aval2",
            "cuitaval1",
            "cuitaval2",
        ]
        labels = {
            "firmante1": "Firmante 1",
            "firmante2": "Firmante 2",
            "aval1": "Aval Nro. 1",
            "aval2": "Aval Nro. 2",
            "cuitaval1": "Número de CUIT (Aval Nro. 1)",
            "cuitaval2": "Número de CUIT (Aval Nro. 2)",
        }
        widgets = {
            "firmante1": forms.TextInput(attrs={"placeholder": "Firmante 1"}),
            "firmante2": forms.TextInput(attrs={"placeholder": "Firmante 2"}),
            "aval1": forms.TextInput(attrs={"placeholder": "Aval Nro. 1"}),
            "aval2": forms.TextInput(attrs={"placeholder": "Aval Nro. 2"}),
            "cuitaval1": forms.TextInput(
                attrs={"placeholder": "Número de CUIT (Aval Nro. 1)"}
            ),
            "cuitaval2": forms.TextInput(
                attrs={"placeholder": "Número de CUIT (Aval Nro. 2)"}
            ),
        }
