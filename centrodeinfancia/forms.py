from django import forms

from ciudadanos.models import Ciudadano
from core.models import Localidad, Municipio, Provincia
from intervenciones.constants import PROGRAMA_ALIASES_CENTRO_INFANCIA
from intervenciones.models.intervenciones import TipoDestinatario, TipoIntervencion
from organizaciones.models import Organizacion
from users.models import Profile
from centrodeinfancia.models import (
    CentroDeInfancia,
    IntervencionCentroInfancia,
    NominaCentroInfancia,
    ObservacionCentroInfancia,
    Trabajador,
)
from centrodeinfancia.forms_formulario_cdi import (
    FormularioCDIForm,
    build_fixed_initial_rows,
    build_articulation_formset_class,
    build_room_distribution_formset_class,
    build_waitlist_formset_class,
)

__all__ = [
    "CentroDeInfanciaForm",
    "NominaCentroInfanciaForm",
    "NominaCentroInfanciaCreateForm",
    "IntervencionCentroInfanciaForm",
    "TrabajadorForm",
    "FormularioCDIForm",
    "build_fixed_initial_rows",
    "build_articulation_formset_class",
    "build_room_distribution_formset_class",
    "build_waitlist_formset_class",
]


class CentroDeInfanciaForm(forms.ModelForm):

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

    def _popular_campos_ubicacion(self):
        def parse_pk(value):
            return int(value) if value and str(value).isdigit() else None

        provincia = Provincia.objects.filter(
            pk=parse_pk(self.data.get(self.add_prefix("provincia")))
        ).first() or getattr(self.instance, "provincia", None)
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
            self.fields["municipio"].queryset = Municipio.objects.filter(
                provincia=provincia
            ).order_by("nombre")
        else:
            self.fields["municipio"].queryset = Municipio.objects.all().order_by(
                "nombre"
            )
            self.fields["localidad"].queryset = Localidad.objects.all().order_by(
                "nombre"
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

    class Meta:
        model = CentroDeInfancia
        fields = [
            "nombre",
            "organizacion",
            "provincia",
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
    def __init__(self, *args, **kwargs):
        destinatario_fijo_nombre = kwargs.pop("destinatario_fijo_nombre", None)
        hide_destinatario = kwargs.pop("hide_destinatario", False)
        super().__init__(*args, **kwargs)
        selected_tipo_id = getattr(self.instance, "tipo_intervencion_id", None)
        self.fields["tipo_intervencion"].queryset = TipoIntervencion.para_programas(
            *PROGRAMA_ALIASES_CENTRO_INFANCIA,
            include_ids=[selected_tipo_id] if selected_tipo_id else None,
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
