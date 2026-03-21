from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from ciudadanos.models import Ciudadano
from core.models import Dia, Sexo
from VAT.models import (
    Centro,
    ActividadCentro,
    ParticipanteActividad,
    Categoria,
    Actividad,
    ModalidadInstitucional,
)
from VAT.services.participante import (
    ParticipanteService,
    AlreadyRegistered,
    CupoExcedido,
    SexoNoPermitido,
)
from VAT.services.form_service import (
    setup_location_fields,
    set_readonly_fields,
)

HORAS_DEL_DIA = [(f"{h:02d}:00", f"{h:02d}:00") for h in range(0, 24)] + [
    (f"{h:02d}:30", f"{h:02d}:30") for h in range(0, 24)
]


class CentroForm(forms.ModelForm):
    class Meta:
        model = Centro
        fields = [
            "nombre",
            "codigo",
            "organizacion_asociada",
            "provincia",
            "municipio",
            "localidad",
            "calle",
            "numero",
            "domicilio_actividad",
            "telefono",
            "celular",
            "correo",
            "sitio_web",
            "link_redes",
            "nombre_referente",
            "apellido_referente",
            "telefono_referente",
            "correo_referente",
            "referente",
            "foto",
            "activo",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["referente"].queryset = User.objects.filter(
            groups__name="ReferenteCentroVAT"
        ).only("id", "username", "first_name", "last_name")

        self.fields["organizacion_asociada"].empty_label = "Seleccionar organización..."


class ActividadCentroForm(forms.ModelForm):
    sexoact = forms.ModelMultipleChoiceField(
        queryset=Sexo.objects.all(),
        required=False,
        label="Actividad dirigida a...",
        widget=forms.SelectMultiple(attrs={"class": "select2 w-100", "multiple": True}),
    )
    dias = forms.ModelMultipleChoiceField(
        queryset=Dia.objects.all(),
        required=False,
        label="Días",
        widget=forms.SelectMultiple(attrs={"class": "select2 w-100", "multiple": True}),
    )
    horariosdesde = forms.TimeField(
        label="Hora Desde",
        widget=forms.TimeInput(
            attrs={
                "class": "form-control timepicker",
                "placeholder": "Seleccione una hora",
            }
        ),
        required=True,
    )
    horarioshasta = forms.TimeField(
        label="Hora Hasta",
        widget=forms.TimeInput(
            attrs={
                "class": "form-control timepicker",
                "placeholder": "Seleccione una hora",
            }
        ),
        required=True,
    )
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.all(),
        required=False,
        label="Categoría",
        empty_label="Seleccione una categoría",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    fecha_inicio = forms.DateField(
        label="Fecha de inicio",
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    fecha_fin = forms.DateField(
        label="Fecha de fin",
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )

    class Meta:
        model = ActividadCentro
        fields = [
            "categoria",
            "actividad",
            "cantidad_personas",
            "sexoact",
            "dias",
            "horariosdesde",
            "horarioshasta",
            "fecha_inicio",
            "fecha_fin",
            "precio",
            "estado",
        ]
        exclude = ["centro"]
        widgets = {
            "cantidad_personas": forms.NumberInput(attrs={"class": "form-control"}),
            "precio": forms.NumberInput(attrs={"class": "form-control"}),
            "estado": forms.Select(attrs={"class": "form-control"}),
        }

    def clean(self):
        cleaned = super().clean()
        fecha_inicio = cleaned.get("fecha_inicio")
        fecha_fin = cleaned.get("fecha_fin")
        if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
            raise forms.ValidationError(
                "La fecha de fin no puede ser anterior a la fecha de inicio."
            )
        return cleaned

    def __init__(self, *args, **kwargs):
        self.centro = kwargs.pop("centro", None)
        super().__init__(*args, **kwargs)

        if self.data:
            cat_id = self.data.get("categoria")
            self.fields["actividad"].queryset = (
                Actividad.objects.filter(categoria_id=cat_id)
                if cat_id
                else Actividad.objects.none()
            )
        elif self.instance and self.instance.pk:
            actividad = self.instance.actividad
            cat_id = actividad.categoria_id if actividad else None
            self.initial.update(
                {
                    "categoria": cat_id,
                    "actividad": self.instance.actividad_id,
                    "dias": [d.pk for d in self.instance.dias.all()],
                }
            )
            self.fields["actividad"].queryset = (
                Actividad.objects.filter(categoria_id=cat_id)
                if cat_id
                else Actividad.objects.none()
            )
        else:
            self.fields["actividad"].queryset = Actividad.objects.none()


class ParticipanteActividadForm(forms.ModelForm):
    nombre = forms.CharField(max_length=255, label="Nombre")
    apellido = forms.CharField(max_length=255, label="Apellido")
    fecha_nacimiento = forms.DateField(
        label="Fecha de Nacimiento", widget=forms.DateInput(attrs={"type": "date"})
    )
    tipo_documento = forms.ChoiceField(
        choices=Ciudadano.DOCUMENTO_CHOICES, label="Tipo de Documento"
    )
    dni = forms.IntegerField(label="Documento")
    genero = forms.ModelChoiceField(queryset=Sexo.objects.all(), label="Sexo")

    class Meta:
        model = ParticipanteActividad
        fields = []

    def __init__(self, *args, **kwargs):
        self.actividad_id = kwargs.pop("actividad_id")
        self.usuario = kwargs.pop("usuario")
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        documento = cleaned.get("dni")
        if ParticipanteActividad.objects.filter(
            actividad_centro_id=self.actividad_id,
            ciudadano__documento=documento,
            estado__in=["inscrito", "lista_espera"],
        ).exists():
            raise ValidationError("El ciudadano ya está inscrito o en lista de espera.")
        return cleaned

    def save(self, commit=True):
        datos = {
            "nombre": self.cleaned_data["nombre"],
            "apellido": self.cleaned_data["apellido"],
            "dni": self.cleaned_data["dni"],
            "fecha_nacimiento": self.cleaned_data["fecha_nacimiento"],
            "tipo_documento": self.cleaned_data["tipo_documento"],
            "genero": self.cleaned_data["genero"],
        }
        try:
            _, participante = ParticipanteService.procesar_creacion(
                usuario=self.usuario,
                actividad_id=self.actividad_id,
                datos=datos,
                ciudadano_id=None,
            )
        except IntegrityError as e:
            raise ValidationError(
                "El ciudadano ya está inscrito o en lista de espera."
            ) from e
        except (AlreadyRegistered, SexoNoPermitido) as e:
            raise ValidationError(str(e)) from e
        except CupoExcedido as e:
            raise ValidationError(
                str(e) + " Se agregará a lista de espera si lo desea."
            ) from e
        return participante


class ActividadForm(forms.ModelForm):
    nombre = forms.CharField(
        label="Nombre de la Actividad",
        widget=forms.TextInput(
            attrs={
                "class": "form-control form-control-sm",
                "placeholder": "Ej. Taller de oficio",
            }
        ),
    )
    categoria = forms.ModelChoiceField(
        label="Categoría",
        queryset=Categoria.objects.all(),
        widget=forms.Select(attrs={"class": "form-control form-control-sm"}),
    )

    class Meta:
        model = Actividad
        fields = ["categoria", "nombre"]


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
