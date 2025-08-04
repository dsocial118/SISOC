from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory

from ciudadanos.models import Sexo, TipoDocumento
from core.models import Dia
from centrodefamilia.models import (
    Centro,
    ActividadCentro,
    HorarioActividadCentro,
    ParticipanteActividad,
    Categoria,
    Actividad,
    Expediente,
)
from centrodefamilia.services.participante import (
    ParticipanteService,
    AlreadyRegistered,
    CupoExcedido,
    SexoNoPermitido,
)

HORAS_DEL_DIA = [(f"{h:02d}:00", f"{h:02d}:00") for h in range(0, 24)] + [
    (f"{h:02d}:30", f"{h:02d}:30") for h in range(0, 24)
]

# Form para cada franja de horario de una actividad en un centro
class HorarioActividadCentroForm(forms.ModelForm):
    class Meta:
        model = HorarioActividadCentro
        fields = ['dia', 'hora_inicio', 'hora_fin']
        widgets = {
            'dia': forms.Select(attrs={'class': 'form-control'}),
            'hora_inicio': forms.TimeInput(attrs={'class': 'form-control timepicker', 'placeholder': 'HH:MM'}),
            'hora_fin': forms.TimeInput(attrs={'class': 'form-control timepicker', 'placeholder': 'HH:MM'}),
        }
        labels = {
            'dia': 'Día',
            'hora_inicio': 'Hora Inicio',
            'hora_fin': 'Hora Fin',
        }

# InlineFormSet para gestionar múltiples franjas en el mismo formulario
HorarioActividadCentroFormSet = inlineformset_factory(
    ActividadCentro,
    HorarioActividadCentro,
    form=HorarioActividadCentroForm,
    extra=1,
    can_delete=True
)

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
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.all(),
        required=False,
        label="Categoría",
        empty_label="Seleccione una categoría",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    precio = forms.IntegerField(
        required=False,
        label="Precio",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    estado = forms.ChoiceField(
        choices=ActividadCentro.ESTADO_CHOICES,
        label="Estado",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    sexoact = forms.ModelMultipleChoiceField(
        queryset=Sexo.objects.all(),
        required=False,
        label="Actividad dirigida a...",
        widget=forms.SelectMultiple(attrs={"class": "select2 w-100", "multiple": True})
    )

    class Meta:
        model = ActividadCentro
        fields = [
            "categoria",
            "actividad",
            "sexoact",
            "precio",
            "estado",
        ]
        exclude = ["centro"]

    def __init__(self, *args, **kwargs):
        self.centro = kwargs.pop("centro", None)
        super().__init__(*args, **kwargs)

        # Ajuste de queryset de 'actividad' según categoría seleccionada
        if self.data.get("categoria"):
            cat_id = self.data.get("categoria")
            self.fields["actividad"].queryset = Actividad.objects.filter(categoria_id=cat_id)
        elif self.instance and self.instance.pk:
            cat_id = self.instance.actividad.categoria_id
            self.initial["categoria"] = cat_id
            self.fields["actividad"].queryset = Actividad.objects.filter(categoria_id=cat_id)
        else:
            self.fields["actividad"].queryset = Actividad.objects.none()

        # Ocultar precio si el centro es FARO
        if self.centro and self.centro.tipo == "faro":
            self.fields["precio"].widget = forms.HiddenInput()
            self.fields["precio"].required = False

    def clean(self):
        cleaned_data = super().clean()
        precio = cleaned_data.get("precio")
        if self.centro and self.centro.tipo == "faro" and precio:
            raise ValidationError("Un centro de tipo FARO no debe tener un precio asignado.")
        return cleaned_data

    
class HorarioModalForm(forms.ModelForm):
    dia = forms.ModelChoiceField(
        queryset=Dia.objects.all(),
        label="Día",
        widget=forms.Select(attrs={"class": "form-control"})
    )
    hora_inicio = forms.TimeField(
        label="Hora Desde",
        widget=forms.TimeInput(attrs={"class": "form-control timepicker", "placeholder": "HH:MM"})
    )
    hora_fin = forms.TimeField(
        label="Hora Hasta",
        widget=forms.TimeInput(attrs={"class": "form-control timepicker", "placeholder": "HH:MM"})
    )
    cantidad_personas = forms.IntegerField(
        label="Cupo",
        widget=forms.NumberInput(attrs={"class": "form-control", "min": 1})
    )
    class Meta:
        model = HorarioActividadCentro
        # No toca fields del modelo base salvo dia y horas; 'cantidad_personas' y 'sexoact' serán tratados en la vista
        fields = ['dia', 'hora_inicio', 'hora_fin']


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
    tipo_documento = forms.ModelChoiceField(
        queryset=TipoDocumento.objects.all(), label="Tipo de Documento"
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
        except (AlreadyRegistered, SexoNoPermitido) as e:
            raise ValidationError(str(e)) from e
        except CupoExcedido as e:
            raise ValidationError(
                str(e) + " Se agregará a lista de espera si lo desea."
            ) from e
        return participante


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
