from django import forms
from django.db.models import Q

from core.models import Localidad, Municipio, Provincia
from ciudadanos.models import Ciudadano, GrupoFamiliar


class CiudadanoForm(forms.ModelForm):
    fecha_nacimiento = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        required=False,
        error_messages={"invalid": "Ingrese una fecha válida."},
    )

    class Meta:
        model = Ciudadano
        fields = [
            "tipo_registro_identidad",
            "apellido",
            "nombre",
            "fecha_nacimiento",
            "tipo_documento",
            "documento",
            "motivo_sin_dni",
            "motivo_sin_dni_descripcion",
            "motivo_no_validacion_renaper",
            "motivo_no_validacion_descripcion",
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
            "motivo_sin_dni_descripcion": forms.Textarea(attrs={"rows": 2}),
            "motivo_no_validacion_descripcion": forms.Textarea(attrs={"rows": 2}),
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

        # Los campos de identidad/nombre/doc son opcionales a nivel form —
        # la obligatoriedad se valida condicionalmente en clean() según
        # tipo_registro_identidad.
        for field_name in (
            "apellido",
            "nombre",
            "fecha_nacimiento",
            "documento",
            "motivo_sin_dni",
            "motivo_sin_dni_descripcion",
            "motivo_no_validacion_renaper",
            "motivo_no_validacion_descripcion",
        ):
            if field_name in self.fields:
                self.fields[field_name].required = False

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

    def clean(self):
        cleaned = super().clean()
        tipo = cleaned.get("tipo_registro_identidad", Ciudadano.TIPO_REGISTRO_ESTANDAR)

        if tipo == Ciudadano.TIPO_REGISTRO_ESTANDAR:
            for field in ("apellido", "nombre", "fecha_nacimiento", "documento"):
                if not cleaned.get(field):
                    self.add_error(field, "Este campo es obligatorio.")

        elif tipo == Ciudadano.TIPO_REGISTRO_SIN_DNI:
            if not cleaned.get("motivo_sin_dni"):
                self.add_error(
                    "motivo_sin_dni",
                    "Debe indicar el motivo por el que no posee DNI.",
                )

        elif tipo == Ciudadano.TIPO_REGISTRO_DNI_NO_VALIDADO:
            if not cleaned.get("documento"):
                self.add_error("documento", "El DNI es obligatorio para este tipo de registro.")
            if not cleaned.get("motivo_no_validacion_renaper"):
                self.add_error(
                    "motivo_no_validacion_renaper",
                    "Debe indicar el motivo por el que RENAPER no validó el documento.",
                )

        return cleaned

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
    ciudadano_2 = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Buscar por documento (4+ dígitos)",
                "autocomplete": "off",
            }
        ),
        label="Familiar",
    )

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
        for name in ("vinculo", "estado_relacion"):
            css = self.fields[name].widget.attrs.get("class", "")
            self.fields[name].widget.attrs["class"] = f"{css} form-select".strip()
        for name in ("observaciones",):
            css = self.fields[name].widget.attrs.get("class", "")
            self.fields[name].widget.attrs["class"] = f"{css} form-control".strip()
        for name in ("conviven", "cuidador_principal"):
            css = self.fields[name].widget.attrs.get("class", "")
            self.fields[name].widget.attrs["class"] = f"{css} form-check-input".strip()

    def clean_ciudadano_2(self):
        familiar_id = self.cleaned_data.get("ciudadano_2")
        if not familiar_id:
            raise forms.ValidationError("Debe seleccionar un familiar.")

        try:
            familiar = Ciudadano.objects.get(pk=int(familiar_id))
        except (Ciudadano.DoesNotExist, ValueError, TypeError) as exc:
            raise forms.ValidationError("Familiar no válido.") from exc

        if familiar == self.ciudadano:
            raise forms.ValidationError("No puede autoreferenciarse.")

        ya_existe = GrupoFamiliar.objects.filter(
            Q(ciudadano_1=self.ciudadano, ciudadano_2=familiar)
            | Q(ciudadano_1=familiar, ciudadano_2=self.ciudadano)
        ).exists()
        if ya_existe:
            raise forms.ValidationError(
                "Ya existe una relación registrada con este familiar."
            )
        return familiar

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.ciudadano_1 = self.ciudadano
        instance.ciudadano_2 = self.cleaned_data["ciudadano_2"]
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
    tipo_registro = forms.ChoiceField(
        label="Tipo de registro",
        required=False,
        choices=[("", "Todos")]
        + [
            (Ciudadano.TIPO_REGISTRO_ESTANDAR, "Estándar"),
            (Ciudadano.TIPO_REGISTRO_SIN_DNI, "Sin DNI"),
            (Ciudadano.TIPO_REGISTRO_DNI_NO_VALIDADO, "DNI no validado RENAPER"),
        ],
    )
