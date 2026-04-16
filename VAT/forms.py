# pylint: disable=too-many-lines

import re
from datetime import date

from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.forms import BaseInlineFormSet, inlineformset_factory
from ciudadanos.models import Ciudadano
from core.models import Dia, Sexo
from core.models import Localidad, Programa
from VAT.models import (
    Centro,
    ModalidadInstitucional,
    Sector,
    Subsector,
    TituloReferencia,
    ModalidadCursada,
    PlanVersionCurricular,
    InscripcionOferta,
    InstitucionContacto,
    InstitucionIdentificadorHist,
    InstitucionUbicacion,
    OfertaInstitucional,
    VoucherParametria,
    Curso,
    ComisionCurso,
    Comision,
    ComisionHorario,
    Inscripcion,
    Evaluacion,
    ResultadoEvaluacion,
)


class VoucherParametriaSelectMultiple(forms.SelectMultiple):
    def create_option(  # pylint: disable=too-many-arguments
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        option = super().create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs
        )
        if value is not None and hasattr(value, "instance") and value.instance:
            option["attrs"]["data-programa-id"] = str(value.instance.programa_id)
        return option


def _normalize_related_ids(values):
    return [value for value in dict.fromkeys(values or []) if value]


def _get_including_deleted_manager(model_class):
    """Devuelve el manager publico con borrados incluidos cuando existe."""

    return getattr(model_class, "all_objects", model_class.objects)


def build_plan_estudio_queryset_for_centro(
    centro_provincia_id=None, include_plan_ids=None
):
    base_queryset = PlanVersionCurricular.objects.filter(activo=True)
    if centro_provincia_id:
        base_queryset = base_queryset.filter(provincia_id=centro_provincia_id)
    else:
        base_queryset = PlanVersionCurricular.objects.none()

    include_plan_ids = _normalize_related_ids(include_plan_ids)
    if include_plan_ids:
        base_queryset = PlanVersionCurricular.objects.filter(
            Q(pk__in=include_plan_ids) | Q(pk__in=base_queryset.values("pk"))
        )

    return base_queryset.select_related("sector", "modalidad_cursada").order_by(
        "sector__nombre",
        "modalidad_cursada__nombre",
    )


def build_voucher_parametria_queryset(include_voucher_ids=None):
    base_queryset = VoucherParametria.objects.filter(activa=True)
    include_voucher_ids = _normalize_related_ids(include_voucher_ids)
    if include_voucher_ids:
        base_queryset = VoucherParametria.objects.filter(
            Q(pk__in=include_voucher_ids) | Q(pk__in=base_queryset.values("pk"))
        )

    return base_queryset.select_related("programa").order_by("nombre")


def build_curso_queryset_for_centros(centro_ids, include_curso_ids=None):
    base_queryset = Curso.objects.filter(
        centro_id__in=_normalize_related_ids(centro_ids)
    )
    include_curso_ids = _normalize_related_ids(include_curso_ids)
    if include_curso_ids:
        manager = _get_including_deleted_manager(Curso)
        base_queryset = manager.filter(
            Q(pk__in=include_curso_ids) | Q(pk__in=base_queryset.values("pk"))
        )

    return base_queryset.select_related("centro").order_by("nombre")


def build_ubicacion_queryset_for_centros(centro_ids, include_ubicacion_ids=None):
    base_queryset = InstitucionUbicacion.objects.filter(
        centro_id__in=_normalize_related_ids(centro_ids)
    )
    include_ubicacion_ids = _normalize_related_ids(include_ubicacion_ids)
    if include_ubicacion_ids:
        manager = _get_including_deleted_manager(InstitucionUbicacion)
        base_queryset = manager.filter(
            Q(pk__in=include_ubicacion_ids) | Q(pk__in=base_queryset.values("pk"))
        )

    return base_queryset.select_related("localidad").order_by(
        "-es_principal",
        "rol_ubicacion",
    )


class ReferenteModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        full_name = f"{obj.first_name} {obj.last_name}".strip()
        if full_name:
            return f"{obj.username} - {full_name}"
        return obj.username


HORAS_DEL_DIA = [(f"{h:02d}:00", f"{h:02d}:00") for h in range(0, 24)] + [
    (f"{h:02d}:30", f"{h:02d}:30") for h in range(0, 24)
]

TIPO_GESTION_CHOICES = [
    ("", "Seleccionar tipo de gestión..."),
    ("Estatal", "Estatal"),
    ("Privada", "Privada"),
]

CLASE_INSTITUCION_CHOICES = [
    ("", "Seleccionar clase de institución..."),
    ("Formación Profesional", "Formación Profesional"),
    ("Secundario Técnico", "Secundario Técnico"),
    ("Superior Formación Docente", "Superior Formación Docente"),
    ("Superior Técnico", "Superior Técnico"),
    ("Secundario Orientado", "Secundario Orientado"),
]

ESTADO_ETP_CHOICES = [
    ("", "Seleccionar estado ETP..."),
    ("Institución de ETP", "Institución de ETP"),
    (
        "Institución de Otro Nivel y/o Modalidad",
        "Institución de Otro Nivel y/o Modalidad",
    ),
]

NORMATIVA_TIPO_CHOICES = [
    ("", "Seleccionar tipo..."),
    ("Resolución", "Resolución"),
    ("Disposición", "Disposición"),
]

NORMATIVA_ANIO_CHOICES = [("", "Seleccionar año...")] + [
    (str(year), str(year)) for year in range(date.today().year, 1949, -1)
]

NORMATIVA_STORAGE_SEPARATOR = " || "
REFERENTE_GROUP_NAMES = ("CFP",)


def _clean_non_empty_text(value, field_label):
    cleaned_value = (value or "").strip()
    if not cleaned_value:
        raise ValidationError(f"{field_label} no puede contener solo espacios.")
    return cleaned_value


def _clean_numeric_text(value, field_label, min_length=None, max_length=None):
    cleaned_value = (value or "").strip()
    if cleaned_value and not cleaned_value.isdigit():
        raise ValidationError(f"{field_label} debe contener solo números.")
    if min_length and len(cleaned_value) < min_length:
        raise ValidationError(
            f"{field_label} debe tener al menos {min_length} dígitos."
        )
    if max_length and len(cleaned_value) > max_length:
        raise ValidationError(
            f"{field_label} no puede superar los {max_length} dígitos."
        )
    return cleaned_value


def _clean_phone_text(value, field_label):
    cleaned_value = (value or "").strip()
    if cleaned_value and not re.fullmatch(r"[0-9+()\-\s]+", cleaned_value):
        raise ValidationError(
            f"{field_label} solo puede incluir números, espacios, paréntesis o guiones."
        )
    return cleaned_value


def _split_normativa_value(value):
    cleaned_value = (value or "").strip()
    if not cleaned_value:
        return "", ""

    if NORMATIVA_STORAGE_SEPARATOR in cleaned_value:
        normativa_texto, normativa_estructurada = cleaned_value.split(
            NORMATIVA_STORAGE_SEPARATOR, 1
        )
        return normativa_texto.strip(), normativa_estructurada.strip()

    if _parse_normativa_match(cleaned_value):
        return "", cleaned_value

    return cleaned_value, ""


def _parse_normativa_match(value):
    return re.fullmatch(
        r"(Resolución|Resolucion|Disposición|Disposicion)\s+(\d+)\s*/\s*(\d{4})",
        value or "",
        flags=re.IGNORECASE,
    )


def _parse_normativa_value(value):
    _, structured_value = _split_normativa_value(value)
    if not structured_value:
        return "", "", ""

    match = _parse_normativa_match(structured_value)
    if not match:
        return "", "", ""

    tipo_raw, numero, anio = match.groups()
    tipo = "Disposición" if tipo_raw.lower().startswith("dis") else "Resolución"
    return tipo, numero, anio


def _build_normativa_value(
    normativa_texto, normativa_tipo, normativa_numero, normativa_anio
):
    normativa_texto = (normativa_texto or "").strip()

    structured_value = ""
    if normativa_tipo and normativa_numero and normativa_anio:
        structured_value = f"{normativa_tipo} {normativa_numero}/{normativa_anio}"

    if normativa_texto and structured_value:
        return f"{normativa_texto}{NORMATIVA_STORAGE_SEPARATOR}{structured_value}"

    return normativa_texto or structured_value


def _validate_normativa_texto(value):
    cleaned_value = (value or "").strip()
    if cleaned_value and NORMATIVA_STORAGE_SEPARATOR in cleaned_value:
        raise ValidationError("La normativa libre no puede contener la secuencia '||'.")
    return cleaned_value


def _has_contact_data(cleaned_data):
    tracked_fields = [
        "nombre_contacto",
        "rol_area",
        "documento",
        "telefono_contacto",
        "email_contacto",
    ]
    return any(cleaned_data.get(field_name) for field_name in tracked_fields)


def _validate_contact_channels(cleaned_data):
    if not _has_contact_data(cleaned_data):
        return

    if cleaned_data.get("email_contacto") or cleaned_data.get("telefono_contacto"):
        return

    raise ValidationError(
        "Debe informar al menos un teléfono o correo electrónico para el contacto."
    )


def _assign_contact_type_and_value(instance, cleaned_data):
    email_contacto = cleaned_data.get("email_contacto")
    telefono_contacto = cleaned_data.get("telefono_contacto")
    instance.tipo = "email" if email_contacto else "telefono"
    instance.valor = email_contacto or telefono_contacto
    return instance


class CentroForm(forms.ModelForm):
    class Meta:
        model = Centro
        fields = [
            "nombre",
            "codigo",
            "provincia",
            "municipio",
            "localidad",
            "calle",
            "numero",
            "domicilio_actividad",
            "codigo_postal",
            "lote",
            "manzana",
            "entre_calles",
            "telefono",
            "celular",
            "correo",
            "sitio_web",
            "nombre_referente",
            "apellido_referente",
            "telefono_referente",
            "correo_referente",
            "referente",
            "activo",
            "tipo_gestion",
            "clase_institucion",
            "situacion",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["referente"].queryset = (
            User.objects.filter(groups__name__in=REFERENTE_GROUP_NAMES)
            .only("id", "username", "first_name", "last_name")
            .distinct()
        )
        self.fields["referente"].error_messages[
            "invalid_choice"
        ] = "El referente seleccionado debe tener un rol valido de referente VAT."
        self.referente_search_options = [
            {
                "id": str(user.pk),
                "username": user.username,
                "label": self.fields["referente"].label_from_instance(user),
            }
            for user in self.fields["referente"].queryset.order_by("username")
        ]

    def clean_referente(self):
        referente = self.cleaned_data.get("referente")
        if (
            referente
            and not referente.groups.filter(name__in=REFERENTE_GROUP_NAMES).exists()
        ):
            raise ValidationError(
                "El referente seleccionado debe tener un rol valido de referente VAT."
            )
        return referente


class CentroAltaForm(CentroForm):
    nombre = forms.CharField(
        label="Denominación de la institución",
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Nombre oficial de la institución",
            }
        ),
    )
    codigo = forms.CharField(
        label="Clave Única de Establecimiento (CUE)",
        max_length=9,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Ej: 500144900",
                "inputmode": "numeric",
            }
        ),
        help_text="Debe contener solo números.",
    )
    provincia = forms.ModelChoiceField(
        queryset=Centro._meta.get_field(
            "provincia"
        ).remote_field.model.objects.order_by("nombre"),
        label="Jurisdicción",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    municipio = forms.ModelChoiceField(
        queryset=Centro._meta.get_field(
            "municipio"
        ).remote_field.model.objects.order_by("nombre"),
        label="Municipio / Partido",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    localidad = forms.ModelChoiceField(
        queryset=Localidad.objects.order_by("nombre"),
        label="Localidad",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    domicilio_actividad = forms.CharField(
        label="Dirección completa",
        max_length=200,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Referencia general del domicilio",
            }
        ),
    )
    calle = forms.CharField(
        label="Calle",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    numero = forms.IntegerField(
        label="Altura",
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    codigo_postal = forms.CharField(
        label="Código Postal",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "inputmode": "numeric"}),
    )
    lote = forms.CharField(
        label="Lote",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    manzana = forms.CharField(
        label="Manzana",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    entre_calles = forms.CharField(
        label="Entre calles",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    telefono = forms.CharField(
        label="Teléfono institucional",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    celular = forms.CharField(
        label="Teléfono alternativo",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    correo = forms.EmailField(
        label="Correo electrónico institucional",
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )
    sitio_web = forms.URLField(
        label="Sitio web institucional",
        required=False,
        widget=forms.URLInput(attrs={"class": "form-control"}),
    )
    tipo_gestion = forms.ChoiceField(
        label="Tipo de gestión",
        choices=TIPO_GESTION_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    clase_institucion = forms.ChoiceField(
        label="Clase de institución",
        choices=CLASE_INSTITUCION_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    situacion = forms.ChoiceField(
        label="Estado ETP",
        choices=ESTADO_ETP_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    referente = ReferenteModelChoiceField(
        queryset=User.objects.none(),
        label="Referente",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    autoridad_dni = forms.CharField(
        label="Documento del director/a (DNI)",
        max_length=20,
        widget=forms.TextInput(attrs={"class": "form-control", "inputmode": "numeric"}),
    )

    class Meta(CentroForm.Meta):
        fields = CentroForm.Meta.fields

    def __init__(self, *args, **kwargs):
        hide_provincia = kwargs.pop("hide_provincia", False)
        provincia_inicial = kwargs.pop("provincia_inicial", None)
        super().__init__(*args, **kwargs)
        self.fields["activo"].required = False
        for hidden_field in [
            "nombre_referente",
            "apellido_referente",
            "telefono_referente",
            "correo_referente",
        ]:
            self.fields[hidden_field].required = False
            self.fields[hidden_field].widget = forms.HiddenInput()
        self.fields["autoridad_dni"].required = False
        self.fields["autoridad_dni"].widget = forms.HiddenInput()
        self.fields["referente"].widget.attrs["class"] = "referente-hidden-select"
        self.fields["referente"].widget.attrs["tabindex"] = "-1"
        self.fields["referente"].empty_label = "Seleccionar referente..."
        self.fields["provincia"].empty_label = "Seleccionar jurisdicción..."
        self.fields["municipio"].empty_label = "Seleccionar municipio..."
        self.fields["localidad"].empty_label = "Seleccionar localidad..."

        if hide_provincia:
            provincia_pk = (
                provincia_inicial.pk
                if getattr(provincia_inicial, "pk", None)
                else provincia_inicial
            )
            self.fields["provincia"].required = False
            self.fields["provincia"].widget = forms.HiddenInput()
            self.fields["provincia"].empty_label = None
            if provincia_pk:
                self.fields["provincia"].queryset = self.fields[
                    "provincia"
                ].queryset.filter(pk=provincia_pk)
                self.initial.setdefault("provincia", provincia_pk)

        provincia_value = (
            self.data.get("provincia")
            or self.initial.get("provincia")
            or getattr(self.instance, "provincia_id", None)
        )
        if provincia_value:
            self.fields["municipio"].queryset = self.fields[
                "municipio"
            ].queryset.filter(provincia_id=provincia_value)

        municipio_value = (
            self.data.get("municipio")
            or self.initial.get("municipio")
            or getattr(self.instance, "municipio_id", None)
        )
        if municipio_value:
            self.fields["localidad"].queryset = self.fields[
                "localidad"
            ].queryset.filter(municipio_id=municipio_value)
        elif provincia_value:
            self.fields["localidad"].queryset = self.fields[
                "localidad"
            ].queryset.filter(municipio__provincia_id=provincia_value)

    def clean_nombre(self):
        return _clean_non_empty_text(self.cleaned_data.get("nombre"), "La denominación")

    def clean_codigo(self):
        return _clean_numeric_text(
            self.cleaned_data.get("codigo"),
            "El CUE",
            min_length=9,
            max_length=9,
        )

    def clean_domicilio_actividad(self):
        return _clean_non_empty_text(
            self.cleaned_data.get("domicilio_actividad"),
            "La dirección completa",
        )

    def clean_codigo_postal(self):
        return _clean_numeric_text(
            self.cleaned_data.get("codigo_postal"),
            "El código postal",
            max_length=20,
        )

    def clean_telefono(self):
        return _clean_phone_text(
            self.cleaned_data.get("telefono"),
            "El teléfono institucional",
        )

    def clean_celular(self):
        return _clean_phone_text(
            self.cleaned_data.get("celular"),
            "El teléfono alternativo",
        )

    def clean_telefono_referente(self):
        return _clean_phone_text(
            self.cleaned_data.get("telefono_referente"),
            "El teléfono del director/a",
        )

    def clean_autoridad_dni(self):
        return _clean_numeric_text(
            self.cleaned_data.get("autoridad_dni"),
            "El DNI del director/a",
            max_length=20,
        )


class BaseInstitucionContactoAltaFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return

        contactos_principales = 0
        tracked_fields = [
            "nombre_contacto",
            "rol_area",
            "documento",
            "telefono_contacto",
            "email_contacto",
        ]

        for form in self.forms:
            if not getattr(form, "cleaned_data", None):
                continue
            if getattr(self, "can_delete", False) and form.cleaned_data.get("DELETE"):
                continue
            if not any(
                form.cleaned_data.get(field_name) for field_name in tracked_fields
            ):
                continue

            if form.cleaned_data.get("es_principal"):
                contactos_principales += 1

        if contactos_principales > 1:
            raise ValidationError("Solo puede existir un contacto principal.")


class InstitucionContactoAltaForm(forms.ModelForm):
    nombre_contacto = forms.CharField(
        label="Nombre y apellido del responsable",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    rol_area = forms.CharField(
        label="Rol / Área",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    documento = forms.CharField(
        label="Documento",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "inputmode": "numeric",
                "pattern": "[0-9]*",
                "maxlength": "20",
                "oninput": "this.value=this.value.replace(/\\D/g, '')",
            }
        ),
    )
    telefono_contacto = forms.CharField(
        label="Teléfono",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    email_contacto = forms.EmailField(
        label="Correo electrónico",
        required=False,
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )
    es_principal = forms.BooleanField(
        label="Contacto principal",
        required=False,
        widget=forms.HiddenInput(),
    )

    class Meta:
        model = InstitucionContacto
        fields = [
            "nombre_contacto",
            "rol_area",
            "documento",
            "telefono_contacto",
            "email_contacto",
            "es_principal",
        ]

    def clean_nombre_contacto(self):
        value = self.cleaned_data.get("nombre_contacto")
        if not value:
            return ""
        return _clean_non_empty_text(value, "El nombre del contacto")

    def clean_rol_area(self):
        value = self.cleaned_data.get("rol_area")
        if not value:
            return ""
        return _clean_non_empty_text(value, "El rol o área")

    def clean_telefono_contacto(self):
        value = self.cleaned_data.get("telefono_contacto")
        if not value:
            return ""
        return _clean_phone_text(value, "El teléfono del contacto")

    def clean_documento(self):
        return _clean_numeric_text(
            self.cleaned_data.get("documento"),
            "El documento",
            max_length=20,
        )

    def clean(self):
        cleaned_data = super().clean()
        _validate_contact_channels(cleaned_data)
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance = _assign_contact_type_and_value(instance, self.cleaned_data)
        if commit:
            instance.save()
        return instance


InstitucionContactoAltaFormSet = inlineformset_factory(
    Centro,
    InstitucionContacto,
    form=InstitucionContactoAltaForm,
    formset=BaseInstitucionContactoAltaFormSet,
    extra=1,
    can_delete=False,
)


class ModalidadInstitucionalForm(forms.ModelForm):
    nombre = forms.CharField(
        label="Nombre de la Modalidad",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Ej. Presencial, Virtual, Semipresencial",
            }
        ),
    )
    descripcion = forms.CharField(
        label="Descripción",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "placeholder": "Descripción detallada de la modalidad",
                "rows": 4,
            }
        ),
    )
    activo = forms.BooleanField(
        label="Activo",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    class Meta:
        model = ModalidadInstitucional
        fields = ["nombre", "descripcion", "activo"]


class SectorForm(forms.ModelForm):
    nombre = forms.CharField(
        label="Nombre del Sector",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    descripcion = forms.CharField(
        label="Descripción",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 4}),
    )

    class Meta:
        model = Sector
        fields = ["nombre", "descripcion"]


class SubsectorForm(forms.ModelForm):
    sector = forms.ModelChoiceField(
        queryset=Sector.objects.all(),
        label="Sector",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    nombre = forms.CharField(
        label="Nombre del Subsector",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    descripcion = forms.CharField(
        label="Descripción",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 4}),
    )

    class Meta:
        model = Subsector
        fields = ["sector", "nombre", "descripcion"]


class TituloReferenciaForm(forms.ModelForm):
    nombre = forms.CharField(
        label="Nombre del Título",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    codigo_referencia = forms.CharField(
        label="Código de Referencia",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    descripcion = forms.CharField(
        label="Descripción",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 4}),
    )
    activo = forms.BooleanField(
        label="Activo",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    plan_estudio = forms.ModelChoiceField(
        queryset=PlanVersionCurricular.objects.filter(activo=True),
        label="Plan de Estudio",
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    class Meta:
        model = TituloReferencia
        fields = [
            "plan_estudio",
            "nombre",
            "codigo_referencia",
            "descripcion",
            "activo",
        ]


class ModalidadCursadaForm(forms.ModelForm):
    nombre = forms.CharField(
        label="Nombre de la Modalidad",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    descripcion = forms.CharField(
        label="Descripción",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 4}),
    )
    activo = forms.BooleanField(
        label="Activo",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    class Meta:
        model = ModalidadCursada
        fields = ["nombre", "descripcion", "activo"]


class PlanVersionCurricularForm(forms.ModelForm):
    nombre = forms.CharField(
        label="Nombre",
        max_length=200,
        strip=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Nombre del plan curricular",
            }
        ),
    )
    sector = forms.ModelChoiceField(
        queryset=Sector.objects.all(),
        label="Sector",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    subsector = forms.ModelChoiceField(
        queryset=Subsector.objects.all(),
        label="Subsector",
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    modalidad_cursada = forms.ModelChoiceField(
        queryset=ModalidadCursada.objects.all(),
        label="Modalidad",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    normativa_tipo = forms.ChoiceField(
        label="Normativa - Tipo",
        required=False,
        choices=NORMATIVA_TIPO_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    normativa_numero = forms.CharField(
        label="Normativa - Número",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "inputmode": "numeric"}),
    )
    normativa_anio = forms.ChoiceField(
        label="Normativa - Año",
        required=False,
        choices=NORMATIVA_ANIO_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    horas_reloj = forms.IntegerField(
        label="Horas Reloj",
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    nivel_requerido = forms.ChoiceField(
        label="Nivel Requerido",
        required=False,
        choices=[
            ("", "---------"),
            ("sin_requisito", "Sin requisito"),
            ("primario_incompleto", "Primario incompleto"),
            ("primario_completo", "Primario completo"),
            ("secundario_incompleto", "Secundario incompleto"),
            ("secundario_completo", "Secundario completo"),
        ],
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    nivel_certifica = forms.ChoiceField(
        label="Nivel que Certifica",
        required=False,
        choices=[
            ("", "---------"),
            ("nivel_1", "Certificado Nivel I"),
            ("nivel_2", "Certificado Nivel II"),
            ("nivel_3", "Certificado Nivel III"),
            ("sin_nivel", "Sin nivel"),
        ],
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    activo = forms.BooleanField(
        label="Activo",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    class Meta:
        model = PlanVersionCurricular
        fields = [
            "nombre",
            "sector",
            "subsector",
            "modalidad_cursada",
            "horas_reloj",
            "nivel_requerido",
            "nivel_certifica",
            "activo",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        sector_id = None
        self.normativa_texto_actual = ""

        self.initial["nombre"] = (
            self.data.get("nombre") if self.is_bound else (self.instance.nombre or "")
        )

        if self.data.get("sector"):
            sector_id = self.data.get("sector")
        elif self.instance and self.instance.pk and self.instance.sector_id:
            sector_id = self.instance.sector_id
        elif self.initial.get("sector"):
            sector = self.initial.get("sector")
            sector_id = sector.id if isinstance(sector, Sector) else sector

        if sector_id:
            self.fields["subsector"].queryset = Subsector.objects.filter(
                sector_id=sector_id
            ).order_by("nombre")
        else:
            self.fields["subsector"].queryset = Subsector.objects.none()

        if not self.is_bound:
            normativa_texto, _ = _split_normativa_value(self.instance.normativa)
            normativa_tipo, normativa_numero, normativa_anio = _parse_normativa_value(
                self.instance.normativa
            )
            self.normativa_texto_actual = normativa_texto
            self.initial.setdefault("normativa_tipo", normativa_tipo)
            self.initial.setdefault("normativa_numero", normativa_numero)
            self.initial.setdefault("normativa_anio", normativa_anio)
        elif self.instance and self.instance.pk:
            normativa_texto, _ = _split_normativa_value(self.instance.normativa)
            self.normativa_texto_actual = normativa_texto

    def clean_nombre(self):
        return _clean_non_empty_text(self.cleaned_data.get("nombre"), "El nombre")

    def clean_normativa_numero(self):
        return _clean_numeric_text(
            self.cleaned_data.get("normativa_numero"),
            "El número de la normativa",
            max_length=20,
        )

    def clean(self):
        cleaned_data = super().clean()
        sector = cleaned_data.get("sector")
        subsector = cleaned_data.get("subsector")
        normativa_texto_actual = self.normativa_texto_actual
        normativa_tipo = cleaned_data.get("normativa_tipo")
        normativa_numero = cleaned_data.get("normativa_numero")
        normativa_anio = cleaned_data.get("normativa_anio")

        if sector and subsector and subsector.sector_id != sector.id:
            self.add_error(
                "subsector",
                "El subsector seleccionado no pertenece al sector indicado.",
            )

        if any([normativa_tipo, normativa_numero, normativa_anio]):
            if not normativa_tipo:
                self.add_error("normativa_tipo", "Seleccione el tipo de normativa.")
            if not normativa_numero:
                self.add_error("normativa_numero", "Ingrese el número de la normativa.")
            if not normativa_anio:
                self.add_error("normativa_anio", "Seleccione el año de la normativa.")

        if normativa_texto_actual and not self.instance.pk:
            normativa_texto_actual = ""

        if normativa_texto_actual or (
            normativa_tipo and normativa_numero and normativa_anio
        ):
            cleaned_data["normativa"] = _build_normativa_value(
                _validate_normativa_texto(normativa_texto_actual),
                normativa_tipo,
                normativa_numero,
                normativa_anio,
            )
        elif self.instance and self.instance.pk:
            cleaned_data["normativa"] = self.instance.normativa
        else:
            cleaned_data["normativa"] = ""

        return cleaned_data

    def save(self, commit=True):
        plan = super().save(commit=False)
        plan.nombre = self.cleaned_data["nombre"]
        plan.normativa = self.cleaned_data.get("normativa")

        if commit:
            plan.save()
            self.save_m2m()
        else:
            return plan

        nombre = self.cleaned_data["nombre"]
        titulo_referencia = plan.titulos.order_by("id").first()

        if titulo_referencia:
            titulo_referencia.nombre = nombre
            titulo_referencia.plan_estudio = plan
            titulo_referencia.activo = plan.activo
            titulo_referencia.save(update_fields=["nombre", "plan_estudio", "activo"])
        else:
            TituloReferencia.objects.create(
                nombre=nombre,
                plan_estudio=plan,
                activo=plan.activo,
            )

        return plan


class InscripcionOfertaForm(forms.ModelForm):
    oferta = forms.ModelChoiceField(
        queryset=Comision.objects.filter(estado__in=["planificada", "activa"]),
        label="Comisión",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    ciudadano = forms.ModelChoiceField(
        queryset=Ciudadano.objects.all(),
        label="Ciudadano",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    estado = forms.ChoiceField(
        label="Estado",
        choices=InscripcionOferta.ESTADO_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    class Meta:
        model = InscripcionOferta
        fields = ["oferta", "ciudadano", "estado"]


# ============================================================================
# PHASE 2 - INSTITUCIÓN FORMS
# ============================================================================


class InstitucionContactoForm(forms.ModelForm):
    centro = forms.ModelChoiceField(
        queryset=Centro.objects.all(),
        label="Centro",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    nombre_contacto = forms.CharField(
        label="Nombre y apellido del responsable",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    rol_area = forms.CharField(
        label="Rol / Área",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    documento = forms.CharField(
        label="Documento",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "inputmode": "numeric",
                "pattern": "[0-9]*",
                "maxlength": "20",
                "oninput": "this.value=this.value.replace(/\\D/g, '')",
            }
        ),
    )
    telefono_contacto = forms.CharField(
        label="Teléfono",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    email_contacto = forms.EmailField(
        label="Correo electrónico",
        required=False,
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )
    es_principal = forms.BooleanField(
        label="Es Principal",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    class Meta:
        model = InstitucionContacto
        fields = [
            "centro",
            "nombre_contacto",
            "rol_area",
            "documento",
            "telefono_contacto",
            "email_contacto",
            "es_principal",
        ]

    def clean_nombre_contacto(self):
        value = self.cleaned_data.get("nombre_contacto")
        if not value:
            return ""
        return _clean_non_empty_text(value, "El nombre y apellido del responsable")

    def clean_rol_area(self):
        value = self.cleaned_data.get("rol_area")
        if not value:
            return ""
        return _clean_non_empty_text(value, "El rol o área")

    def clean_documento(self):
        return _clean_numeric_text(
            self.cleaned_data.get("documento"),
            "El documento",
            max_length=20,
        )

    def clean_telefono_contacto(self):
        value = self.cleaned_data.get("telefono_contacto")
        if not value:
            return ""
        return _clean_phone_text(value, "El teléfono del responsable")

    def clean(self):
        cleaned_data = super().clean()
        _validate_contact_channels(cleaned_data)
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance = _assign_contact_type_and_value(instance, self.cleaned_data)
        if commit:
            instance.save()
        return instance


class InstitucionIdentificadorHistForm(forms.ModelForm):
    centro = forms.ModelChoiceField(
        queryset=Centro.objects.all(),
        label="Centro",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    tipo_identificador = forms.ChoiceField(
        label="Tipo de Identificador",
        choices=InstitucionIdentificadorHist.TIPO_IDENTIFICADOR_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    valor_identificador = forms.CharField(
        label="Valor del Identificador",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    ubicacion = forms.ModelChoiceField(
        queryset=InstitucionUbicacion.objects.none(),
        label="Ubicación Asociada",
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    es_actual = forms.BooleanField(
        label="Es Actual",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    vigencia_hasta = forms.DateField(
        label="Vigencia Hasta",
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    motivo = forms.CharField(
        label="Motivo del Cambio",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        centro = None
        if self.instance and self.instance.pk and self.instance.centro_id:
            centro = self.instance.centro
        elif "centro" in self.data:
            try:
                centro = Centro.objects.get(pk=self.data["centro"])
            except (Centro.DoesNotExist, ValueError):
                pass
        elif self.initial.get("centro"):
            try:
                centro_val = self.initial["centro"]
                if isinstance(centro_val, Centro):
                    centro = centro_val
                else:
                    centro = Centro.objects.get(pk=centro_val)
            except (Centro.DoesNotExist, ValueError):
                pass

        if centro:
            self.fields["ubicacion"].queryset = (
                InstitucionUbicacion.objects.filter(centro=centro)
                .select_related("localidad")
                .order_by("-es_principal", "rol_ubicacion")
            )

    class Meta:
        model = InstitucionIdentificadorHist
        fields = [
            "centro",
            "tipo_identificador",
            "valor_identificador",
            "rol_institucional",
            "ubicacion",
            "es_actual",
            "vigencia_hasta",
            "motivo",
        ]


class InstitucionUbicacionForm(forms.ModelForm):
    centro = forms.ModelChoiceField(
        queryset=Centro.objects.all(),
        label="Centro",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    localidad = forms.ModelChoiceField(
        queryset=Localidad.objects.order_by("nombre"),
        label="Localidad",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    rol_ubicacion = forms.ChoiceField(
        label="Rol de la ubicación",
        choices=InstitucionUbicacion.ROL_UBICACION_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    nombre_ubicacion = forms.CharField(
        label="Nombre de ubicación",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    domicilio = forms.CharField(
        label="Domicilio",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    es_principal = forms.BooleanField(
        label="Es principal",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    observaciones = forms.CharField(
        label="Observaciones",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
    )

    class Meta:
        model = InstitucionUbicacion
        fields = [
            "centro",
            "localidad",
            "rol_ubicacion",
            "nombre_ubicacion",
            "domicilio",
            "es_principal",
            "observaciones",
        ]


# ============================================================================
# CURSOS FORMS
# ============================================================================


class CursoForm(forms.ModelForm):
    plan_estudio = forms.ModelChoiceField(
        queryset=build_plan_estudio_queryset_for_centro(),
        label="Plan Curricular",
        required=True,
        widget=forms.Select(attrs={"class": "form-control"}),
        help_text="Se listan todos los planes curriculares activos de la provincia del centro.",
    )
    nombre = forms.CharField(
        label="Nombre",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    estado = forms.ChoiceField(
        label="Estado",
        choices=Curso.ESTADO_CURSO_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    usa_voucher = forms.BooleanField(
        label="Usa Voucher",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        help_text="Al inscribirse, se valida y descuenta crédito del voucher del ciudadano.",
    )
    inscripcion_libre = forms.BooleanField(
        label="Inscripción libre",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        help_text=(
            "Permite altas públicas aunque el ciudadano todavía no exista en SISOC."
        ),
    )
    voucher_parametrias = forms.ModelMultipleChoiceField(
        queryset=build_voucher_parametria_queryset(),
        label="Vouchers",
        required=False,
        widget=VoucherParametriaSelectMultiple(
            attrs={
                "class": "form-select",
                "size": "7",
                "style": "min-height: 170px;",
            }
        ),
        help_text="Seleccioná uno o más vouchers del mismo programa (Ctrl/Cmd + click para selección múltiple).",
    )
    costo_creditos = forms.IntegerField(
        label="Costo en créditos",
        required=False,
        min_value=0,
        initial=0,
        widget=forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
        help_text="Cantidad de créditos que se debitan por inscripción cuando usa voucher. Si no usa voucher, se guarda en 0.",
    )
    observaciones = forms.CharField(
        label="Observaciones",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
    )

    class Meta:
        model = Curso
        fields = [
            "plan_estudio",
            "nombre",
            "estado",
            "usa_voucher",
            "inscripcion_libre",
            "voucher_parametrias",
            "costo_creditos",
            "observaciones",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["plan_estudio"].empty_label = "Seleccionar plan de estudio..."
        centro_id = None
        centro_provincia_id = None
        current_plan_id = None
        current_voucher_ids = []

        if self.instance and self.instance.pk and self.instance.centro_id:
            centro_id = self.instance.centro_id
            centro_provincia_id = self.instance.centro.provincia_id
            current_plan_id = self.instance.plan_estudio_id
            current_voucher_ids = list(
                self.instance.voucher_parametrias.values_list("pk", flat=True)
            )
        elif self.initial.get("centro"):
            centro = self.initial.get("centro")
            if isinstance(centro, Centro):
                centro_id = centro.id
                centro_provincia_id = centro.provincia_id
            else:
                centro_id = centro

        if centro_provincia_id is None and centro_id:
            centro_provincia_id = (
                Centro.objects.filter(pk=centro_id)
                .values_list("provincia_id", flat=True)
                .first()
            )

        self.fields["plan_estudio"].queryset = build_plan_estudio_queryset_for_centro(
            centro_provincia_id,
            include_plan_ids=[current_plan_id],
        )
        self.fields["voucher_parametrias"].queryset = build_voucher_parametria_queryset(
            current_voucher_ids
        )

    def clean(self):
        cleaned_data = super().clean()
        plan_estudio = cleaned_data.get("plan_estudio")
        usa_voucher = cleaned_data.get("usa_voucher")
        inscripcion_libre = cleaned_data.get("inscripcion_libre")
        voucher_parametrias = cleaned_data.get("voucher_parametrias")
        costo_creditos = cleaned_data.get("costo_creditos")

        if not plan_estudio:
            self.add_error(
                "plan_estudio",
                "Debés seleccionar un plan de estudio para definir la modalidad del curso.",
            )
        else:
            cleaned_data["modalidad"] = plan_estudio.modalidad_cursada

        if usa_voucher and inscripcion_libre:
            self.add_error(
                "inscripcion_libre",
                "No podés activar inscripción libre y voucher al mismo tiempo.",
            )

        if usa_voucher and not voucher_parametrias:
            self.add_error(
                "voucher_parametrias",
                "Debés seleccionar al menos un voucher cuando el curso usa voucher.",
            )

        if usa_voucher and (costo_creditos is None or costo_creditos <= 0):
            self.add_error(
                "costo_creditos",
                "Debés informar un costo mayor a 0 cuando el curso usa voucher.",
            )

        if not usa_voucher:
            cleaned_data["costo_creditos"] = 0
            cleaned_data["voucher_parametrias"] = VoucherParametria.objects.none()

        if voucher_parametrias:
            programas_ids = {voucher.programa_id for voucher in voucher_parametrias}
            if len(programas_ids) > 1:
                self.add_error(
                    "voucher_parametrias",
                    "Todos los vouchers seleccionados deben pertenecer al mismo programa.",
                )

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.modalidad = self.cleaned_data.get("modalidad")

        if commit:
            instance.save()
            self.save_m2m()

        return instance


class ComisionCursoForm(forms.ModelForm):
    curso = forms.ModelChoiceField(
        queryset=Curso.objects.all(),
        label="Curso",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    ubicacion = forms.ModelChoiceField(
        queryset=InstitucionUbicacion.objects.none(),
        label="Ubicación",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    cupo_total = forms.IntegerField(
        label="Cupo Total",
        min_value=1,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    acepta_lista_espera = forms.BooleanField(
        label="Acepta Lista de Espera",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    fecha_inicio = forms.DateField(
        label="Fecha de Inicio",
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    fecha_fin = forms.DateField(
        label="Fecha de Fin",
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    estado = forms.ChoiceField(
        label="Estado",
        choices=ComisionCurso.ESTADO_COMISION_CURSO_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    observaciones = forms.CharField(
        label="Observaciones",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
    )

    class Meta:
        model = ComisionCurso
        fields = [
            "curso",
            "ubicacion",
            "cupo_total",
            "acepta_lista_espera",
            "fecha_inicio",
            "fecha_fin",
            "estado",
            "observaciones",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        curso_id = None
        current_ubicacion_id = self.instance.ubicacion_id if self.instance else None

        if self.is_bound:
            curso_id = self.data.get("curso")
        elif self.instance and self.instance.pk:
            curso_id = self.instance.curso_id
        else:
            curso_inicial = self.initial.get("curso")
            if isinstance(curso_inicial, Curso):
                curso_id = curso_inicial.id
            else:
                curso_id = curso_inicial

        if curso_id:
            centro_id = (
                Curso.all_objects.filter(pk=curso_id)
                .values_list("centro_id", flat=True)
                .first()
            )
            self.fields["ubicacion"].queryset = build_ubicacion_queryset_for_centros(
                [centro_id],
                include_ubicacion_ids=[current_ubicacion_id],
            )
        else:
            self.fields["ubicacion"].queryset = InstitucionUbicacion.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        curso = cleaned_data.get("curso")
        ubicacion = cleaned_data.get("ubicacion")
        cupo_total = cleaned_data.get("cupo_total")
        fecha_inicio = cleaned_data.get("fecha_inicio")
        fecha_fin = cleaned_data.get("fecha_fin")

        if curso and ubicacion and ubicacion.centro_id != curso.centro_id:
            self.add_error(
                "ubicacion",
                "La ubicación seleccionada no pertenece al centro del curso.",
            )

        if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
            self.add_error(
                "fecha_fin",
                "La fecha de fin debe ser mayor o igual a la fecha de inicio.",
            )

        if cupo_total is not None and cupo_total <= 0:
            self.add_error("cupo_total", "El cupo total debe ser mayor a 0.")

        return cleaned_data


# ============================================================================
# PHASE 4 - OFERTA INSTITUCIONAL FORMS
# ============================================================================


class OfertaInstitucionalForm(forms.ModelForm):
    centro = forms.ModelChoiceField(
        queryset=Centro.objects.all(),
        label="Centro",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    titulo_referencia = forms.ModelChoiceField(
        queryset=TituloReferencia.objects.filter(activo=True).select_related(
            "plan_estudio"
        ),
        label="Título de Referencia",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    plan_curricular = forms.ModelChoiceField(
        queryset=PlanVersionCurricular.objects.all(),
        required=False,
        widget=forms.HiddenInput(),
    )
    programa = forms.ModelChoiceField(
        queryset=Programa.objects.all(),
        label="Programa",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    nombre_local = forms.CharField(
        label="Nombre Local",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    ciclo_lectivo = forms.IntegerField(
        label="Ciclo Lectivo",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    estado = forms.ChoiceField(
        label="Estado de Oferta",
        choices=OfertaInstitucional.ESTADO_OFERTA_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    costo = forms.DecimalField(
        label="Costo ($)",
        min_value=0,
        initial=0,
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        help_text="Dejar en 0 si el curso es gratuito.",
    )
    usa_voucher = forms.BooleanField(
        label="Usa Voucher",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        help_text="Al inscribirse, se valida y descuenta un crédito del voucher del ciudadano.",
    )
    voucher_parametrias = forms.ModelMultipleChoiceField(
        queryset=VoucherParametria.objects.filter(activa=True).select_related(
            "programa"
        ),
        label="Vouchers",
        required=False,
        widget=VoucherParametriaSelectMultiple(
            attrs={
                "class": "form-select",
                "size": "7",
                "style": "min-height: 170px;",
            }
        ),
        help_text="Seleccioná uno o más vouchers del mismo programa (Ctrl/Cmd + click para selección múltiple).",
    )
    fecha_publicacion = forms.DateField(
        label="Fecha de Publicación",
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    observaciones = forms.CharField(
        label="Observaciones",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
    )

    class Meta:
        model = OfertaInstitucional
        fields = [
            "centro",
            "titulo_referencia",
            "plan_curricular",
            "programa",
            "nombre_local",
            "ciclo_lectivo",
            "estado",
            "costo",
            "usa_voucher",
            "voucher_parametrias",
            "fecha_publicacion",
            "observaciones",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["voucher_parametrias"].queryset = (
            VoucherParametria.objects.filter(activa=True)
            .select_related("programa")
            .order_by("nombre")
        )

        # Si la oferta ya existe, preseleccionamos el título asociado al plan.
        if self.instance and self.instance.pk and self.instance.plan_curricular_id:
            titulo = self.instance.plan_curricular.titulos.first()
            if titulo:
                self.fields["titulo_referencia"].initial = titulo.pk

    def clean(self):
        cleaned_data = super().clean()

        titulo = cleaned_data.get("titulo_referencia")
        if not titulo:
            return cleaned_data

        if not titulo.plan_estudio_id:
            self.add_error(
                "titulo_referencia",
                "El título seleccionado no tiene un Plan de Estudio asociado.",
            )
            return cleaned_data

        usa_voucher = cleaned_data.get("usa_voucher")
        programa = cleaned_data.get("programa")
        voucher_parametrias = cleaned_data.get("voucher_parametrias")

        if usa_voucher and not voucher_parametrias:
            self.add_error(
                "voucher_parametrias",
                "Debés seleccionar al menos un voucher cuando la oferta usa voucher.",
            )

        if programa and voucher_parametrias:
            invalidas = [
                v.nombre for v in voucher_parametrias if v.programa_id != programa.id
            ]
            if invalidas:
                self.add_error(
                    "voucher_parametrias",
                    "Todos los vouchers seleccionados deben pertenecer al programa elegido.",
                )

        cleaned_data["plan_curricular"] = titulo.plan_estudio
        return cleaned_data


class ComisionForm(forms.ModelForm):
    oferta = forms.ModelChoiceField(
        queryset=OfertaInstitucional.objects.all(),
        label="Oferta Institucional",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    ubicacion = forms.ModelChoiceField(
        queryset=InstitucionUbicacion.objects.all(),
        label="Ubicación",
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    codigo_comision = forms.CharField(
        label="Código de Comisión",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    nombre = forms.CharField(
        label="Nombre",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    fecha_inicio = forms.DateField(
        label="Fecha de Inicio",
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    fecha_fin = forms.DateField(
        label="Fecha de Fin",
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    cupo = forms.IntegerField(
        label="Cupo Total",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    acepta_lista_espera = forms.BooleanField(
        label="Acepta Lista de Espera",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    estado = forms.ChoiceField(
        label="Estado",
        choices=Comision.ESTADO_COMISION_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    observaciones = forms.CharField(
        label="Observaciones",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
    )

    class Meta:
        model = Comision
        fields = [
            "oferta",
            "ubicacion",
            "codigo_comision",
            "nombre",
            "fecha_inicio",
            "fecha_fin",
            "cupo",
            "acepta_lista_espera",
            "estado",
            "observaciones",
        ]


class ComisionHorarioForm(forms.ModelForm):
    comision = forms.ModelChoiceField(
        queryset=Comision.objects.all(),
        label="Comisión",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    dia_semana = forms.ModelChoiceField(
        queryset=Dia.objects.all(),
        label="Día de la Semana",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    hora_desde = forms.TimeField(
        label="Hora Desde",
        widget=forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
    )
    hora_hasta = forms.TimeField(
        label="Hora Hasta",
        widget=forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
    )
    aula_espacio = forms.CharField(
        label="Aula/Espacio",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    vigente = forms.BooleanField(
        label="Vigente",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    class Meta:
        model = ComisionHorario
        fields = [
            "comision",
            "dia_semana",
            "hora_desde",
            "hora_hasta",
            "aula_espacio",
            "vigente",
        ]


class ComisionCursoHorarioForm(forms.ModelForm):
    comision_curso = forms.ModelChoiceField(
        queryset=ComisionCurso.objects.all(),
        label="Comisión de Curso",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    dia_semana = forms.ModelChoiceField(
        queryset=Dia.objects.all(),
        label="Día de la Semana",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    hora_desde = forms.TimeField(
        label="Hora Desde",
        widget=forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
    )
    hora_hasta = forms.TimeField(
        label="Hora Hasta",
        widget=forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
    )
    aula_espacio = forms.CharField(
        label="Aula/Espacio",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    vigente = forms.BooleanField(
        label="Vigente",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    class Meta:
        model = ComisionHorario
        fields = [
            "comision_curso",
            "dia_semana",
            "hora_desde",
            "hora_hasta",
            "aula_espacio",
            "vigente",
        ]


# ============================================================================
# PHASE 5 - INSCRIPCIÓN FORMS
# ============================================================================


class InscripcionForm(forms.ModelForm):
    ciudadano = forms.ModelChoiceField(
        queryset=Ciudadano.objects.all(),
        label="Ciudadano",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    comision = forms.ModelChoiceField(
        queryset=Comision.objects.all(),
        label="Comisión",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    programa = forms.ModelChoiceField(
        queryset=Programa.objects.all(),
        label="Programa",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    estado = forms.ChoiceField(
        label="Estado",
        choices=Inscripcion.ESTADO_INSCRIPCION_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    origen_canal = forms.ChoiceField(
        label="Origen del Canal",
        choices=Inscripcion.ORIGEN_CANAL_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    observaciones = forms.CharField(
        label="Observaciones",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
    )

    class Meta:
        model = Inscripcion
        fields = [
            "ciudadano",
            "comision",
            "programa",
            "estado",
            "origen_canal",
            "observaciones",
        ]


class CiudadanoInscripcionRapidaForm(forms.ModelForm):
    apellido = forms.CharField(
        label="Apellido",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    nombre = forms.CharField(
        label="Nombre",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    fecha_nacimiento = forms.DateField(
        label="Fecha de Nacimiento",
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    tipo_documento = forms.CharField(
        initial=Ciudadano.DOCUMENTO_DNI,
        widget=forms.HiddenInput(),
    )
    documento = forms.IntegerField(
        label="Documento",
        widget=forms.NumberInput(
            attrs={"class": "form-control", "inputmode": "numeric"}
        ),
    )
    sexo = forms.ModelChoiceField(
        queryset=Sexo.objects.all(),
        label="Sexo",
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
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
        ]


# ============================================================================
# PHASE 7 - EVALUACIÓN FORMS
# ============================================================================


class EvaluacionForm(forms.ModelForm):
    comision = forms.ModelChoiceField(
        queryset=Comision.objects.all(),
        label="Comisión",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    tipo = forms.ChoiceField(
        label="Tipo de Evaluación",
        choices=Evaluacion.TIPO_EVALUACION_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    nombre = forms.CharField(
        label="Nombre de la Evaluación",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    descripcion = forms.CharField(
        label="Descripción",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
    )
    fecha = forms.DateField(
        label="Fecha de la Evaluación",
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    es_final = forms.BooleanField(
        label="Es Evaluación Final",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    ponderacion = forms.DecimalField(
        label="Ponderación (%)",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
    )
    observaciones = forms.CharField(
        label="Observaciones",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
    )

    class Meta:
        model = Evaluacion
        fields = [
            "comision",
            "tipo",
            "nombre",
            "descripcion",
            "fecha",
            "es_final",
            "ponderacion",
            "observaciones",
        ]


class ResultadoEvaluacionForm(forms.ModelForm):
    evaluacion = forms.ModelChoiceField(
        queryset=Evaluacion.objects.all(),
        label="Evaluación",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    inscripcion = forms.ModelChoiceField(
        queryset=Inscripcion.objects.all(),
        label="Inscripción",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    calificacion = forms.DecimalField(
        label="Calificación",
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
    )
    aprobo = forms.NullBooleanField(
        label="¿Aprobó?",
        required=False,
        widget=forms.Select(
            choices=[(None, "---"), (True, "Sí"), (False, "No")],
            attrs={"class": "form-control"},
        ),
    )
    observaciones = forms.CharField(
        label="Observaciones",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
    )

    class Meta:
        model = ResultadoEvaluacion
        fields = [
            "evaluacion",
            "inscripcion",
            "calificacion",
            "aprobo",
            "observaciones",
        ]


# ============================================================================
# VOUCHER FORMS
# ============================================================================


class VoucherParametriaForm(forms.ModelForm):
    nombre = forms.CharField(
        label="Nombre",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    descripcion = forms.CharField(
        label="Descripción",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
    )
    programa = forms.ModelChoiceField(
        queryset=Programa.objects.all(),
        label="Programa",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    cantidad_inicial = forms.IntegerField(
        label="Créditos por ciudadano",
        min_value=1,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    fecha_vencimiento = forms.DateField(
        label="Fecha de vencimiento",
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )

    renovacion_mensual = forms.BooleanField(
        label="Renovación mensual",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        help_text="Si está activo, los créditos se renuevan automáticamente cada mes.",
    )
    cantidad_renovacion = forms.IntegerField(
        label="Créditos en cada renovación",
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        help_text="Dejar vacío para usar la cantidad inicial.",
    )
    renovacion_tipo = forms.ChoiceField(
        label="Tipo de renovación",
        choices=[
            ("suma", "Sumar al saldo existente"),
            ("reinicia", "Reiniciar al valor configurado"),
        ],
        widget=forms.RadioSelect(),
        initial="suma",
    )

    inscripcion_unica_activa = forms.BooleanField(
        label="Inscripción única activa",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        help_text=(
            "Si está activado, el ciudadano solo puede tener una inscripción activa "
            "a la vez. Debe completar o abandonar el curso actual antes de inscribirse en otro."
        ),
    )

    def clean_fecha_vencimiento(self):
        fecha = self.cleaned_data.get("fecha_vencimiento")
        if fecha and fecha <= date.today():
            raise forms.ValidationError(
                "La fecha de vencimiento debe ser posterior a hoy."
            )
        return fecha

    class Meta:
        model = VoucherParametria
        fields = [
            "nombre",
            "descripcion",
            "programa",
            "cantidad_inicial",
            "fecha_vencimiento",
            "renovacion_mensual",
            "cantidad_renovacion",
            "renovacion_tipo",
            "inscripcion_unica_activa",
        ]


class VoucherForm(forms.ModelForm):
    ciudadano = forms.ModelChoiceField(
        queryset=Ciudadano.objects.all(),
        label="Ciudadano",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    programa = forms.ModelChoiceField(
        queryset=Programa.objects.all(),
        label="Programa",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    cantidad_inicial = forms.IntegerField(
        label="Cantidad de créditos",
        min_value=1,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    fecha_vencimiento = forms.DateField(
        label="Fecha de vencimiento",
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )

    def clean_fecha_vencimiento(self):
        fecha = self.cleaned_data.get("fecha_vencimiento")
        if fecha and fecha <= date.today():
            raise forms.ValidationError(
                "La fecha de vencimiento debe ser posterior a hoy."
            )
        return fecha

    class Meta:
        from VAT.models import Voucher

        model = Voucher
        fields = ["ciudadano", "programa", "cantidad_inicial", "fecha_vencimiento"]


class VoucherRecargaForm(forms.Form):
    cantidad = forms.IntegerField(
        label="Cantidad a recargar",
        min_value=1,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    motivo = forms.ChoiceField(
        label="Motivo",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from VAT.models import VoucherRecarga

        self.fields["motivo"].choices = VoucherRecarga.MOTIVO_CHOICES


class VoucherAsignacionMasivaForm(forms.Form):
    programa = forms.ModelChoiceField(
        queryset=Programa.objects.all(),
        label="Programa",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    cantidad_inicial = forms.IntegerField(
        label="Cantidad de créditos por ciudadano",
        min_value=1,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    fecha_vencimiento = forms.DateField(
        label="Fecha de vencimiento",
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    dnis = forms.CharField(
        label="DNIs",
        help_text="Ingresá los DNIs separados por comas, espacios o saltos de línea.",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": "Ej: 12345678, 23456789, 34567890",
            }
        ),
    )

    def clean_dnis(self):
        raw = self.cleaned_data["dnis"]
        dnis = [d.strip() for d in re.split(r"[\s,;]+", raw) if d.strip()]
        if not dnis:
            raise forms.ValidationError("Ingresá al menos un DNI.")
        if len(dnis) > 500:
            raise forms.ValidationError(
                "No se pueden asignar más de 500 vouchers a la vez."
            )
        return dnis
