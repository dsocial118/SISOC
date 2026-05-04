from django import forms
from django.core.cache import cache
from django.db.models import Q

from ciudadanos.models import Ciudadano, GrupoFamiliar
from core.models import Localidad, Municipio, Provincia

PROVINCIA_FILTER_CHOICES_CACHE_KEY = "ciudadanos:filtro:provincias:v1"
PROVINCIA_FILTER_CHOICES_CACHE_TTL = 60 * 60


def get_cached_provincia_filter_choices():
    """Devuelve choices cacheados para evitar reconstruir la lista por request."""

    cached_choices = cache.get(PROVINCIA_FILTER_CHOICES_CACHE_KEY)
    if cached_choices is not None:
        return cached_choices

    cached_choices = [
        (str(provincia.id), provincia.nombre)
        for provincia in Provincia.objects.only("id", "nombre").order_by("nombre")
    ]
    cache.set(
        PROVINCIA_FILTER_CHOICES_CACHE_KEY,
        cached_choices,
        PROVINCIA_FILTER_CHOICES_CACHE_TTL,
    )
    return cached_choices


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

        # Los campos de identidad/nombre/doc son opcionales a nivel form;
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
            cleaned["motivo_sin_dni"] = None
            cleaned["motivo_sin_dni_descripcion"] = ""
            cleaned["motivo_no_validacion_renaper"] = None
            cleaned["motivo_no_validacion_descripcion"] = ""
            for field in ("apellido", "nombre", "fecha_nacimiento", "documento"):
                if not cleaned.get(field):
                    self.add_error(field, "Este campo es obligatorio.")

        elif tipo == Ciudadano.TIPO_REGISTRO_SIN_DNI:
            cleaned["documento"] = None
            cleaned["motivo_no_validacion_renaper"] = None
            cleaned["motivo_no_validacion_descripcion"] = ""
            if not cleaned.get("motivo_sin_dni"):
                self.add_error(
                    "motivo_sin_dni",
                    "Debe indicar el motivo por el que no posee DNI.",
                )

        elif tipo == Ciudadano.TIPO_REGISTRO_DNI_NO_VALIDADO:
            cleaned["motivo_sin_dni"] = None
            cleaned["motivo_sin_dni_descripcion"] = ""
            if not cleaned.get("documento"):
                self.add_error(
                    "documento", "El DNI es obligatorio para este tipo de registro."
                )
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
    ESTADO_REVISION_FINALIZADA = "FINALIZADA"
    ESTADO_REVISION_PENDIENTE = "PENDIENTE"
    ESTADO_REVISION_TODOS = "TODOS"
    FILTERS_MODE_UI = "ui"
    FILTERS_MODE_API = "api"

    q = forms.CharField(
        label="Buscar",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Nombre o documento"}),
    )
    provincia = forms.TypedChoiceField(
        required=False,
        coerce=int,
        empty_value=None,
        choices=(),
    )
    tipo_registro = forms.ChoiceField(
        label="Estado identidad",
        required=False,
        choices=[("", "Todos")]
        + [
            (Ciudadano.TIPO_REGISTRO_ESTANDAR, "Estándar"),
            (Ciudadano.TIPO_REGISTRO_SIN_DNI, "Sin DNI"),
            (Ciudadano.TIPO_REGISTRO_DNI_NO_VALIDADO, "DNI no validado RENAPER"),
        ],
    )
    estado_revision = forms.ChoiceField(
        label="Estado de Revisión",
        required=False,
        choices=[
            (ESTADO_REVISION_FINALIZADA, "Finalizada"),
            (ESTADO_REVISION_PENDIENTE, "Pendiente"),
            (ESTADO_REVISION_TODOS, "Todos"),
        ],
        initial=ESTADO_REVISION_FINALIZADA,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["provincia"].choices = [
            ("", "Todas"),
            *get_cached_provincia_filter_choices(),
        ]
        self._filters_mode = self.FILTERS_MODE_UI
        self._estado_revision_explicito = False
        if not self.is_bound:
            self.initial.setdefault("estado_revision", self.ESTADO_REVISION_FINALIZADA)
        else:
            self._filters_mode = (
                self.data.get("filters_mode") or ""
            ).strip() or self.FILTERS_MODE_API
            self._estado_revision_explicito = bool(
                (self.data.get("estado_revision") or "").strip()
            )
            if not self._estado_revision_explicito:
                mutable_data = self.data.copy()
                mutable_data["estado_revision"] = (
                    self.ESTADO_REVISION_FINALIZADA
                    if self._filters_mode == self.FILTERS_MODE_UI
                    else self.ESTADO_REVISION_TODOS
                )
                self.data = mutable_data

    @property
    def estado_revision_fue_seleccionado_explicitamente(self):
        if not self.is_bound:
            return False
        return self._estado_revision_explicito

    def clean_provincia(self):
        provincia_id = self.cleaned_data.get("provincia")
        if not provincia_id:
            return None

        provincia = (
            Provincia.objects.only("id", "nombre").filter(pk=provincia_id).first()
        )
        if provincia is None:
            raise forms.ValidationError("Provincia inválida.")
        return provincia

    def clean_estado_revision(self):
        estado_revision = self.cleaned_data.get("estado_revision")
        if not estado_revision:
            if self._filters_mode == self.FILTERS_MODE_UI:
                return self.ESTADO_REVISION_FINALIZADA
            return None
        return estado_revision

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data["estado_revision_explicito"] = (
            self.estado_revision_fue_seleccionado_explicitamente
        )
        return cleaned_data
