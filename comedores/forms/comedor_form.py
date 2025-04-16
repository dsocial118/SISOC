from django import forms


from comedores.models.comedor import (
    Comedor,
    Referente,
    Intervencion,
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

    class Meta:
        model = Referente
        fields = "__all__"


class IntervencionForm(forms.ModelForm):
    class Meta:
        model = Intervencion
        fields = "__all__"
        widgets = {
            "detalles": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            "subintervencion": forms.Select(
                attrs={"class": "select2 subintervencion-select"}
            ),
            "tipo_intervencion": forms.Select(
                attrs={"class": "select2 tipo_intervencion-select"}
            ),
        }
        labels = {
            "detalles": "Detalles de la intervención",
            "subintervencion": "Subintervención",
            "tipo_intervencion": "Tipo de intervención",
            "estado": "Estado",
            "direccion": "Dirección",
        }


class NominaForm(forms.ModelForm):
    class Meta:
        model = Nomina
        fields = "__all__"
        widgets = {
            "nombre": forms.TextInput(
                attrs={
                    "class": "form-control",  # Clase CSS para estilos de Bootstrap o personalizados
                    "placeholder": "Nombre",  # Placeholder para el campo
                }
            ),
            "apellido": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Apellido",
                }
            ),
            "dni": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Documento de Identidad",
                }
            ),
            "sexo": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
            "estado": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
            "detalles": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Observaciones",
                }
            ),
        }
        labels = {
            "estado": "Estado",
            "nombre": "Nombre",
            "apellido": "Apellido",
            "dni": "Documento de Identidad",
            "sexo": "Sexo",
        }


class ComedorForm(forms.ModelForm):

    comienzo = forms.IntegerField(min_value=1900, required=False)
    longitud = forms.FloatField(min_value=-180, max_value=180, required=False)
    latitud = forms.FloatField(min_value=-90, max_value=90, required=False)
    codigo_postal = forms.IntegerField(min_value=1000, max_value=999999, required=False)

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
            self.fields["municipio"].queryset = (
                Municipio.objects.none()
            )  # Evitar la carga total de las instancias
            self.fields["localidad"].queryset = (
                Localidad.objects.none()
            )  # Evitar la carga total de las instancias

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
