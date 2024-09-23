from datetime import datetime
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Div, Submit, HTML

from comedores.models import Comedor
from legajos.models import LegajoLocalidad, LegajoMunicipio, LegajoProvincias


class ComedorForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.layout()

        self.popular_campos_ubicacion()

    def layout(self):
        self.helper = FormHelper()
        self.helper.form_class = "form-inline"
        self.helper.layout = Layout(
            Row(
                Div("nombre", css_class="col-sm-4"),
                Div(
                    "comienzo", css_class="col-sm-4", min=1900, max=datetime.now().year
                ),
                Div("referente", css_class="col-sm-4"),
            ),
            Row(
                Div("provincia", css_class="col-sm-4"),
                Div("municipio", css_class="col-sm-4"),
                Div("localidad", css_class="col-sm-4"),
            ),
            Row(
                Div("partido", css_class="col-sm-4"),
                Div("barrio", css_class="col-sm-4"),
                Div("codigo_postal", css_class="col-sm-4"),
            ),
            Row(
                Div("calle", css_class="col-sm-3"),
                Div("numero", css_class="col-sm-3"),
                Div("entre_calle_1", css_class="col-sm-3"),
                Div("entre_calle_2", css_class="col-sm-3"),
            ),
            Row(
                Submit("submit", "Confirmar", css_class="btn btn-primary mr-1"),
                HTML(
                    "<a class='btn btn-secondary print mr-1 d-none d-sm-inline'>Imprimir</a>"
                ),
                HTML(
                    "<a href='javascript:history.back()' class='btn btn-secondary'>Cancelar</a>"
                ),
            ),
        )

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
                codigo_ifam__startswith=provincia.abreviatura
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
                departamento_id=municipio.departamento_id
            )

        if hasattr(self.instance, "localidad"):
            self.fields["localidad"].initial = localidad

    class Meta:
        model = Comedor
        fields = "__all__"
