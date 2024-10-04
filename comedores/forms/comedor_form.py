from django import forms

from comedores.models import Comedor, Referente
from legajos.models import LegajoLocalidad, LegajoMunicipio, LegajoProvincias


class ReferenteForm(forms.ModelForm):
    class Meta:
        model = Referente
        fields = "__all__"


class ComedorForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.popular_campos_ubicacion()

    def popular_campos_ubicacion(self):
        provincia = LegajoProvincias.objects.filter(
            pk=self.data.get("provincia")
        ).first() or getattr(self.instance, "provincia", None)
        municipio = LegajoMunicipio.objects.filter(
            pk=self.data.get("municipio")
        ).first() or getattr(self.instance, "municipio", None)
        localidad = LegajoLocalidad.objects.filter(
            pk=self.data.get("localidad")
        ).first() or getattr(self.instance, "localidad", None)

        if provincia:
            self.fields["provincia"].initial = LegajoProvincias.objects.get(
                id=provincia.id
            )
            self.fields["provincia"].queryset = LegajoProvincias.objects.all()
            self.fields["municipio"].queryset = LegajoMunicipio.objects.filter(
                fk_provincia=provincia
            )
        else:
            self.fields["provincia"].queryset = LegajoProvincias.objects.all()
            self.fields["municipio"].queryset = (
                LegajoMunicipio.objects.none()
            )  # Evitar la carga total de las instancias
            self.fields["localidad"].queryset = (
                LegajoLocalidad.objects.none()
            )  # Evitar la carga total de las instancias

        if municipio:
            self.fields["municipio"].initial = municipio
            self.fields["localidad"].queryset = LegajoLocalidad.objects.filter(
                fk_municipio=municipio
            )

        if localidad:
            self.fields["localidad"].initial = localidad

    class Meta:
        model = Comedor
        fields = "__all__"
