from django import forms

from ciudadanos.models import Ciudadano
from core.models import Localidad, Municipio, Provincia
from organizaciones.models import Organizacion
from centrodeinfancia.models import (
    CentroDeInfancia,
    IntervencionCentroInfancia,
    NominaCentroInfancia,
    ObservacionCentroInfancia,
)


class CentroDeInfanciaForm(forms.ModelForm):

    @staticmethod
    def _obtener_provincia_usuario(user):
        if not user:
            return None
        try:
            profile = user.profile
        except Exception:
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
        self._aplicar_provincia_usuario_en_alta()

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

    def _aplicar_provincia_usuario_en_alta(self):
        if not self.lock_provincia_from_user or self.instance.pk:
            return

        provincia_usuario = self._obtener_provincia_usuario(self.current_user)
        if not provincia_usuario:
            self.fields["provincia"].queryset = Provincia.objects.all().order_by("nombre")
            self.fields["provincia"].disabled = False
            return

        self.fields["provincia"].queryset = Provincia.objects.filter(
            pk=provincia_usuario.pk
        )
        self.fields["provincia"].initial = provincia_usuario
        self.fields["provincia"].disabled = True
        self.fields["municipio"].queryset = Municipio.objects.filter(
            provincia=provincia_usuario
        ).order_by("nombre")

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
            "telefono",
            "nombre_referente",
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


class IntervencionCentroInfanciaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
            self.fields[field_name].widget.attrs["class"] = (
                f"{existing} {css_class}".strip()
            )

        checkbox_existing = self.fields["tiene_documentacion"].widget.attrs.get(
            "class", ""
        )
        self.fields["tiene_documentacion"].widget.attrs["class"] = (
            f"{checkbox_existing} form-check-input".strip()
        )

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
