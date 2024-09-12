from datetime import date

from django import forms
from django.core.files.base import ContentFile
from django.core.validators import MaxValueValidator, MinValueValidator

from legajos.models import (
    DimensionEconomia,
    DimensionEducacion,
    DimensionFamilia,
    DimensionSalud,
    DimensionTrabajo,
    DimensionVivienda,
    LegajoLocalidad,
    LegajoMunicipio,
    LegajoProvincias,
    Legajos,
    LegajosArchivos,
)
from usuarios.utils import recortar_imagen
from usuarios.validators import MaxSizeFileValidator


class LegajosForm(forms.ModelForm):
    foto = forms.ImageField(
        required=False,
        label="Foto Legajo",
        validators=[MaxSizeFileValidator(max_file_size=2)],
    )
    documento = forms.IntegerField(
        required=False,
        validators=[MinValueValidator(3000000), MaxValueValidator(100000000)],
        widget=forms.NumberInput(),
    )
    fk_provincia = forms.ModelChoiceField(
        required=True,
        label="Provincia",
        queryset=LegajoProvincias.objects.all(),
    )
    fk_municipio = forms.ModelChoiceField(
        required=True,
        label="Municipio",
        queryset=LegajoMunicipio.objects.none(),
    )
    fk_localidad = forms.ModelChoiceField(
        required=True,
        label="Localidad",
        queryset=LegajoLocalidad.objects.none(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Configurar el queryset del campo 'fk_provincia' para cargar solo las provincias
        self.fields["fk_provincia"].queryset = LegajoProvincias.objects.all()
        # Configurar los querysets de los campos 'fk_municipio' y 'fk_localidad' para que estén vacíos inicialmente
        self.fields["fk_municipio"].queryset = LegajoMunicipio.objects.none()
        self.fields["fk_localidad"].queryset = LegajoLocalidad.objects.none()

        # Actualizar los querysets si los datos están presentes en el formulario
        if "fk_municipio" in self.data:
            try:
                municipio_id = int(self.data.get("fk_municipio"))
                self.fields["fk_municipio"].queryset = LegajoMunicipio.objects.filter(
                    id=municipio_id
                ).order_by("nombre_region")
            except (ValueError, TypeError):
                self.fields["fk_municipio"].queryset = LegajoMunicipio.objects.none()

        if "fk_localidad" in self.data:
            try:
                localidad_id = int(self.data.get("fk_localidad"))
                self.fields["fk_localidad"].queryset = LegajoLocalidad.objects.filter(
                    id=localidad_id
                ).order_by("nombre")
            except (ValueError, TypeError):
                self.fields["fk_localidad"].queryset = LegajoLocalidad.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        tipo_doc = cleaned_data.get("tipo_doc")
        documento = cleaned_data.get("documento")
        apellido = cleaned_data.get("apellido")
        nombre = cleaned_data.get("nombre")
        fecha_nacimiento = cleaned_data.get("fecha_nacimiento")

        # Validación de campo unico, combinación de DNI + Tipo DNI
        existente = (
            tipo_doc
            and documento
            and fecha_nacimiento
            and apellido
            and nombre
            and Legajos.objects.filter(
                tipo_doc=tipo_doc,
                documento=documento,
                apellido=apellido,
                nombre=nombre,
                fecha_nacimiento=fecha_nacimiento,
            ).exists()
        )

        if existente:
            self.add_error(
                "documento", "Ya existe un legajo con ese TIPO y NÚMERO de documento."
            )

        if fecha_nacimiento and fecha_nacimiento > date.today():
            self.add_error(
                "fecha_nacimiento", "La fecha de termino debe ser menor al día de hoy."
            )

        return cleaned_data

    def crear_dimensiones(self, legajo):
        DimensionFamilia.objects.create(fk_legajo_id=legajo.id)
        DimensionVivienda.objects.create(fk_legajo_id=legajo.id)
        DimensionSalud.objects.create(fk_legajo_id=legajo.id)
        DimensionEconomia.objects.create(fk_legajo_id=legajo.id)
        DimensionEducacion.objects.create(fk_legajo_id=legajo.id)
        DimensionTrabajo.objects.create(fk_legajo_id=legajo.id)

    def save(self, commit: bool = True):
        legajo = super().save(commit=False)

        if legajo.foto:
            buffer = recortar_imagen(legajo.foto)
            legajo.foto.save(legajo.foto.name, ContentFile(buffer.getvalue()))

        if commit:
            legajo.save()
            self.crear_dimensiones(legajo)

        return legajo

    class Meta:
        model = Legajos
        exclude = (
            "creado",
            "modificado",
        )
        widgets = {
            "fecha_nacimiento": forms.DateInput(
                attrs={"type": "date", "required": True}, format="%Y-%m-%d"
            ),
            "m2m_alertas": forms.Select(attrs={"class": "select2"}),
            "m2m_familiares": forms.Select(attrs={"class": "select2"}),
            "fk_municipio": forms.Select(attrs={"class": "select2 municipio-select"}),
            "fk_localidad": forms.Select(attrs={"class": "select2 localidad-select"}),
            "fk_provincia": forms.Select(attrs={"class": "select2 provincia-select"}),
        }
        labels = {
            "fk_provincia": "Provincia",
            "fk_localidad": "Localidad",
            "fk_municipio": "Municipio",
            "nombre": "Nombre",
            "apellido": "Apellidos",
            "foto": "",
            "m2m_alertas": "",
            "Longitud": "Longitud",
            "Latitud": "Latitud",
        }


class LegajosUpdateForm(forms.ModelForm):
    foto = forms.ImageField(
        required=False,
        label="Foto Legajo",
        validators=[MaxSizeFileValidator(max_file_size=2)],
    )
    documento = forms.IntegerField(
        required=False,
        validators=[MinValueValidator(3000000), MaxValueValidator(100000000)],
        widget=forms.NumberInput(),
    )

    fk_provincia = forms.ModelChoiceField(
        required=True,
        label="Provincia",
        queryset=LegajoProvincias.objects.all(),
    )
    fk_municipio = forms.ModelChoiceField(
        required=True,
        label="Municipio",
        queryset=LegajoMunicipio.objects.all(),
    )
    fk_localidad = forms.ModelChoiceField(
        required=True,
        label="Localidad",
        queryset=LegajoLocalidad.objects.all(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fk_provincia"].queryset = LegajoProvincias.objects.all()
        if self.instance and self.instance.pk:
            municipio_actual = self.instance.fk_municipio
            localidad_actual = self.instance.fk_localidad
            self.fields["fk_municipio"].choices = [
                (municipio_actual.id, municipio_actual.nombre_region)
            ]
            self.fields["fk_localidad"].choices = [
                (localidad_actual.id, localidad_actual.nombre)
            ]

    def clean(self):
        cleaned_data = super().clean()
        tipo_doc = cleaned_data.get("tipo_doc")
        documento = cleaned_data.get("documento")
        fecha_nacimiento = cleaned_data.get("fecha_nacimiento")
        instance = self.instance  # Obtener la instancia del objeto actual

        # Validación de campo unico, combinación de DNI + Tipo DNI
        if tipo_doc and documento:
            # Verificar si el tipo o el documento han cambiado
            if (
                tipo_doc != instance.tipo_doc or documento != instance.documento
            ) and Legajos.objects.filter(
                tipo_doc=tipo_doc, documento=documento
            ).exists():
                self.add_error(
                    "tipo", "Ya existe otro objeto con el mismo tipo y documento"
                )

        # validación de fecha de nacimiento
        if fecha_nacimiento and fecha_nacimiento > date.today():
            self.add_error(
                "fecha_nacimiento", "La fecha de termino debe ser menor al día de hoy."
            )

        return cleaned_data

    def save(self, commit: bool = True):
        legajo = super().save(commit=False)

        if legajo.foto and legajo.foto != self.instance.foto:
            buffer = recortar_imagen(legajo.foto)
            legajo.foto.save(legajo.foto.name, ContentFile(buffer.getvalue()))

        if commit:
            legajo.save()

        return legajo

    class Meta:
        model = Legajos
        exclude = ("creado", "modificado", "m2m_familiares", "m2m_alertas")
        widgets = {
            "estado": forms.Select(choices=[(True, "Activo"), (False, "Inactivo")]),
            "fecha_nacimiento": forms.DateInput(
                attrs={"type": "date"}, format="%Y-%m-%d"
            ),
            "fk_municipio": forms.Select(attrs={"class": "select2 municipio-select"}),
            "fk_localidad": forms.Select(attrs={"class": "select2 localidad-select"}),
            "fk_provincia": forms.Select(attrs={"class": "select2 provincia-select"}),
        }
        labels = {
            "nombre": "Nombre",
            "apellido": "Apellidos",
            "foto": "",
            "fk_provincia": "Provincia",
            "fk_localidad": "Localidad",
            "fk_municipio": "Municipio",
        }


class LegajosArchivosForm(forms.ModelForm):
    class Meta:
        model = LegajosArchivos
        fields = ["fk_legajo", "archivo"]
