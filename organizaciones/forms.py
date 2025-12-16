from django import forms
from django.forms import inlineformset_factory
from organizaciones.models import (
    Organizacion,
    Firmante,
    Aval,
)
from core.models import Municipio, Provincia, Localidad


class OrganizacionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Asegura que el campo date cargue el valor previo (almacenado como DateTime)
        fecha_vencimiento = getattr(self.instance, "fecha_vencimiento", None)
        if not self.is_bound and fecha_vencimiento:
            self.initial["fecha_vencimiento"] = fecha_vencimiento.date()
        self.fields["fecha_vencimiento"].input_formats = ["%Y-%m-%d"]

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
        model = Organizacion
        fields = "__all__"
        widgets = {
            "fecha_vencimiento": forms.DateInput(
                attrs={"type": "date", "class": "form-control"},
                format="%Y-%m-%d",
            ),
        }


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


class AvalForm(forms.ModelForm):
    class Meta:
        model = Aval
        fields = ["nombre", "cuit"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["nombre"].required = False
        self.fields["cuit"].required = False


AvalFormset = inlineformset_factory(
    Organizacion, Aval, form=AvalForm, extra=1, max_num=1, can_delete=True
)
FirmanteFormset = inlineformset_factory(
    Organizacion, Firmante, form=FirmanteForm, extra=0, can_delete=True
)
