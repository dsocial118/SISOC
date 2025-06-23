from django import forms
from django.core.exceptions import ValidationError
from .models import Centro, ActividadCentro, ParticipanteActividad, Categoria, Actividad ,Orientadores
from django.contrib.auth.models import User


class CentroForm(forms.ModelForm):
    class Meta:
        model = Centro
        fields = [
            "tipo",
            "nombre",
            "codigo",
            "organizacionasociada",
            "domicilio_sede",
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
        super().__init__(*args, **kwargs)
        self.fields["referente"].queryset = User.objects.filter(groups__name="ReferenteCentro")
        self.fields["faro_asociado"].queryset = Centro.objects.filter(tipo='faro', activo=True)

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get("tipo")
        faro_asociado = cleaned_data.get("faro_asociado")

        if tipo == "adherido" and not faro_asociado:
            raise ValidationError("Debe asociar un Centro FARO activo si el centro es ADHERIDO.")
        if tipo == "faro" and faro_asociado:
            raise ValidationError("Un Centro FARO no puede tener un FARO asociado.")
        return cleaned_data


class ActividadCentroForm(forms.ModelForm):
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.all(),
        required=False,
        label="Categoría",
        empty_label="Seleccione una categoría"
    )

    class Meta:
        model = ActividadCentro
        fields = ["categoria", "actividad", "cantidad_personas", "dias", "horarios", "precio", "estado"]
        exclude = ["centro"]

    def __init__(self, *args, **kwargs):
        self.centro = kwargs.pop("centro", None)
        super().__init__(*args, **kwargs)

        # Si se pasó un dato de categoría, filtramos las actividades
        if 'data' in kwargs:
            categoria_id = kwargs['data'].get("categoria")
            if categoria_id:
                self.fields["actividad"].queryset = Actividad.objects.filter(categoria_id=categoria_id)
            else:
                self.fields["actividad"].queryset = Actividad.objects.none()
        else:
            self.fields["actividad"].queryset = Actividad.objects.none()

        # Si es FARO, ocultar el campo precio
        if self.centro and self.centro.tipo == "faro":
            self.fields["precio"].widget = forms.HiddenInput()
            self.fields["precio"].required = False

    def clean(self):
        cleaned_data = super().clean()
        precio = cleaned_data.get("precio")

        if self.centro and self.centro.tipo == "faro" and precio:
            raise ValidationError("Un centro de tipo FARO no debe tener un precio asignado.")
        return cleaned_data


class ParticipanteActividadForm(forms.ModelForm):
    class Meta:
        model = ParticipanteActividad
        fields = [
            "nombre",
            "apellido",
            "dni",
            "edad",
            "genero",
            "cuit",
        ]

    def clean_cuit(self):
        cuit = self.cleaned_data["cuit"]
        if not cuit.isdigit() or len(cuit) not in [10, 11]:
            raise ValidationError("El CUIT debe tener entre 10 y 11 dígitos numéricos.")
        return cuit

    def clean(self):
        cleaned_data = super().clean()
        actividad = cleaned_data.get("actividad_centro")
        cuit = cleaned_data.get("cuit")

        if actividad and cuit:
            if ParticipanteActividad.objects.filter(
                actividad_centro=actividad, cuit=cuit
            ).exists():
                raise ValidationError(
                    "Este CUIT ya está registrado para esta actividad."
                )

        return cleaned_data


class OrientadoresForm(forms.ModelForm):
    class Meta:
        model = Orientadores
        fields = [
            "nombre",
            "apellido",
            "dni",
            "genero",
            "foto",
            "cargo",
        ]
        widgets = {
            "genero": forms.Select(attrs={"class": "form-control"}),
            "cargo": forms.Select(attrs={"class": "form-control"}),
        }

    def clean_dni(self):
        dni = self.cleaned_data.get("dni")
        if not dni.isdigit():
            raise forms.ValidationError("El DNI debe contener solo números.")
        return dni
