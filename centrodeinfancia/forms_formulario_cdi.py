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
    CAMPOS_OTRA_OPCION = (
        ("tipo_jornada", "other", "tipo_jornada_otra"),
        ("modalidad_gestion", "otra", "modalidad_gestion_otra"),
        ("modalidad_tenencia", "otra", "modalidad_tenencia_otra"),
    )
    CAMPOS_SI_NO_DEPENDIENTES = (
        ("tiene_espacio_cocina", "si", "combustible_cocinar"),
        ("tiene_espacio_exterior", "si", "tiene_juegos_exteriores"),
    )
    CAMPOS_VACIAR_SIN_PRESTACIONES = (
        "calidad_elaboracion_menu",
        "evaluacion_periodica_menu",
        "cobertura_capacitacion_manipulacion_alimentos",
    )
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
        campos = {
            "provincia": f"provincia_{sufijo}",
            "departamento": f"departamento_{sufijo}",
            "municipio": f"municipio_{sufijo}",
            "localidad": f"localidad_{sufijo}",
        }
        instancias = {
            nombre: getattr(self.instance, campo, None)
            for nombre, campo in campos.items()
        }
        valores = {
            nombre: self._obtener_valor_enlazado_o_inicial(campo, instancias[nombre])
            for nombre, campo in campos.items()
        }

        provincia = Provincia.objects.filter(
            pk=self._parsear_pk(valores["provincia"])
        ).first()
        departamento = DepartamentoIpi.objects.filter(
            pk=self._parsear_pk(valores["departamento"])
        ).first()
        municipio = Municipio.objects.filter(
            pk=self._parsear_pk(valores["municipio"])
        ).first()
        localidad = Localidad.objects.filter(
            pk=self._parsear_pk(valores["localidad"])
        ).first()

        self.fields[campos["provincia"]].queryset = Provincia.objects.all().order_by(
            "nombre"
        )
        self.fields[campos["departamento"]].queryset = (
            DepartamentoIpi.objects.filter(provincia=provincia).order_by("nombre")
            if provincia
            else DepartamentoIpi.objects.none()
        )
        self.fields[campos["municipio"]].queryset = (
            Municipio.objects.filter(provincia=provincia).order_by("nombre")
            if provincia
            else Municipio.objects.none()
        )
        self.fields[campos["localidad"]].queryset = (
            Localidad.objects.filter(municipio=municipio).order_by("nombre")
            if municipio
            else Localidad.objects.none()
        )

        if provincia:
            self.fields[campos["provincia"]].initial = provincia
        if departamento:
            self.fields[campos["departamento"]].initial = departamento
        if municipio:
            self.fields[campos["municipio"]].initial = municipio
        if localidad:
            self.fields[campos["localidad"]].initial = localidad

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
        for (
            campo_controlador,
            valor_habilitante,
            campo_dependiente,
        ) in self.CAMPOS_OTRA_OPCION:
            if cleaned_data.get(campo_controlador) != valor_habilitante:
                cleaned_data[campo_dependiente] = ""

        if "otra" not in meals:
            cleaned_data["prestaciones_alimentarias_otra"] = ""

        if "ninguna" in meals:
            for field_name in self.CAMPOS_VACIAR_SIN_PRESTACIONES:
                cleaned_data[field_name] = ""

        for (
            campo_controlador,
            valor_habilitante,
            campo_dependiente,
        ) in self.CAMPOS_SI_NO_DEPENDIENTES:
            if cleaned_data.get(campo_controlador) != valor_habilitante:
                cleaned_data[campo_dependiente] = ""

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
