from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from ciudadanos.models import Sexo, TipoDocumento
from core.models import Dia
from centrodefamilia.models import (
    Centro,
    ActividadCentro,
    ParticipanteActividad,
    Categoria,
    Actividad,
    Expediente,
)

HORAS_DEL_DIA = [(f"{h:02d}:00", f"{h:02d}:00") for h in range(0, 24)] + [
    (f"{h:02d}:30", f"{h:02d}:30") for h in range(0, 24)
]


class CentroForm(forms.ModelForm):
    class Meta:
        model = Centro
        fields = [
            "tipo",
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
            "faro_asociado",
            "foto",
            "activo",
        ]

    def __init__(self, *args, **kwargs):
        from_faro = kwargs.pop("from_faro", False)
        super().__init__(*args, **kwargs)

        if from_faro:
            self.fields["tipo"].initial = "adherido"
            self.fields["tipo"].disabled = True
            self.fields["tipo"].widget = forms.HiddenInput()
            self.fields["faro_asociado"].disabled = True

        self.fields["referente"].queryset = User.objects.filter(
            groups__name="ReferenteCentro"
        ).only("id", "username", "first_name", "last_name")

        self.fields["faro_asociado"].queryset = Centro.objects.filter(
            tipo="faro", activo=True
        ).only("id", "nombre")
        self.fields["organizacion_asociada"].empty_label = "Seleccionar organización..."

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get("tipo")
        faro_asociado = cleaned_data.get("faro_asociado")

        if tipo == "adherido" and not faro_asociado:
            raise ValidationError(
                "Debe asociar un Centro FARO activo si el centro es ADHERIDO."
            )
        if tipo == "faro" and faro_asociado:
            raise ValidationError("Un Centro FARO no puede tener un FARO asociado.")
        return cleaned_data


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
            "precio",
            "estado",
        ]
        exclude = ["centro"]
        widgets = {
            "cantidad_personas": forms.NumberInput(attrs={"class": "form-control"}),
            "precio": forms.NumberInput(attrs={"class": "form-control"}),
            "estado": forms.Select(attrs={"class": "form-control"}),
        }

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

        if self.centro and self.centro.tipo == "faro":
            self.fields["precio"].widget = forms.HiddenInput()
            self.fields["precio"].required = False

    def clean(self):
        cleaned_data = super().clean()
        precio = cleaned_data.get("precio")
        if self.centro and self.centro.tipo == "faro" and precio:
            raise ValidationError(
                "Un centro de tipo FARO no debe tener un precio asignado."
            )
        return cleaned_data


class ParticipanteActividadForm(forms.ModelForm):
    nombre = forms.CharField(max_length=255, label="Nombre")
    apellido = forms.CharField(max_length=255, label="Apellido")
    fecha_nacimiento = forms.DateField(
        label="Fecha de Nacimiento", widget=forms.DateInput(attrs={"type": "date"})
    )
    tipo_documento = forms.ModelChoiceField(
        queryset=TipoDocumento.objects.all(), label="Tipo de Documento"
    )
    dni = forms.IntegerField(label="Documento")
    genero = forms.ModelChoiceField(queryset=Sexo.objects.all(), label="Sexo")

    class Meta:
        model = ParticipanteActividad
        # no usamos directamente los campos del modelo porque todos se construyen en la vista
        fields = []


class ExpedienteCabalForm(forms.ModelForm):
    periodo = forms.DateField(
        label="Periodo",
        widget=forms.DateInput(
            attrs={"type": "date", "class": "form-control form-control-sm"}
        ),
    )
    archivo = forms.FileField(
        label="Archivo",
        widget=forms.ClearableFileInput(
            attrs={"class": "form-control form-control-sm", "accept": ".pdf,.xlsx,.csv"}
        ),
    )

    class Meta:
        model = Expediente
        fields = ["periodo", "archivo"]


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
