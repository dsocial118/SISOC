from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator, RegexValidator

from ciudadanos.models import Ciudadano
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
    ObservacionCentroInfancia,
    Trabajador,
    normalizar_cuit,
)
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
    "IntervencionCentroInfanciaForm",
    "TrabajadorForm",
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
        for field_name in ["numero", "codigo_postal", "cuit_organizacion_gestiona"]:
            attrs = self.fields[field_name].widget.attrs
            attrs["inputmode"] = "numeric"
            attrs["pattern"] = r"\d*"

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
            "fecha_inicio": forms.DateInput(attrs={"type": "date"}),
            "meses_funcionamiento": forms.CheckboxSelectMultiple(),
            "dias_funcionamiento": forms.CheckboxSelectMultiple(),
        }


class NominaCentroInfanciaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["estado"].widget.attrs["class"] = "form-select"
        self.fields["observaciones"].widget.attrs["class"] = "form-control"

    class Meta:
        model = NominaCentroInfancia
        fields = ["estado", "observaciones"]
        widgets = {
            "observaciones": forms.Textarea(attrs={"rows": 3}),
        }


class NominaCentroInfanciaCreateForm(forms.ModelForm):
    ciudadano = forms.ModelChoiceField(
        queryset=Ciudadano.objects.all().order_by("apellido", "nombre"),
        empty_label="Seleccione un ciudadano",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["ciudadano"].widget.attrs["class"] = "form-select"
        self.fields["estado"].widget.attrs["class"] = "form-select"
        self.fields["observaciones"].widget.attrs["class"] = "form-control"

    class Meta:
        model = NominaCentroInfancia
        fields = ["ciudadano", "estado", "observaciones"]
        widgets = {
            "observaciones": forms.Textarea(attrs={"rows": 3}),
        }


class TrabajadorForm(forms.ModelForm):
    class Meta:
        model = Trabajador
        fields = ["nombre", "apellido", "telefono", "rol"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ["nombre", "apellido", "telefono"]:
            self.fields[field_name].widget.attrs["class"] = "form-control"
        self.fields["rol"].widget.attrs["class"] = "form-select"


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


class ObservacionCentroInfanciaForm(forms.ModelForm):
    class Meta:
        model = ObservacionCentroInfancia
        fields = ["observacion"]
        labels = {"observacion": "Observación"}
        widgets = {
            "observacion": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Describa la observación",
                }
            )
        }
