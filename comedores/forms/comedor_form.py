from django import forms

from comedores.models import Comedor, Referente
from configuraciones.models import Municipio, Provincias
from configuraciones.models import Localidad


class ReferenteForm(forms.ModelForm):
    class Meta:
        model = Referente
        fields = "__all__"


class ComedorForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.popular_campos_ubicacion()

    def popular_campos_ubicacion(self):
        provincia = Provincias.objects.filter(
            pk=self.data.get("provincia")
        ).first() or getattr(self.instance, "provincia", None)
        municipio = Municipio.objects.filter(
            pk=self.data.get("municipio")
        ).first() or getattr(self.instance, "municipio", None)
        localidad = Localidad.objects.filter(
            pk=self.data.get("localidad")
        ).first() or getattr(self.instance, "localidad", None)

        if provincia:
            self.fields["provincia"].initial = Provincias.objects.get(id=provincia.id)
            self.fields["provincia"].queryset = Provincias.objects.all()
            self.fields["municipio"].queryset = Municipio.objects.filter(
                fk_provincia=provincia
            )
        else:
            self.fields["provincia"].queryset = Provincias.objects.all()
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
