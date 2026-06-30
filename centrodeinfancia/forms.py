# pylint: disable=too-many-lines

from datetime import datetime, date

from django import forms
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator, RegexValidator

from core.models import Localidad, Municipio, Provincia
from core.validators import validate_unicode_email
from intervenciones.constants import PROGRAMA_ALIASES_CENTRO_INFANCIA
from intervenciones.models.intervenciones import (
    SubIntervencion,
    TipoDestinatario,
    TipoIntervencion,
)
from users.models import Profile
from centrodeinfancia.formulario_cdi_schema import (
    CAMPOS_OPCIONES_MULTIPLES,
    OPCIONES_DIAS_SEMANA,
)
from centrodeinfancia.models import (
    CentroDeInfancia,
    CentroDeInfanciaHorarioFuncionamiento,
    DepartamentoIpi,
    IntervencionCentroInfancia,
    NominaCentroInfancia,
    Trabajador,
    normalizar_cuit,
    TRABAJADOR_CAPACITACIONES_CHOICES,
    TRABAJADOR_GRUPO_PERTENENCIA_CHOICES,
    TRABAJADOR_LENGUAJES_CHOICES,
    TRABAJADOR_TIPO_DISCAPACIDAD_CHOICES,
    NOMINA_ALERGIA_CHOICES,
    NOMINA_DOSIS_VACUNA_CHOICES,
    NOMINA_VACUNAS,
    NominaPais,
    NominaNacionalidad,
)
from centrodeinfancia.forms_observacion import ObservacionCentroInfanciaForm
from centrodeinfancia.forms_formulario_cdi import (
    FormularioCDIForm,
    construir_filas_iniciales_fijas,
    construir_clase_formset_articulacion,
    construir_clase_formset_distribucion_salas,
    construir_clase_formset_demanda_insatisfecha,
)

__all__ = [
    "CentroDeInfanciaForm",
    "NominaCentroInfanciaForm",
    "NominaCentroInfanciaCreateForm",
    "NominaCentroInfanciaDestinatariosForm",
    "IntervencionCentroInfanciaForm",
    "TrabajadorCDIForm",
    "ObservacionCentroInfanciaForm",
    "FormularioCDIForm",
    "construir_filas_iniciales_fijas",
    "construir_clase_formset_articulacion",
    "construir_clase_formset_distribucion_salas",
    "construir_clase_formset_demanda_insatisfecha",
]


class CentroDeInfanciaForm(forms.ModelForm):
    SOLO_DIGITOS_ERROR = "Ingrese solo números (sin espacios ni signos)."
    TELEFONO_FORMATO_ERROR = "Ingrese un teléfono válido: solo números o grupos numéricos separados por guiones."
    TELEFONO_REGEX = RegexValidator(
        regex=r"^\d+(?:-\d+)*$",
        message=TELEFONO_FORMATO_ERROR,
    )
    DIAS_SEMANA = list(OPCIONES_DIAS_SEMANA)
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
    decil_ipi = forms.CharField(
        label="Decil de IPI",
        required=False,
        disabled=True,
    )

    @staticmethod
    def _obtener_provincia_usuario(user):
        if not user or not getattr(user, "is_authenticated", False):
            return None
        profile = Profile.objects.select_related("provincia").filter(user=user).first()
        if not profile:
            return None

        provincia_usuario = getattr(profile, "provincia", None)
        if not provincia_usuario:
            return None

        if not Provincia.objects.filter(pk=provincia_usuario.pk).exists():
            return None

        return provincia_usuario

    def __init__(self, *args, **kwargs):
        self.current_user = kwargs.pop("user", None)
        self.lock_provincia_from_user = kwargs.pop("lock_provincia_from_user", False)
        super().__init__(*args, **kwargs)
        self._configurar_campos_dinamicos_horarios()
        self._popular_campos_ubicacion()
        self._aplicar_provincia_usuario()
        self._aplicar_requeridos()
        self._aplicar_atributos_numericos()
        self._aplicar_campo_decil_ipi()
        self._aplicar_clases_y_placeholders()

    # Mostrar/editar solo el año en el formulario: aceptamos AAAA y lo convertimos
    # internamente como una fecha <AAAA>-01-01 para mantener compatibilidad
    # con el modelo (`DateField`).
    fecha_inicio = forms.CharField(
        required=False,
        label="Año de inicio de actividades del CDI",
        widget=forms.NumberInput(
            attrs={
                "placeholder": "AAAA",
                "min": "1900",
                "max": "2100",
                "class": "form-control",
            }
        ),
    )

    def _aplicar_requeridos(self):
        self.fields["telefono"].required = True
        self.fields["telefono"].error_messages[
            "required"
        ] = "Este campo es obligatorio."
        self.fields["telefono_referente"].required = False
        self.fields["ambito"].required = False

    def _configurar_campos_dinamicos_horarios(self):
        horarios_instancia = {}
        if getattr(self.instance, "pk", None):
            horarios_instancia = {
                horario.dia: horario
                for horario in self.instance.horarios_funcionamiento.all()
            }

        for dia, etiqueta in self.DIAS_SEMANA:
            apertura_name = f"horario_{dia}_apertura"
            cierre_name = f"horario_{dia}_cierre"
            horario = horarios_instancia.get(dia)
            self.fields[apertura_name] = forms.TimeField(
                required=False,
                label=f"{etiqueta} - apertura",
                widget=forms.TimeInput(attrs={"type": "time"}),
                initial=getattr(horario, "hora_apertura", None),
            )
            self.fields[cierre_name] = forms.TimeField(
                required=False,
                label=f"{etiqueta} - cierre",
                widget=forms.TimeInput(attrs={"type": "time"}),
                initial=getattr(horario, "hora_cierre", None),
            )

    def _aplicar_atributos_numericos(self):
        # Campos estrictamente numéricos
        for field_name in ["numero", "codigo_postal"]:
            attrs = self.fields[field_name].widget.attrs
            attrs["inputmode"] = "numeric"
            attrs["pattern"] = r"\d*"

        cuit_attrs = self.fields["cuit_organizacion_gestiona"].widget.attrs
        cuit_attrs["inputmode"] = "numeric"
        cuit_attrs.pop("pattern", None)

        # Campos de teléfono: permitir guiones y usar inputmode="tel"
        for field_name in ["telefono", "telefono_referente"]:
            if field_name not in self.fields:
                continue
            attrs = self.fields[field_name].widget.attrs
            attrs["inputmode"] = "tel"
            # Patrón alineado con TELEFONO_REGEX/validación backend: dígitos con grupos separados por guiones
            attrs["pattern"] = r"\d+(?:-\d+)*"

        self.fields["codigo_postal"].widget.attrs["maxlength"] = "10"
        self.fields["cuit_organizacion_gestiona"].widget.attrs["maxlength"] = "13"

    def _aplicar_campo_decil_ipi(self):
        self.fields["decil_ipi"].widget.attrs["readonly"] = True
        self.fields["decil_ipi"].widget.attrs["tabindex"] = "-1"

    def _aplicar_clases_y_placeholders(self):
        for _field_name, field in self.fields.items():
            existing = field.widget.attrs.get("class", "")
            widget_class = (
                "form-select"
                if isinstance(field.widget, (forms.Select, forms.SelectMultiple))
                else "form-control"
            )
            field.widget.attrs["class"] = f"{existing} {widget_class}".strip()

        self.fields["cuit_organizacion_gestiona"].widget.attrs[
            "placeholder"
        ] = "20-44535030-4"
        self.fields["cuit_organizacion_gestiona"].max_length = 13
        self.fields["cuit_organizacion_gestiona"].validators = [
            validator
            for validator in self.fields["cuit_organizacion_gestiona"].validators
            if not isinstance(validator, MaxLengthValidator)
        ]
        if not self.instance.pk and not self.initial.get("ambito"):
            self.initial["ambito"] = "sin_informacion"

    def _clean_solo_digitos(self, field_name):
        value = (self.cleaned_data.get(field_name) or "").strip()
        if not value:
            return value
        if not value.isdigit():
            raise forms.ValidationError(self.SOLO_DIGITOS_ERROR)
        return value

    def _popular_campos_ubicacion(self):
        def parse_pk(value):
            return int(value) if value and str(value).isdigit() else None

        provincia = Provincia.objects.filter(
            pk=parse_pk(self.data.get(self.add_prefix("provincia")))
        ).first() or getattr(self.instance, "provincia", None)
        departamento = DepartamentoIpi.objects.filter(
            pk=parse_pk(self.data.get(self.add_prefix("departamento")))
        ).first() or getattr(self.instance, "departamento", None)
        municipio = Municipio.objects.filter(
            pk=parse_pk(self.data.get(self.add_prefix("municipio")))
        ).first() or getattr(self.instance, "municipio", None)
        localidad = Localidad.objects.filter(
            pk=parse_pk(self.data.get(self.add_prefix("localidad")))
        ).first() or getattr(self.instance, "localidad", None)

        self.fields["provincia"].queryset = Provincia.objects.all().order_by("nombre")

        if not provincia and not self.data:
            provincia = self._obtener_provincia_usuario(self.current_user)

        if provincia:
            self.fields["provincia"].initial = provincia
            self.fields["departamento"].queryset = DepartamentoIpi.objects.filter(
                provincia=provincia
            ).order_by("nombre")
            self.fields["municipio"].queryset = Municipio.objects.filter(
                provincia=provincia
            ).order_by("nombre")
        else:
            self.fields["departamento"].queryset = (
                DepartamentoIpi.objects.all().order_by("nombre")
            )
            self.fields["municipio"].queryset = Municipio.objects.all().order_by(
                "nombre"
            )
            self.fields["localidad"].queryset = Localidad.objects.all().order_by(
                "nombre"
            )

        if departamento:
            self.fields["departamento"].initial = departamento
            self.fields["decil_ipi"].initial = (
                str(departamento.decil_ipi)
                if departamento.decil_ipi is not None
                else ""
            )

        if municipio:
            self.fields["municipio"].initial = municipio
            self.fields["localidad"].queryset = Localidad.objects.filter(
                municipio=municipio
            ).order_by("nombre")

        if localidad:
            self.fields["localidad"].initial = localidad

    def _aplicar_provincia_usuario(self):
        provincia_usuario = self._obtener_provincia_usuario(self.current_user)
        if not provincia_usuario:
            self.fields["provincia"].queryset = Provincia.objects.all().order_by(
                "nombre"
            )
            self.fields["provincia"].disabled = False
            return

        if self.lock_provincia_from_user and not self.instance.pk:
            self.fields["provincia"].queryset = Provincia.objects.filter(
                pk=provincia_usuario.pk
            )
            self.fields["provincia"].initial = provincia_usuario
            self.fields["provincia"].disabled = True
            self.fields["departamento"].queryset = DepartamentoIpi.objects.filter(
                provincia=provincia_usuario
            ).order_by("nombre")
            self.fields["municipio"].queryset = Municipio.objects.filter(
                provincia=provincia_usuario
            ).order_by("nombre")
            return

        self.fields["provincia"].disabled = False
        if not self.fields["provincia"].initial:
            self.fields["provincia"].initial = provincia_usuario

    def clean_provincia(self):
        if self.fields["provincia"].disabled and self.current_user:
            provincia_usuario = self._obtener_provincia_usuario(self.current_user)
            if provincia_usuario:
                return provincia_usuario
        return self.cleaned_data.get("provincia")

    def clean_numero(self):
        return self._clean_solo_digitos("numero")

    def clean_cuit_organizacion_gestiona(self):
        value = normalizar_cuit(self.cleaned_data.get("cuit_organizacion_gestiona"))
        if not value:
            return None
        if len(value) != 11:
            raise forms.ValidationError("Ingrese un CUIT válido de 11 dígitos.")
        return value

    def clean_mail(self):
        mail = self.cleaned_data.get("mail")
        if not mail:
            return mail
        if not isinstance(mail, str):
            raise ValidationError("El correo electrónico debe ser una cadena válida.")
        mail = mail.strip()
        if not mail:
            return None
        try:
            validate_unicode_email(mail)
        except ValidationError as exc:
            raise forms.ValidationError(exc.messages) from exc
        return mail

    def clean_fecha_inicio(self):
        raw = self.cleaned_data.get("fecha_inicio")
        if raw in (None, ""):
            return None
        # If it's already a date, normalize to Jan 1 of that year
        if isinstance(raw, date):
            return date(raw.year, 1, 1)
        if isinstance(raw, str):
            raw = raw.strip()
            # Accept plain year "AAAA"
            if raw.isdigit() and len(raw) == 4:
                year = int(raw)
                return date(year, 1, 1)
            # Fallback: accept dd/mm/YYYY or YYYY-mm-dd for compatibility
            try:
                return datetime.strptime(raw, "%d/%m/%Y").date()
            except ValueError:
                try:
                    return datetime.strptime(raw, "%Y-%m-%d").date()
                except ValueError as exc2:
                    raise forms.ValidationError(
                        "Formato inválido para Año de inicio. Use AAAA."
                    ) from exc2
        raise forms.ValidationError("Formato inválido para Año de inicio.")

    def clean_telefono(self):
        value = (self.cleaned_data.get("telefono") or "").strip()
        if not value:
            return value
        self.TELEFONO_REGEX(value)
        return value

    def clean_telefono_referente(self):
        value = (self.cleaned_data.get("telefono_referente") or "").strip()
        if not value:
            return value
        self.TELEFONO_REGEX(value)
        return value

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("ambito"):
            cleaned_data["ambito"] = "sin_informacion"
        if cleaned_data.get("tipo_jornada") != "other":
            cleaned_data["tipo_jornada_otra"] = ""

        if cleaned_data.get("modalidad_gestion") != "otra":
            cleaned_data["modalidad_gestion_otra"] = ""

        dias = cleaned_data.get("dias_funcionamiento") or []
        horarios = {}
        for dia, _etiqueta in self.DIAS_SEMANA:
            apertura = cleaned_data.get(f"horario_{dia}_apertura")
            cierre = cleaned_data.get(f"horario_{dia}_cierre")
            if dia not in dias and (apertura or cierre):
                self.add_error(
                    f"horario_{dia}_cierre",
                    "El día debe estar seleccionado para cargar horarios.",
                )
            if dia in dias:
                if bool(apertura) != bool(cierre):
                    self.add_error(
                        f"horario_{dia}_cierre",
                        "Debe completar horario de apertura y cierre.",
                    )
                elif apertura and cierre and apertura >= cierre:
                    self.add_error(
                        f"horario_{dia}_cierre",
                        "El horario de cierre debe ser posterior al de apertura.",
                    )
                horarios[dia] = {
                    "hora_apertura": apertura,
                    "hora_cierre": cierre,
                }
        cleaned_data["horarios_funcionamiento_data"] = horarios
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=commit)
        if not commit:
            return instance

        horarios = self.cleaned_data.get("horarios_funcionamiento_data", {})
        instance.horarios_funcionamiento.exclude(dia__in=horarios.keys()).delete()
        for dia, horario_data in horarios.items():
            CentroDeInfanciaHorarioFuncionamiento.objects.update_or_create(
                centro=instance,
                dia=dia,
                defaults=horario_data,
            )
        return instance

    class Meta:
        model = CentroDeInfancia
        fields = [
            "nombre",
            "organizacion",
            "cuit_organizacion_gestiona",
            "ambito",
            "provincia",
            "departamento",
            "municipio",
            "localidad",
            "codigo_postal",
            "calle",
            "numero",
            "latitud",
            "longitud",
            "telefono",
            "mail",
            "meses_funcionamiento",
            "dias_funcionamiento",
            "tipo_jornada",
            "tipo_jornada_otra",
            "oferta_servicios",
            "modalidad_gestion",
            "modalidad_gestion_otra",
            "nombre_referente",
            "apellido_referente",
            "email_referente",
            "telefono_referente",
            "fecha_inicio",
        ]
        widgets = {
            "fecha_inicio": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "meses_funcionamiento": forms.CheckboxSelectMultiple(),
            "dias_funcionamiento": forms.CheckboxSelectMultiple(),
        }


class NullableBooleanChoiceField(forms.TypedChoiceField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("required", False)
        kwargs.setdefault(
            "choices",
            (
                ("", "---------"),
                ("true", "Si"),
                ("false", "No"),
            ),
        )
        kwargs.setdefault(
            "coerce", lambda value: None if value == "" else value == "true"
        )
        kwargs.setdefault("empty_value", None)
        super().__init__(*args, **kwargs)


class NominaCentroInfanciaFormEdit(forms.ModelForm):
    class Meta:
        model = NominaCentroInfancia
        fields = [
            "estado",
            "dni",
            "apellido",
            "nombre",
            "fecha_nacimiento",
            "sexo",
            "nacionalidad",
            "sala",
            "pertenece_pueblo_originario",
            "pueblo_originario_cual",
            "habla_lengua_originaria_hogar",
            "talla",
            "peso",
            "calendario_vacunacion_al_dia",
            "tiene_discapacidad",
            "discapacidad_tipo",
            "recibe_apoyo_discapacidad",
            "posee_cud",
            "posee_obra_social",
            "calle_domicilio",
            "altura_domicilio",
            "piso_domicilio",
            "departamento_domicilio",
            "provincia_domicilio",
            "municipio_domicilio",
            "localidad_domicilio",
            "responsable_legal_1_apellido",
            "responsable_legal_1_nombre",
            "responsable_legal_1_dni",
            "responsable_legal_1_telefono",
            "responsable_legal_1_percibe_auh",
            "responsable_legal_1_percibe_alimenta",
            "responsable_legal_2_apellido",
            "responsable_legal_2_nombre",
            "responsable_legal_2_dni",
            "responsable_legal_2_telefono",
            "responsable_legal_2_percibe_auh",
            "responsable_legal_2_percibe_alimenta",
            "adulto_responsable_apellido",
            "adulto_responsable_nombre",
            "adulto_responsable_dni",
            "adulto_responsable_telefono",
            "adulto_responsable_parentesco",
            "observaciones",
        ]
        labels = {
            "estado": "Estado",
            "dni": "DNI",
            "apellido": "Apellido",
            "nombre": "Nombre",
            "fecha_nacimiento": "Fecha de nacimiento",
            "sexo": "Sexo",
            "nacionalidad": "Nacionalidad",
            "sala": "Sala",
            "pertenece_pueblo_originario": (
                "¿El niño pertenece o se reconoce como parte de un pueblo indígena u originario?"
            ),
            "pueblo_originario_cual": "¿Cuál?",
            "habla_lengua_originaria_hogar": (
                "¿En el hogar del niño se habla habitualmente alguna lengua indígena u originaria?"
            ),
            "talla": "Talla",
            "peso": "Peso",
            "tiene_discapacidad": (
                "¿El niño tiene alguna discapacidad y/o requiere apoyos específicos?"
            ),
            "discapacidad_tipo": "En caso de responder Sí, indicar cuál",
            "calle_domicilio": "Calle",
            "altura_domicilio": "Altura",
            "piso_domicilio": "Piso",
            "departamento_domicilio": "Departamento",
            "provincia_domicilio": "Provincia",
            "municipio_domicilio": "Municipio",
            "localidad_domicilio": "Localidad",
            "responsable_legal_1_apellido": "Apellido",
            "responsable_legal_1_nombre": "Nombre",
            "responsable_legal_1_dni": "DNI",
            "responsable_legal_1_telefono": "Teléfono",
            "responsable_legal_1_percibe_auh": "Percibe AUH",
            "responsable_legal_1_percibe_alimenta": "Percibe Alimenta",
            "responsable_legal_2_apellido": "Apellido",
            "responsable_legal_2_nombre": "Nombre",
            "responsable_legal_2_dni": "DNI",
            "responsable_legal_2_telefono": "Teléfono",
            "responsable_legal_2_percibe_auh": "Percibe AUH",
            "responsable_legal_2_percibe_alimenta": "Percibe Alimenta",
            "adulto_responsable_apellido": "Apellido",
            "adulto_responsable_nombre": "Nombre",
            "adulto_responsable_dni": "DNI",
            "adulto_responsable_telefono": "Teléfono",
            "adulto_responsable_parentesco": "Relación de parentesco",
            "observaciones": "Observaciones",
        }
        widgets = {
            "fecha_nacimiento": forms.DateInput(
                format="%Y-%m-%d",
                attrs={"type": "date"},
            ),
        }


class NominaCentroInfanciaBaseForm(forms.ModelForm):
    edad_calculada = forms.IntegerField(
        label="Edad",
        required=False,
        disabled=True,
    )

    class Meta:
        model = NominaCentroInfancia
        fields = [
            "estado",
            "dni",
            "apellido",
            "nombre",
            "fecha_nacimiento",
            "edad_calculada",
            "sexo",
            "nacionalidad",
            "sala",
            "pertenece_pueblo_originario",
            "pueblo_originario_cual",
            "habla_lengua_originaria_hogar",
            "talla",
            "peso",
            "calendario_vacunacion_al_dia",
            "tiene_discapacidad",
            "discapacidad_tipo",
            "recibe_apoyo_discapacidad",
            "posee_cud",
            "posee_obra_social",
            "calle_domicilio",
            "altura_domicilio",
            "piso_domicilio",
            "departamento_domicilio",
            "provincia_domicilio",
            "municipio_domicilio",
            "localidad_domicilio",
            "responsable_legal_1_apellido",
            "responsable_legal_1_nombre",
            "responsable_legal_1_dni",
            "responsable_legal_1_telefono",
            "responsable_legal_1_percibe_auh",
            "responsable_legal_1_percibe_alimenta",
            "responsable_legal_2_apellido",
            "responsable_legal_2_nombre",
            "responsable_legal_2_dni",
            "responsable_legal_2_telefono",
            "responsable_legal_2_percibe_auh",
            "responsable_legal_2_percibe_alimenta",
            "adulto_responsable_apellido",
            "adulto_responsable_nombre",
            "adulto_responsable_dni",
            "adulto_responsable_telefono",
            "adulto_responsable_parentesco",
            "observaciones",
        ]
        widgets = {
            "fecha_nacimiento": forms.DateInput(
                format="%Y-%m-%d",
                attrs={"type": "date"},
            ),
            "observaciones": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._configure_boolean_fields()
        self._configure_choice_fields()
        self._configure_widgets()
        self._configure_geography_fields()
        self._configure_initial_age()
        self._apply_required_flags()

    def _configure_boolean_fields(self):
        boolean_fields = {
            "calendario_vacunacion_al_dia": {
                "label": "Calendario de vacunación al día",
            },
            "recibe_apoyo_discapacidad": {
                "label": (
                    "Recibe actualmente algún tipo de apoyo, tratamiento o acompañamiento"
                ),
            },
            "posee_cud": {
                "label": "Posee Certificado Único de Discapacidad (CUD)",
                "choices": (
                    ("", "---------"),
                    ("true", "Tiene"),
                    ("false", "No tiene"),
                ),
            },
            "posee_obra_social": {
                "label": "Posee Obra Social",
            },
        }
        for field_name, config in boolean_fields.items():
            current_value = None
            if self.instance.pk:
                current_value = getattr(self.instance, field_name)
            if current_value is True:
                current_value = "true"
            elif current_value is False:
                current_value = "false"
            field_kwargs = {
                "label": config["label"],
                "initial": current_value,
            }
            if "choices" in config:
                field_kwargs["choices"] = config["choices"]
            self.fields[field_name] = NullableBooleanChoiceField(**field_kwargs)

    def _configure_choice_fields(self):
        self.fields["sexo"].choices = [("", "---------")] + list(
            NominaCentroInfancia.SexoChoices.choices
        )

    def _configure_widgets(self):
        labels = {
            "estado": "Estado",
            "dni": "DNI",
            "apellido": "Apellido",
            "nombre": "Nombre",
            "fecha_nacimiento": "Fecha de nacimiento",
            "sexo": "Sexo",
            "nacionalidad": "Nacionalidad",
            "sala": "Sala",
            "pertenece_pueblo_originario": (
                "¿El niño pertenece o se reconoce como parte de un pueblo indígena u originario?"
            ),
            "pueblo_originario_cual": "¿Cuál?",
            "habla_lengua_originaria_hogar": (
                "¿En el hogar del niño se habla habitualmente alguna lengua indígena u originaria?"
            ),
            "talla": "Talla",
            "peso": "Peso",
            "tiene_discapacidad": (
                "¿El niño tiene alguna discapacidad y/o requiere apoyos específicos?"
            ),
            "discapacidad_tipo": "En caso de responder Sí, indicar cuál",
            "calle_domicilio": "Calle",
            "altura_domicilio": "Altura",
            "piso_domicilio": "Piso",
            "departamento_domicilio": "Departamento",
            "provincia_domicilio": "Provincia",
            "municipio_domicilio": "Municipio",
            "localidad_domicilio": "Localidad",
            "responsable_legal_1_apellido": "Apellido",
            "responsable_legal_1_nombre": "Nombre",
            "responsable_legal_1_dni": "DNI",
            "responsable_legal_1_telefono": "Teléfono",
            "responsable_legal_1_percibe_auh": "Percibe AUH",
            "responsable_legal_1_percibe_alimenta": "Percibe Alimentar",
            "responsable_legal_2_apellido": "Apellido",
            "responsable_legal_2_nombre": "Nombre",
            "responsable_legal_2_dni": "DNI",
            "responsable_legal_2_telefono": "Teléfono",
            "responsable_legal_2_percibe_auh": "Percibe AUH",
            "responsable_legal_2_percibe_alimenta": "Percibe Alimentar",
            "adulto_responsable_apellido": "Apellido",
            "adulto_responsable_nombre": "Nombre",
            "adulto_responsable_dni": "DNI",
            "adulto_responsable_telefono": "Teléfono",
            "adulto_responsable_parentesco": "Relación de parentesco",
            "observaciones": "Observaciones",
        }
        for field_name, field in self.fields.items():
            if field_name in labels:
                field.label = labels[field_name]
            widget = field.widget
            css_class = "form-control"
            if isinstance(widget, forms.Select):
                css_class = "form-select"
            widget.attrs["class"] = (
                f'{widget.attrs.get("class", "")} {css_class}'.strip()
            )

        for field_name in [
            "dni",
            "responsable_legal_1_dni",
            "responsable_legal_1_telefono",
            "responsable_legal_2_dni",
            "responsable_legal_2_telefono",
            "adulto_responsable_dni",
            "altura_domicilio",
            "peso",
        ]:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs["inputmode"] = "numeric"

        self.fields["edad_calculada"].widget.attrs["readonly"] = True
        self.fields["edad_calculada"].widget.attrs["tabindex"] = "-1"

    def _configure_geography_fields(self):
        def parse_pk(value):
            return int(value) if value and str(value).isdigit() else None

        def normalize_name(value):
            return slugify(str(value or "").strip())

        def resolve_by_name(queryset, value):
            normalized = normalize_name(value)
            if not normalized:
                return None
            for item in queryset.order_by("nombre"):
                if normalize_name(item.nombre) == normalized:
                    return item
            return None

        provincia_initial = self.initial.get("provincia_domicilio")
        municipio_initial = self.initial.get("municipio_domicilio")
        localidad_initial = self.initial.get("localidad_domicilio")

        provincia = Provincia.objects.filter(
            pk=parse_pk(self.data.get(self.add_prefix("provincia_domicilio")))
        ).first() or getattr(self.instance, "provincia_domicilio", None)
        if (
            not provincia
            and provincia_initial
            and not isinstance(provincia_initial, Provincia)
        ):
            provincia = resolve_by_name(Provincia.objects.all(), provincia_initial)

        municipio = Municipio.objects.filter(
            pk=parse_pk(self.data.get(self.add_prefix("municipio_domicilio")))
        ).first() or getattr(self.instance, "municipio_domicilio", None)
        if (
            not municipio
            and municipio_initial
            and not isinstance(municipio_initial, Municipio)
        ):
            municipio_queryset = Municipio.objects.filter(provincia=provincia)
            if not provincia:
                municipio_queryset = Municipio.objects.all()
            municipio = resolve_by_name(municipio_queryset, municipio_initial)

        localidad = Localidad.objects.filter(
            pk=parse_pk(self.data.get(self.add_prefix("localidad_domicilio")))
        ).first() or getattr(self.instance, "localidad_domicilio", None)
        if (
            not localidad
            and localidad_initial
            and not isinstance(localidad_initial, Localidad)
        ):
            localidad_queryset = Localidad.objects.filter(municipio=municipio)
            if not municipio:
                localidad_queryset = Localidad.objects.all()
            localidad = resolve_by_name(localidad_queryset, localidad_initial)

        self.fields["provincia_domicilio"].queryset = Provincia.objects.all().order_by(
            "nombre"
        )
        if provincia:
            self.fields["provincia_domicilio"].initial = provincia
        if provincia:
            self.fields["municipio_domicilio"].queryset = Municipio.objects.filter(
                provincia=provincia
            ).order_by("nombre")
        else:
            self.fields["municipio_domicilio"].queryset = Municipio.objects.none()
        if municipio:
            self.fields["municipio_domicilio"].initial = municipio

        if municipio:
            self.fields["localidad_domicilio"].queryset = Localidad.objects.filter(
                municipio=municipio
            ).order_by("nombre")
        else:
            self.fields["localidad_domicilio"].queryset = Localidad.objects.none()

        if localidad:
            self.fields["localidad_domicilio"].initial = localidad

    def _configure_initial_age(self):
        fecha_nacimiento = self.initial.get("fecha_nacimiento") or getattr(
            self.instance, "fecha_nacimiento", None
        )
        if fecha_nacimiento:
            temp_nomina = (
                self.instance
                if self.instance.pk
                else NominaCentroInfancia(fecha_nacimiento=fecha_nacimiento)
            )
            self.fields["edad_calculada"].initial = temp_nomina.edad

    def _apply_required_flags(self):
        for field_name in ["estado", "dni", "apellido", "nombre", "fecha_nacimiento"]:
            self.fields[field_name].required = True

    def clean(self):
        cleaned_data = super().clean()
        fecha_nacimiento = cleaned_data.get("fecha_nacimiento")
        if fecha_nacimiento:
            cleaned_data["edad_calculada"] = NominaCentroInfancia(
                fecha_nacimiento=fecha_nacimiento
            ).edad
        return cleaned_data


class NominaCentroInfanciaForm(NominaCentroInfanciaBaseForm):
    pass


class NominaCentroInfanciaCreateForm(NominaCentroInfanciaBaseForm):
    pass


class NominaCentroInfanciaDestinatariosForm(NominaCentroInfanciaBaseForm):
    """Formulario de página completa para el legajo 201 (Destinatarios CDI)."""

    # ── JSONField multiselects ────────────────────────────────────────────────
    grupo_pertenencia = forms.MultipleChoiceField(
        choices=TRABAJADOR_GRUPO_PERTENENCIA_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label=(
            "¿Desciende, tiene antepasados o pertenece a alguno de los siguientes grupos?"
        ),
    )
    lenguajes = forms.MultipleChoiceField(
        choices=TRABAJADOR_LENGUAJES_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Lenguajes que utiliza",
    )
    tipo_discapacidad = forms.MultipleChoiceField(
        choices=TRABAJADOR_TIPO_DISCAPACIDAD_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="¿Qué tipo de discapacidad presenta?",
    )
    alergias_alimentarias = forms.MultipleChoiceField(
        choices=NOMINA_ALERGIA_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Alergias alimentarias",
    )
    nacionalidad = forms.ChoiceField(
        choices=[],
        required=False,
        label="Nacionalidad",
    )
    pais_nacimiento = forms.ChoiceField(
        choices=[],
        required=False,
        label="¿Cuál es su país de nacimiento?",
    )
    responsable_legal_1_pais_nacimiento = forms.ChoiceField(
        choices=[],
        required=False,
        label="¿Cuál es su país de nacimiento?",
    )
    responsable_legal_1_nacionalidad = forms.ChoiceField(
        choices=[],
        required=False,
        label="¿Cuál es su nacionalidad?",
    )
    responsable_legal_2_pais_nacimiento = forms.ChoiceField(
        choices=[],
        required=False,
        label="¿Cuál es su país de nacimiento?",
    )
    responsable_legal_2_nacionalidad = forms.ChoiceField(
        choices=[],
        required=False,
        label="¿Cuál es su nacionalidad?",
    )

    class Meta(NominaCentroInfanciaBaseForm.Meta):
        fields = list(NominaCentroInfanciaBaseForm.Meta.fields) + [
            # Sección 3: Registro
            "tipo_registro",
            "fecha_registro",
            # Sección 4: Trabajador que registra
            "trabajador_registra",
            # Sección 5: Responsable 1 (extendido)
            "responsable_legal_1_relacion",
            "responsable_legal_1_fecha_nacimiento",
            "responsable_legal_1_tipo_documentacion",
            "responsable_legal_1_cuit",
            "responsable_legal_1_pais_nacimiento",
            "responsable_legal_1_nacionalidad",
            "responsable_legal_1_sexo_registral",
            "responsable_legal_1_nivel_educativo",
            "responsable_legal_1_consentimiento",
            # Sección 6: Responsable 2 (extendido)
            "responsable_legal_2_relacion",
            "responsable_legal_2_fecha_nacimiento",
            "responsable_legal_2_tipo_documentacion",
            "responsable_legal_2_cuit",
            "responsable_legal_2_pais_nacimiento",
            "responsable_legal_2_nacionalidad",
            "responsable_legal_2_sexo_registral",
            "responsable_legal_2_nivel_educativo",
            "responsable_legal_2_consentimiento",
            # Sección 7: Datos del niño/a (extendido)
            "tipo_documentacion",
            "cuit_nino",
            "pais_nacimiento",
            "edad_unidad",
            # Sección 8: Domicilio (extendido)
            "tipo_barrio",
            "convivientes",
            # Sección 9: Cultura e identidad
            "grupo_pertenencia",
            "lenguajes",
            "necesito_interprete",
            # Sección 10: Discapacidad (extendido)
            "tipo_discapacidad",
            "numero_cud",
            # Sección 11: Salud
            "cobertura_salud",
            "controles_sanitarios_ultimo_anio",
            # Sección 12: Antropometría
            "longitud_acostado",
            "perimetro_cefalico",
            # Sección 13: Nutrición
            "lactancia",
            "diagnostico_peso",
            "diagnostico_talla",
            "orientacion_msal",
            "alergias_alimentarias",
            # Sección 14: ANSES
            "anses_auh",
            "anses_aue",
            "anses_acsi",
            "anses_acn",
            # Sección 16: Desarrollo Infantil Temprano
            "recibe_apoyo_desarrollo",
            # vacunacion_nomivac se maneja con campos dinámicos, no aparece aquí
        ]
        widgets = {
            **NominaCentroInfanciaBaseForm.Meta.widgets,
            "fecha_registro": forms.DateInput(
                format="%Y-%m-%d", attrs={"type": "date"}
            ),
            "responsable_legal_1_fecha_nacimiento": forms.DateInput(
                format="%Y-%m-%d", attrs={"type": "date"}
            ),
            "responsable_legal_2_fecha_nacimiento": forms.DateInput(
                format="%Y-%m-%d", attrs={"type": "date"}
            ),
        }

    _NEW_LABELS = {
        "tipo_registro": "Tipo de registro",
        "fecha_registro": "Fecha de alta, seguimiento o baja",
        "trabajador_registra": "Trabajador/a que registra",
        "responsable_legal_1_relacion": "Relación con el/la infante",
        "responsable_legal_1_fecha_nacimiento": "Fecha de nacimiento",
        "responsable_legal_1_tipo_documentacion": "Tipo de documentación",
        "responsable_legal_1_cuit": "CUIT",
        "responsable_legal_1_pais_nacimiento": "País de nacimiento",
        "responsable_legal_1_nacionalidad": "Nacionalidad",
        "responsable_legal_1_sexo_registral": "Sexo registral",
        "responsable_legal_1_nivel_educativo": "Nivel educativo",
        "responsable_legal_1_consentimiento": "Consentimiento libre, previo e informado",
        "responsable_legal_2_relacion": "Relación con el/la infante",
        "responsable_legal_2_fecha_nacimiento": "Fecha de nacimiento",
        "responsable_legal_2_tipo_documentacion": "Tipo de documentación",
        "responsable_legal_2_cuit": "CUIT",
        "responsable_legal_2_pais_nacimiento": "País de nacimiento",
        "responsable_legal_2_nacionalidad": "Nacionalidad",
        "responsable_legal_2_sexo_registral": "Sexo registral",
        "responsable_legal_2_nivel_educativo": "Nivel educativo",
        "responsable_legal_2_consentimiento": "Consentimiento libre, previo e informado",
        "tipo_documentacion": "Tipo de documentación",
        "cuit_nino": "CUIT",
        "pais_nacimiento": "País de nacimiento",
        "edad_unidad": "Unidad de medida de la edad",
        "tipo_barrio": "Tipo de barrio",
        "convivientes": "Cantidad de personas convivientes",
        "necesito_interprete": "¿Se necesitó intérprete?",
        "numero_cud": "Número de CUD (ANSES)",
        "cobertura_salud": "Cobertura de salud",
        "controles_sanitarios_ultimo_anio": "Controles sanitarios en el último año",
        "longitud_acostado": "Longitud (cm, medida acostado)",
        "perimetro_cefalico": "Perímetro cefálico (cm)",
        "lactancia": "Lactancia",
        "diagnostico_peso": "Estimación del peso",
        "diagnostico_talla": "Estimación de la talla",
        "orientacion_msal": "Orientación Ministerio de Salud",
        "anses_auh": "Asignación Universal por Hijo (AUH)",
        "anses_aue": "Asignación por Embarazo (AUE)",
        "anses_acsi": "Asignación por Cuidado de Salud Integral (ACSI)",
        "anses_acn": "Asignación de Complemento Nutricional (ACN)",
        "recibe_apoyo_desarrollo": (
            "¿Recibe apoyo, tratamiento o acompañamiento para su desarrollo?"
        ),
    }

    def _configure_pais_nacionalidad_fields(self):
        empty = ("", "---------")
        paises = [empty] + [
            (p.nombre, p.nombre) for p in NominaPais.objects.order_by("nombre")
        ]
        nacionalidades = [empty] + [
            (n.nombre, n.nombre) for n in NominaNacionalidad.objects.order_by("nombre")
        ]
        for fname in (
            "pais_nacimiento",
            "responsable_legal_1_pais_nacimiento",
            "responsable_legal_2_pais_nacimiento",
        ):
            self.fields[fname].choices = paises
        for fname in (
            "nacionalidad",
            "responsable_legal_1_nacionalidad",
            "responsable_legal_2_nacionalidad",
        ):
            self.fields[fname].choices = nacionalidades

    def __init__(self, *args, centro=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._configure_pais_nacionalidad_fields()

        # Scope trabajador_registra al CDI recibido
        if centro:
            self.fields["trabajador_registra"].queryset = Trabajador.objects.filter(
                centro=centro
            ).order_by("apellido", "nombre")
        else:
            self.fields["trabajador_registra"].queryset = Trabajador.objects.none()

        # Pre-popular MultipleChoiceField desde la instancia
        for fname in (
            "grupo_pertenencia",
            "lenguajes",
            "tipo_discapacidad",
            "alergias_alimentarias",
        ):
            if self.instance.pk:
                self.fields[fname].initial = getattr(self.instance, fname) or []

        # Aplicar labels nuevos
        for fname, label in self._NEW_LABELS.items():
            if fname in self.fields:
                self.fields[fname].label = label

        # Aplicar CSS a campos nuevos (CheckboxSelectMultiple se salta)
        for fname, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.CheckboxSelectMultiple):
                continue
            css = "form-select" if isinstance(widget, forms.Select) else "form-control"
            current = widget.attrs.get("class", "")
            if css not in current:
                widget.attrs["class"] = f"{current} {css}".strip()

        # Agregar campos dinámicos por vacuna (Sección 15)
        nomivac_data = {}
        if self.instance.pk and self.instance.vacunacion_nomivac:
            nomivac_data = self.instance.vacunacion_nomivac
        for code, label in NOMINA_VACUNAS:
            vaccine_data = nomivac_data.get(code, {})
            dosis_field = forms.ChoiceField(
                choices=[("", "---------")] + list(NOMINA_DOSIS_VACUNA_CHOICES),
                required=False,
                label=label,
                initial=vaccine_data.get("dosis", ""),
            )
            dosis_field.widget.attrs["class"] = "form-select form-select-sm"
            self.fields[f"vacuna_{code}_dosis"] = dosis_field
            fecha_field = forms.DateField(
                required=False,
                label=f"{label} — última dosis",
                initial=vaccine_data.get("fecha") or None,
                widget=forms.DateInput(
                    format="%Y-%m-%d",
                    attrs={"type": "date", "class": "form-control form-control-sm"},
                ),
            )
            self.fields[f"vacuna_{code}_fecha"] = fecha_field

    def clean_grupo_pertenencia(self):
        return self.cleaned_data.get("grupo_pertenencia") or []

    def clean_lenguajes(self):
        return self.cleaned_data.get("lenguajes") or []

    def clean_tipo_discapacidad(self):
        return self.cleaned_data.get("tipo_discapacidad") or []

    def clean_alergias_alimentarias(self):
        return self.cleaned_data.get("alergias_alimentarias") or []

    def clean(self):
        cleaned_data = super().clean()
        # Construir vacunacion_nomivac desde los campos dinámicos
        nomivac = {}
        for code, _label in NOMINA_VACUNAS:
            dosis = cleaned_data.get(f"vacuna_{code}_dosis") or ""
            fecha_val = cleaned_data.get(f"vacuna_{code}_fecha")
            if dosis or fecha_val:
                nomivac[code] = {
                    "dosis": dosis,
                    "fecha": fecha_val.isoformat() if fecha_val else "",
                }
        cleaned_data["vacunacion_nomivac"] = nomivac
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.vacunacion_nomivac = self.cleaned_data.get("vacunacion_nomivac", {})
        if commit:
            instance.save()
        return instance


_MULTISELECT_FIELDS_TRABAJADOR = (
    "capacitaciones_certificadas",
    "grupo_pertenencia",
    "lenguajes",
    "tipo_discapacidad",
)


class TrabajadorCDIForm(forms.ModelForm):
    capacitaciones_certificadas = forms.MultipleChoiceField(
        choices=TRABAJADOR_CAPACITACIONES_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Capacitaciones certificadas (últimos tres años)",
    )
    grupo_pertenencia = forms.MultipleChoiceField(
        choices=TRABAJADOR_GRUPO_PERTENENCIA_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="¿Desciende, tiene antepasados o pertenece a alguno de los siguientes grupos?",
    )
    lenguajes = forms.MultipleChoiceField(
        choices=TRABAJADOR_LENGUAJES_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Lenguajes que utiliza",
    )
    tipo_discapacidad = forms.MultipleChoiceField(
        choices=TRABAJADOR_TIPO_DISCAPACIDAD_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="¿Qué tipo de discapacidad presenta? (puede marcar más de una opción)",
    )

    class Meta:
        model = Trabajador
        fields = [
            "fecha_carga",
            "subcomponente",
            "funcion_egp",
            "funcion_cdi",
            "sala_cdi",
            "nombre",
            "apellido",
            "fecha_nacimiento",
            "tipo_documentacion",
            "dni",
            "sexo_registral",
            "cuit",
            "pais_nacimiento",
            "nacionalidad_trabajador",
            "nivel_educativo",
            "formacion_academica",
            "capacitaciones_certificadas",
            "anos_trabajo_primera_infancia",
            "tipo_contratacion",
            "carga_horaria_semanal",
            "email",
            "telefono",
            "calle_contacto",
            "unidad_funcional",
            "tipo_barrio",
            "provincia_contacto",
            "departamento_contacto",
            "municipio_contacto",
            "localidad_contacto",
            "grupo_pertenencia",
            "pueblo_originario",
            "lenguajes",
            "es_interprete",
            "tiene_discapacidad",
            "tipo_discapacidad",
            "recibe_apoyo_discapacidad",
            "tiene_cud",
            "numero_cud",
        ]
        widgets = {
            "fecha_carga": forms.DateInput(
                attrs={"type": "date", "class": "form-control"},
                format="%Y-%m-%d",
            ),
            "fecha_nacimiento": forms.DateInput(
                attrs={"type": "date", "class": "form-control"},
                format="%Y-%m-%d",
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Precarga de valores para campos multiselect desde JSONField
        if self.instance.pk:
            for fname in _MULTISELECT_FIELDS_TRABAJADOR:
                value = getattr(self.instance, fname, None) or []
                if value:
                    self.initial[fname] = value

        # CSS classes
        for fname, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxSelectMultiple):
                continue
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault("class", "form-select")
            else:
                field.widget.attrs.setdefault("class", "form-control")

        # Tooltip en teléfono
        self.fields["telefono"].widget.attrs["placeholder"] = "Incluir código de área"

        # Límite HTML en carga horaria
        self.fields["carga_horaria_semanal"].widget.attrs.update(
            {"min": "1", "max": "60"}
        )

    def clean_carga_horaria_semanal(self):
        value = self.cleaned_data.get("carga_horaria_semanal")
        if value is not None and value > 60:
            raise forms.ValidationError(
                "La carga horaria no puede superar las 60 horas semanales."
            )
        return value

    def clean_capacitaciones_certificadas(self):
        return self.cleaned_data.get("capacitaciones_certificadas") or []

    def clean_grupo_pertenencia(self):
        return self.cleaned_data.get("grupo_pertenencia") or []

    def clean_lenguajes(self):
        return self.cleaned_data.get("lenguajes") or []

    def clean_tipo_discapacidad(self):
        return self.cleaned_data.get("tipo_discapacidad") or []


class IntervencionCentroInfanciaForm(forms.ModelForm):
    @staticmethod
    def _parse_selected_id(raw_value):
        return int(raw_value) if raw_value and str(raw_value).isdigit() else None

    def __init__(self, *args, **kwargs):
        destinatario_fijo_nombre = kwargs.pop("destinatario_fijo_nombre", None)
        hide_destinatario = kwargs.pop("hide_destinatario", False)
        super().__init__(*args, **kwargs)
        selected_tipo_id = getattr(self.instance, "tipo_intervencion_id", None)
        if self.is_bound:
            selected_tipo_id = self._parse_selected_id(
                self.data.get(self.add_prefix("tipo_intervencion"))
            )
        selected_subtipo_id = getattr(self.instance, "subintervencion_id", None)
        if self.is_bound:
            selected_subtipo_id = self._parse_selected_id(
                self.data.get(self.add_prefix("subintervencion"))
            )
        self.fields["tipo_intervencion"].queryset = TipoIntervencion.para_programas(
            *PROGRAMA_ALIASES_CENTRO_INFANCIA,
            include_ids=[selected_tipo_id] if selected_tipo_id else None,
        )
        self.fields["subintervencion"].queryset = SubIntervencion.para_tipo(
            selected_tipo_id,
            include_ids=[selected_subtipo_id] if selected_subtipo_id else None,
        )

        self.destinatario_fijo_instance = None
        self.destinatario_fijo_missing = False
        self.destinatario_fijo_nombre = destinatario_fijo_nombre
        if destinatario_fijo_nombre:
            destinatario_fijo = TipoDestinatario.objects.filter(
                nombre__iexact=destinatario_fijo_nombre
            ).first()
            if destinatario_fijo:
                self.destinatario_fijo_instance = destinatario_fijo
                self.fields["destinatario"].required = False
                self.fields["destinatario"].initial = destinatario_fijo.pk
                self.fields["destinatario"].queryset = TipoDestinatario.objects.filter(
                    pk=destinatario_fijo.pk
                )
            else:
                self.destinatario_fijo_missing = True
                self.fields["destinatario"].required = False
            if hide_destinatario:
                self.fields["destinatario"].widget = forms.HiddenInput()

        for field_name in [
            "tipo_intervencion",
            "subintervencion",
            "destinatario",
            "fecha",
            "forma_contacto",
            "observaciones",
            "documentacion",
        ]:
            css_class = "form-control"
            if field_name in {
                "tipo_intervencion",
                "subintervencion",
                "destinatario",
                "forma_contacto",
            }:
                css_class = "form-select"

            existing = self.fields[field_name].widget.attrs.get("class", "")
            self.fields[field_name].widget.attrs[
                "class"
            ] = f"{existing} {css_class}".strip()

        checkbox_existing = self.fields["tiene_documentacion"].widget.attrs.get(
            "class", ""
        )
        self.fields["tiene_documentacion"].widget.attrs[
            "class"
        ] = f"{checkbox_existing} form-check-input".strip()

    class Meta:
        model = IntervencionCentroInfancia
        fields = [
            "tipo_intervencion",
            "subintervencion",
            "destinatario",
            "fecha",
            "forma_contacto",
            "observaciones",
            "tiene_documentacion",
            "documentacion",
        ]
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date"}),
            "observaciones": forms.Textarea(attrs={"rows": 4}),
        }

    def clean(self):
        cleaned_data = super().clean()
        tipo_intervencion = cleaned_data.get("tipo_intervencion")
        subintervencion = cleaned_data.get("subintervencion")
        destinatario = cleaned_data.get("destinatario")

        if self.destinatario_fijo_instance:
            cleaned_data["destinatario"] = self.destinatario_fijo_instance
        elif self.destinatario_fijo_missing:
            self.add_error(
                "destinatario",
                f"No existe el destinatario requerido: {self.destinatario_fijo_nombre}.",
            )
        elif destinatario is None:
            self.add_error(
                "destinatario",
                "Debe seleccionar un destinatario.",
            )

        if not tipo_intervencion:
            return cleaned_data

        if (
            subintervencion
            and subintervencion.tipo_intervencion_id != tipo_intervencion.id
        ):
            self.add_error(
                "subintervencion",
                "La subintervención seleccionada no corresponde al tipo de intervención.",
            )
            return cleaned_data

        subintervenciones_disponibles = tipo_intervencion.subintervenciones.all()
        if subintervenciones_disponibles.exists():
            if not subintervencion:
                self.add_error(
                    "subintervencion", "Debe seleccionar una subintervención."
                )
        else:
            cleaned_data["subintervencion"] = None

        return cleaned_data
