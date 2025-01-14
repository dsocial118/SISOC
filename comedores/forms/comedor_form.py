from django import forms


from comedores.models import Comedor, Referente, Intervencion, ImagenComedor, Nomina

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
            "fk_subintervencion": forms.Select(
                attrs={"class": "select2 subintervencion-select"}
            ),
            "fk_tipo_intervencion": forms.Select(
                attrs={"class": "select2 tipo_intervencion-select"}
            ),
        }
        labels = {
            "detalles": "Detalles de la intervención",
            "fk_subintervencion": "Subintervención",
            "fk_tipo_intervencion": "Tipo de intervención",
            "fk_estado": "Estado",
            "fk_direccion": "Dirección",
        }


class NominaForm(forms.ModelForm):
    class Meta:
        model = Nomina
        fields = "__all__"
        widgets = {
            "detalles": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
        }
        labels = {
            "fk_estado": "Estado",
            "nombre": "Nombre",
            "apellido": "Apellido",
            "dni": "Dni",
            "fk_sexo": "Sexo",
        }


class ComedorForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.popular_campos_ubicacion()

    def popular_campos_ubicacion(self):
        provincia = Provincia.objects.filter(
            pk=self.data.get("provincia")
        ).first() or getattr(self.instance, "provincia", None)
        municipio = Municipio.objects.filter(
            pk=self.data.get("municipio")
        ).first() or getattr(self.instance, "municipio", None)
        localidad = Localidad.objects.filter(
            pk=self.data.get("localidad")
        ).first() or getattr(self.instance, "localidad", None)

        if provincia:
            self.fields["provincia"].initial = Provincia.objects.get(id=provincia.id)
            self.fields["provincia"].queryset = Provincia.objects.all()
            self.fields["municipio"].queryset = Municipio.objects.filter(
                fk_provincia=provincia
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
                fk_municipio=municipio
            )

        if localidad:
            self.fields["localidad"].initial = localidad

    class Meta:
        model = Comedor
        fields = "__all__"


class ImagenComedorForm(forms.ModelForm):
    class Meta:
        model = ImagenComedor
        fields = "__all__"
