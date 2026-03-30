from django import forms
from django.core.validators import RegexValidator

from ciudadanos.models import Ciudadano
from core.models import Localidad, Municipio, Provincia
from intervenciones.constants import PROGRAMA_ALIASES_CENTRO_INFANCIA
from intervenciones.models.intervenciones import (
    SubIntervencion,
    TipoDestinatario,
    TipoIntervencion,
)
from organizaciones.models import Organizacion
from users.models import Profile
from centrodeinfancia.models import (
    CentroDeInfancia,
    DepartamentoIpi,
    IntervencionCentroInfancia,
    NominaCentroInfancia,
    ObservacionCentroInfancia,
    Trabajador,
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
        self._popular_campos_ubicacion()
        self._aplicar_provincia_usuario()
        self._aplicar_requeridos()
        self._aplicar_atributos_numericos()
        self._aplicar_campo_decil_ipi()

    def _aplicar_requeridos(self):
        for field_name in ["telefono", "telefono_referente"]:
            self.fields[field_name].required = True
            self.fields[field_name].error_messages["required"] = (
                "Este campo es obligatorio."
            )

    def _aplicar_atributos_numericos(self):
        # Campos estrictamente numéricos
        for field_name in ["numero"]:
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

    def _aplicar_campo_decil_ipi(self):
        self.fields["decil_ipi"].widget.attrs["readonly"] = True
        self.fields["decil_ipi"].widget.attrs["tabindex"] = "-1"

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

        self.fields["organizacion"].queryset = Organizacion.objects.all().order_by(
            "nombre"
        )
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
            self.fields["departamento"].queryset = DepartamentoIpi.objects.all().order_by(
                "nombre"
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

    class Meta:
        model = CentroDeInfancia
        fields = [
            "nombre",
            "organizacion",
            "provincia",
            "departamento",
            "municipio",
            "localidad",
            "calle",
            "numero",
            "telefono",
            "nombre_referente",
            "apellido_referente",
            "email_referente",
            "telefono_referente",
            "fecha_inicio",
        ]
        widgets = {
            "fecha_inicio": forms.DateInput(attrs={"type": "date"}),
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
