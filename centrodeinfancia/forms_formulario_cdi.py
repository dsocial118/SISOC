"""Forms para FormularioCDI."""

from __future__ import annotations

from django import forms
from django.core.validators import RegexValidator
from django.forms import inlineformset_factory

from core.models import Localidad, Municipio, Provincia
from centrodeinfancia.formulario_cdi_schema import (
    OPCIONES_INSTITUCIONES_ARTICULACION,
    ETIQUETAS_BOOLEANAS,
    CAMPOS_OPCIONES,
    ETIQUETAS_CAMPOS,
    SECCIONES_FORMULARIO_CDI,
    CAMPOS_OPCIONES_MULTIPLES,
    OPCIONES_GRUPO_ETARIO_SALAS,
    OPCIONES_GRUPO_ETARIO_DEMANDA,
)
from centrodeinfancia.models import (
    DepartamentoIpi,
    FormularioCDI,
    FormularioCDIArticulationFrequency,
    FormularioCDIRoomDistribution,
    FormularioCDIWaitlistByAgeGroup,
)


OPCIONES_BOOLEANAS = [("", "---------"), ("true", "Si"), ("false", "No")]
TELEFONO_FORMATO_FLEXIBLE_ERROR = (
    "Ingrese un teléfono válido: solo números o grupos numéricos separados por guiones."
)
TELEFONO_FORMATO_FLEXIBLE_VALIDATOR = RegexValidator(
    regex=r"^\d+(?:-\d+)*$",
    message=TELEFONO_FORMATO_FLEXIBLE_ERROR,
)


def construir_filas_iniciales_fijas(options, key_name):
    return [{key_name: option[0]} for option in options]


class CampoBooleanoNulable(forms.TypedChoiceField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("choices", OPCIONES_BOOLEANAS)
        kwargs.setdefault("required", False)
        kwargs.setdefault(
            "coerce",
            lambda value: (
                True
                if value in (True, "true", "True", "1", 1)
                else False if value in (False, "false", "False", "0", 0) else None
            ),
        )
        super().__init__(*args, **kwargs)


class FormularioCDIForm(forms.ModelForm):
    meses_funcionamiento = forms.MultipleChoiceField(
        required=False,
        choices=CAMPOS_OPCIONES_MULTIPLES["meses_funcionamiento"],
        widget=forms.CheckboxSelectMultiple,
    )
    dias_funcionamiento = forms.MultipleChoiceField(
        required=False,
        choices=CAMPOS_OPCIONES_MULTIPLES["dias_funcionamiento"],
        widget=forms.CheckboxSelectMultiple,
    )
    items_protocolo_salud = forms.MultipleChoiceField(
        required=False,
        choices=CAMPOS_OPCIONES_MULTIPLES["items_protocolo_salud"],
        widget=forms.CheckboxSelectMultiple,
    )
    prestaciones_alimentarias = forms.MultipleChoiceField(
        required=False,
        choices=CAMPOS_OPCIONES_MULTIPLES["prestaciones_alimentarias"],
        widget=forms.CheckboxSelectMultiple,
    )
    uso_exclusivo_espacio = CampoBooleanoNulable(
        choices=[
            ("", "---------"),
            ("true", "Sí"),
            ("false", ETIQUETAS_BOOLEANAS["uso_exclusivo_espacio"][1]),
        ]
    )
    tiene_extintores_vigentes = CampoBooleanoNulable()
    tiene_computadora_funcionando = CampoBooleanoNulable()
    tiene_instrumento_priorizacion_ingreso = CampoBooleanoNulable()

    class Meta:
        model = FormularioCDI
        exclude = (
            "centro",
            "source_form_version",
            "created_at",
            "updated_at",
            "created_by",
            "deleted_at",
            "deleted_by",
        )
        labels = ETIQUETAS_CAMPOS
        widgets = {
            "fecha_relevamiento": forms.DateInput(attrs={"type": "date"}),
            "horario_apertura": forms.TimeInput(attrs={"type": "time"}),
            "horario_cierre": forms.TimeInput(attrs={"type": "time"}),
            "nombre_completo_respondente": forms.TextInput(attrs={"maxlength": 255}),
            "rol_respondente": forms.TextInput(attrs={"maxlength": 255}),
            "codigo_cdi": forms.TextInput(attrs={"readonly": "readonly"}),
        }

    definiciones_secciones = SECCIONES_FORMULARIO_CDI
    phone_field_names = (
        "telefono_cdi",
        "telefono_referente_cdi",
        "telefono_organizacion",
        "telefono_referente_organizacion",
    )

    @staticmethod
    def _parsear_pk(value):
        if hasattr(value, "pk"):
            return value.pk
        return int(value) if value and str(value).isdigit() else None

    def _obtener_valor_enlazado_o_inicial(self, field_name, instance_value=None):
        if self.is_bound:
            bound_value = self.data.get(self.add_prefix(field_name))
            if bound_value not in (None, ""):
                return bound_value
        initial_value = self.initial.get(field_name)
        if initial_value not in (None, ""):
            return initial_value
        return instance_value

    def _configurar_grupo_geo(self, sufijo):
        province_field = f"provincia_{sufijo}"
        department_field = f"departamento_{sufijo}"
        municipality_field = f"municipio_{sufijo}"
        locality_field = f"localidad_{sufijo}"

        province_instance = getattr(self.instance, province_field, None)
        department_instance = getattr(self.instance, department_field, None)
        municipality_instance = getattr(self.instance, municipality_field, None)
        locality_instance = getattr(self.instance, locality_field, None)

        province_value = self._obtener_valor_enlazado_o_inicial(
            province_field, province_instance
        )
        department_value = self._obtener_valor_enlazado_o_inicial(
            department_field, department_instance
        )
        municipality_value = self._obtener_valor_enlazado_o_inicial(
            municipality_field, municipality_instance
        )
        locality_value = self._obtener_valor_enlazado_o_inicial(
            locality_field, locality_instance
        )

        province = Provincia.objects.filter(pk=self._parsear_pk(province_value)).first()
        department = DepartamentoIpi.objects.filter(
            pk=self._parsear_pk(department_value)
        ).first()
        municipality = Municipio.objects.filter(
            pk=self._parsear_pk(municipality_value)
        ).first()
        locality = Localidad.objects.filter(pk=self._parsear_pk(locality_value)).first()

        self.fields[province_field].queryset = Provincia.objects.all().order_by(
            "nombre"
        )
        self.fields[department_field].queryset = (
            DepartamentoIpi.objects.filter(provincia=province).order_by("nombre")
            if province
            else DepartamentoIpi.objects.none()
        )
        self.fields[municipality_field].queryset = (
            Municipio.objects.filter(provincia=province).order_by("nombre")
            if province
            else Municipio.objects.none()
        )
        self.fields[locality_field].queryset = (
            Localidad.objects.filter(municipio=municipality).order_by("nombre")
            if municipality
            else Localidad.objects.none()
        )

        if province:
            self.fields[province_field].initial = province
        if department:
            self.fields[department_field].initial = department
        if municipality:
            self.fields[municipality_field].initial = municipality
        if locality:
            self.fields[locality_field].initial = locality

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["codigo_cdi"].disabled = True
        self._configurar_grupo_geo("cdi")
        self._configurar_grupo_geo("organizacion")
        self._aplicar_validacion_flexible_telefonos()

        for field_name, options in CAMPOS_OPCIONES.items():
            if field_name in self.fields:
                self.fields[field_name].choices = [("", "---------"), *options]

        for field_name, label in ETIQUETAS_CAMPOS.items():
            if field_name in self.fields:
                self.fields[field_name].label = label

        for field_name in self.fields:
            field = self.fields[field_name]
            existing = field.widget.attrs.get("class", "")
            if isinstance(field.widget, forms.CheckboxSelectMultiple):
                field.widget.attrs["class"] = f"{existing} form-check-input".strip()
                continue
            widget_class = (
                "form-select"
                if isinstance(
                    field.widget,
                    (forms.Select, forms.SelectMultiple),
                )
                else "form-control"
            )
            field.widget.attrs["class"] = f"{existing} {widget_class}".strip()

    def _aplicar_validacion_flexible_telefonos(self):
        for field_name in self.phone_field_names:
            if field_name not in self.fields:
                continue
            field = self.fields[field_name]
            field.validators = [TELEFONO_FORMATO_FLEXIBLE_VALIDATOR]
            field.widget.attrs["inputmode"] = "tel"
            field.widget.attrs["pattern"] = r"\d+(?:-\d+)*"

    def clean(self):
        cleaned_data = super().clean()
        meals = cleaned_data.get("prestaciones_alimentarias") or []

        # Los campos ocultos por la UI no deben bloquear el guardado si
        # quedaron con valores residuales de una interacción previa.
        if cleaned_data.get("tipo_jornada") != "other":
            cleaned_data["tipo_jornada_otra"] = ""

        if cleaned_data.get("modalidad_gestion") != "otra":
            cleaned_data["modalidad_gestion_otra"] = ""

        if cleaned_data.get("modalidad_tenencia") != "otra":
            cleaned_data["modalidad_tenencia_otra"] = ""

        if "otra" not in meals:
            cleaned_data["prestaciones_alimentarias_otra"] = ""

        if "ninguna" in meals:
            cleaned_data["calidad_elaboracion_menu"] = ""
            cleaned_data["evaluacion_periodica_menu"] = ""
            cleaned_data["cobertura_capacitacion_manipulacion_alimentos"] = ""

        if cleaned_data.get("tiene_espacio_cocina") != "si":
            cleaned_data["combustible_cocinar"] = ""

        if cleaned_data.get("tiene_espacio_exterior") != "si":
            cleaned_data["tiene_juegos_exteriores"] = ""

        if cleaned_data.get("acceso_energia") == "sin_electricidad":
            cleaned_data["seguridad_electrica"] = ""

        if self.instance and self.instance.pk:
            cleaned_data["codigo_cdi"] = self.instance.codigo_cdi

        return cleaned_data


class MezclaEtiquetaFilaFija:
    campo_codigo_fila = ""
    opciones_fila = ()

    @property
    def etiqueta_fila(self):
        option_map = dict(self.opciones_fila)
        initial = getattr(self, "initial", {})
        data = getattr(self, "data", {})
        add_prefix = getattr(self, "add_prefix", lambda field_name: field_name)
        value = initial.get(self.campo_codigo_fila) or data.get(
            add_prefix(self.campo_codigo_fila)
        )
        return option_map.get(value, value)


class FormularioCDIDistribucionSalasForm(MezclaEtiquetaFilaFija, forms.ModelForm):
    campo_codigo_fila = "grupo_etario"
    opciones_fila = OPCIONES_GRUPO_ETARIO_SALAS

    class Meta:
        model = FormularioCDIRoomDistribution
        fields = [
            "grupo_etario",
            "cantidad_salas",
            "superficie_exclusiva_m2",
            "cantidad_ninos",
            "cantidad_personal_sala",
        ]
        widgets = {
            "grupo_etario": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in [
            "cantidad_salas",
            "superficie_exclusiva_m2",
            "cantidad_ninos",
            "cantidad_personal_sala",
        ]:
            self.fields[field_name].required = False
            self.fields[field_name].widget.attrs["class"] = "form-control"


class FormularioCDIDemandaInsatisfechaGrupoEtarioForm(
    MezclaEtiquetaFilaFija, forms.ModelForm
):
    campo_codigo_fila = "grupo_etario"
    opciones_fila = OPCIONES_GRUPO_ETARIO_DEMANDA

    class Meta:
        model = FormularioCDIWaitlistByAgeGroup
        fields = ["grupo_etario", "cantidad_demanda_insatisfecha"]
        widgets = {
            "grupo_etario": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cantidad_demanda_insatisfecha"].required = False
        self.fields["cantidad_demanda_insatisfecha"].widget.attrs[
            "class"
        ] = "form-control"


class FormularioCDIArticulacionFrecuenciaForm(MezclaEtiquetaFilaFija, forms.ModelForm):
    campo_codigo_fila = "tipo_institucion"
    opciones_fila = OPCIONES_INSTITUCIONES_ARTICULACION

    class Meta:
        model = FormularioCDIArticulationFrequency
        fields = ["tipo_institucion", "frecuencia"]
        widgets = {
            "tipo_institucion": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["frecuencia"].required = False
        self.fields["frecuencia"].widget.attrs["class"] = "form-select"


def construir_clase_formset_distribucion_salas(extra=0):
    return inlineformset_factory(
        FormularioCDI,
        FormularioCDIRoomDistribution,
        form=FormularioCDIDistribucionSalasForm,
        extra=extra,
        can_delete=False,
    )


def construir_clase_formset_demanda_insatisfecha(extra=0):
    return inlineformset_factory(
        FormularioCDI,
        FormularioCDIWaitlistByAgeGroup,
        form=FormularioCDIDemandaInsatisfechaGrupoEtarioForm,
        extra=extra,
        can_delete=False,
    )


def construir_clase_formset_articulacion(extra=0):
    return inlineformset_factory(
        FormularioCDI,
        FormularioCDIArticulationFrequency,
        form=FormularioCDIArticulacionFrecuenciaForm,
        extra=extra,
        can_delete=False,
    )
