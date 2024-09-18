from datetime import datetime
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Div, Submit

from comedores.models import Comedor
from legajos.models import LegajoLocalidad, LegajoMunicipio


class ComedorForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.layout()

        self.popular_campos_ubicacion()

        self.fields["comienzo"].help_text = None

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
            Row(Submit("submit", "Crear", css_class="btn btn-primary")),
        )

    def popular_campos_ubicacion(self):
        self.fields["municipio"].queryset = (
            LegajoMunicipio.objects.none()
        )  # Evitar la carga total de las instancias
        self.fields["localidad"].queryset = (
            LegajoLocalidad.objects.none()
        )  # Evitar la carga total de las instancias

        if "municipio" in self.data:
            try:
                municipio_id = int(self.data.get("municipio"))
                self.fields["municipio"].queryset = LegajoMunicipio.objects.filter(
                    id=municipio_id
                ).order_by("nombre_region")
            except (ValueError, TypeError):
                self.fields["municipio"].queryset = LegajoMunicipio.objects.none()

        if "localidad" in self.data:
            try:
                localidad_id = int(self.data.get("localidad"))
                self.fields["localidad"].queryset = LegajoLocalidad.objects.filter(
                    id=localidad_id
                ).order_by("nombre")
            except (ValueError, TypeError):
                self.fields["localidad"].queryset = (
                    LegajoLocalidad.objects.none()
                )  # Evitar helptext innecesario

    class Meta:
        model = Comedor
        fields = "__all__"
