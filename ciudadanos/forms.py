from django import forms

from core.models import Localidad, Municipio, Provincia
from ciudadanos.models import Ciudadano, GrupoFamiliar


class CiudadanoForm(forms.ModelForm):
    fecha_nacimiento = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        error_messages={"invalid": "Ingrese una fecha válida."},
    )

    class Meta:
        model = Ciudadano
        fields = [
            "apellido",
            "nombre",
            "fecha_nacimiento",
            "tipo_documento",
            "documento",
            "sexo",
            "nacionalidad",
            "calle",
            "altura",
            "piso_departamento",
            "barrio",
            "provincia",
            "municipio",
            "localidad",
            "codigo_postal",
            "telefono",
            "telefono_alternativo",
            "email",
            "observaciones",
            "foto",
            "activo",
        ]
        widgets = {
            "observaciones": forms.Textarea(attrs={"rows": 3}),
            "activo": forms.CheckboxInput(
                attrs={"class": "form-check-input", "role": "switch"}
            ),
        }

    provincia = forms.ModelChoiceField(
        queryset=Provincia.objects.all(),
        required=False,
        label="Provincia",
    )
    municipio = forms.ModelChoiceField(
        queryset=Municipio.objects.all(),
        required=False,
        label="Municipio",
    )
    localidad = forms.ModelChoiceField(
        queryset=Localidad.objects.all(),
        required=False,
        label="Localidad",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap_styles()
        if "foto" in self.fields:
            self.fields["foto"].widget.attrs.update(
                {
                    "class": "d-none",
                    "id": "foto-input",
                }
            )
        self.fields["provincia"].queryset = Provincia.objects.all().order_by("nombre")
        self.fields["municipio"].queryset = Municipio.objects.none()
        self.fields["localidad"].queryset = Localidad.objects.none()

        if "municipio" in self.data:
            try:
                municipio_id = int(self.data.get("municipio"))
                self.fields["municipio"].queryset = Municipio.objects.filter(
                    id=municipio_id
                ).order_by("nombre")
            except (TypeError, ValueError):
                pass
        elif self.instance.pk and self.instance.municipio_id:
            self.fields["municipio"].queryset = Municipio.objects.filter(
                provincia=self.instance.provincia
            ).order_by("nombre")

        if "localidad" in self.data:
            try:
                localidad_id = int(self.data.get("localidad"))
                self.fields["localidad"].queryset = Localidad.objects.filter(
                    id=localidad_id
                ).order_by("nombre")
            except (TypeError, ValueError):
                pass
        elif self.instance.pk and self.instance.localidad_id:
            self.fields["localidad"].queryset = Localidad.objects.filter(
                municipio=self.instance.municipio
            ).order_by("nombre")

    def _apply_bootstrap_styles(self):
        text_like = (
            forms.TextInput,
            forms.NumberInput,
            forms.EmailInput,
            forms.URLInput,
            forms.PasswordInput,
            forms.DateInput,
            forms.TimeInput,
            forms.DateTimeInput,
            forms.Textarea,
        )
        select_like = (forms.Select, forms.SelectMultiple)
        for field in self.fields.values():
            widget = field.widget
            css = widget.attrs.get("class", "")
            if isinstance(widget, text_like):
                widget.attrs["class"] = f"{css} form-control".strip()
            elif isinstance(widget, select_like):
                widget.attrs["class"] = f"{css} form-select".strip()
            elif isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = f"{css} form-check-input".strip()


class GrupoFamiliarForm(forms.ModelForm):
    class Meta:
        model = GrupoFamiliar
        fields = [
            "ciudadano_2",
            "vinculo",
            "estado_relacion",
            "conviven",
            "cuidador_principal",
            "observaciones",
        ]
        widgets = {
            "observaciones": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, ciudadano: Ciudadano, *args, **kwargs):
        self.ciudadano = ciudadano
        super().__init__(*args, **kwargs)
        self.fields["ciudadano_2"].queryset = Ciudadano.objects.exclude(pk=ciudadano.pk)
        self.fields["ciudadano_2"].label = "Familiar"

    def clean_ciudadano_2(self):
        familiar = self.cleaned_data["ciudadano_2"]
        if familiar == self.ciudadano:
            raise forms.ValidationError("No puede autoreferenciarse.")
        return familiar

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.ciudadano_1 = self.ciudadano
        if commit:
            instance.save()
        return instance


class CiudadanoFiltroForm(forms.Form):
    q = forms.CharField(
        label="Buscar",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Nombre o documento"}),
    )
    provincia = forms.ModelChoiceField(
        queryset=Provincia.objects.all(), required=False, empty_label="Todas"
    )
