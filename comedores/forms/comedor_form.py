import re
from django import forms
from django.core.exceptions import ValidationError


from ciudadanos.models import Ciudadano
from comedores.models import (
    Comedor,
    Referente,
    ImagenComedor,
    Nomina,
)

from configuraciones.models import Municipio, Provincia
from configuraciones.models import Localidad


class ReferenteForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        comedor_id = kwargs.pop("comedor_pk", None)
        if comedor_id:
            comedor = Comedor.objects.get(pk=comedor_id)

            self.fields["referente_nombre"].initial = comedor.referente.nombre
            self.fields["referente_apellido"].initial = comedor.referente.apellido
            self.fields["referente_mail"].initial = comedor.referente.mail
            self.fields["referente_celular"].initial = comedor.referente.celular
            self.fields["referente_documento"].initial = comedor.referente.documento
            self.fields["referente_funcion"].initial = comedor.referente.funcion

    def clean_mail(self):
        mail = self.cleaned_data.get("mail")
        if not mail:
            return mail

        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not isinstance(mail, str):
            raise ValidationError("El correo electrónico debe ser una cadena válida.")
        if not re.match(email_regex, mail):
            raise ValidationError("Por favor, ingresa un correo electrónico válido.")
        return mail

    class Meta:
        model = Referente
        fields = "__all__"


class NominaForm(forms.ModelForm):
    ciudadano = forms.ModelChoiceField(
        queryset=Ciudadano.objects.all(),
        label="Ciudadano",
        widget=forms.Select(attrs={"class": "form-control select2"}),
        help_text="Selecciona un ciudadano del legajo",
    )

    class Meta:
        model = Nomina
        fields = ["ciudadano", "estado", "observaciones"]
        widgets = {
            "estado": forms.Select(attrs={"class": "form-control"}),
            "observaciones": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class ComedorForm(forms.ModelForm):

    comienzo = forms.IntegerField(min_value=1900, required=False)
    longitud = forms.FloatField(min_value=-180, max_value=180, required=False)
    latitud = forms.FloatField(min_value=-90, max_value=90, required=False)
    codigo_postal = forms.IntegerField(min_value=1000, max_value=999999, required=False)
    codigo_de_proyecto = forms.CharField(max_length=7, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.popular_campos_ubicacion()

    def popular_campos_ubicacion(self):

        def pk_formatter(value):
            return int(value) if value and value.isdigit() else None

        provincia = Provincia.objects.filter(
            pk=pk_formatter(self.data.get("provincia"))
        ).first() or getattr(self.instance, "provincia", None)

        municipio = Municipio.objects.filter(
            pk=pk_formatter(self.data.get("municipio"))
        ).first() or getattr(self.instance, "municipio", None)

        localidad = Localidad.objects.filter(
            pk=pk_formatter(self.data.get("localidad"))
        ).first() or getattr(self.instance, "localidad", None)

        if provincia:
            self.fields["provincia"].initial = Provincia.objects.get(id=provincia.id)
            self.fields["provincia"].queryset = Provincia.objects.all()
            self.fields["municipio"].queryset = Municipio.objects.filter(
                provincia=provincia
            )
        else:
            self.fields["provincia"].queryset = Provincia.objects.all()
            self.fields["municipio"].queryset = Municipio.objects.none()
            self.fields["localidad"].queryset = Localidad.objects.none()

        if municipio:
            self.fields["municipio"].initial = municipio
            self.fields["localidad"].queryset = Localidad.objects.filter(
                municipio=municipio
            )

        if localidad:
            self.fields["localidad"].initial = localidad

    class Meta:
        model = Comedor
        fields = "__all__"

        labels = {
            "tipocomedor": "Tipo comedor",
        }


class ImagenComedorForm(forms.ModelForm):
    class Meta:
        model = ImagenComedor
        fields = "__all__"
