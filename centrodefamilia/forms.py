from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from ciudadanos.models import Ciudadano
from core.models import Dia, Sexo
from centrodefamilia.models import (
    Centro,
    ActividadCentro,
    ParticipanteActividad,
    Categoria,
    Actividad,
    Beneficiario,
    Responsable,
)
from centrodefamilia.services.participante import (
    ParticipanteService,
    AlreadyRegistered,
    CupoExcedido,
    SexoNoPermitido,
)
from centrodefamilia.services.form_service import (
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
    """
    Form para inscripción de participantes: crea o reutiliza ciudadano,
    y registra inscripción (o lista de espera) usando ParticipanteService.
    """

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
        fields = []  # se procesan todos los datos en save()

    def __init__(self, *args, **kwargs):
        self.actividad_id = kwargs.pop("actividad_id")
        self.usuario = kwargs.pop("usuario")
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        # Validar existencia previa
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


class ResponsableForm(forms.ModelForm):
    class Meta:
        model = Responsable
        exclude = ["fecha_creado", "fecha_modificado"]
        widgets = {
            "genero": forms.Select(
                choices=Responsable.GENERO_CHOICES, attrs={"disabled": True}
            ),
            "fecha_nacimiento": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        setup_location_fields(self)
        set_readonly_fields(
            self, ["nombre", "apellido", "dni", "genero", "fecha_nacimiento"]
        )


class BeneficiarioForm(forms.ModelForm):
    actividad_preferida = forms.MultipleChoiceField(
        choices=Beneficiario.ACTIVIDAD_PREFERIDA_CHOICES,
        widget=forms.SelectMultiple(
            attrs={
                "class": "select2",
                "data-placeholder": "Seleccione actividades preferidas",
            }
        ),
        required=True,
    )
    actividades_detalle = forms.ModelMultipleChoiceField(
        queryset=Actividad.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
        label="",
        required=False,
    )

    class Meta:
        model = Beneficiario
        exclude = ["fecha_creado", "fecha_modificado", "responsable"]
        widgets = {
            "genero": forms.Select(
                choices=Beneficiario.GENERO_CHOICES, attrs={"disabled": True}
            ),
            "nivel_educativo_actual": forms.Select(
                choices=Beneficiario.NIVEL_EDUCATIVO_ACTUAL_CHOICES
            ),
            "maximo_nivel_educativo": forms.Select(
                choices=Beneficiario.MAXIMO_NIVEL_EDUCATIVO_CHOICES
            ),
            "fecha_nacimiento": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        setup_location_fields(self)
        self.fields["actividades_detalle"].required = False
        set_readonly_fields(
            self, ["nombre", "apellido", "fecha_nacimiento", "dni", "genero"]
        )
