from datetime import date

from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator

from usuarios.validators import MaxSizeFileValidator

from .models import (
    DimensionEducacion,
    Legajos,
    LegajoProvincias,
    LegajoMunicipio,
    LegajoLocalidad,
    LegajoGrupoFamiliar,
    LegajoGrupoHogar,
    CategoriaAlertas,
    LegajoAlertas,
    LegajosArchivos,
    LegajosDerivaciones,
    DimensionFamilia,
    DimensionVivienda,
    DimensionSalud,
    DimensionEconomia,
    DimensionTrabajo,
    Intervencion,
    Llamado,
    CHOICE_VINCULO_FAMILIAR,
    CHOICE_ESTADO_RELACION,
    CHOICE_SINO,
)


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
                self.fields["fk_municipio"].queryset = LegajoMunicipio.objects.filter(id=municipio_id).order_by("nombre_region")
            except (ValueError, TypeError):
                self.fields["fk_municipio"].queryset = LegajoMunicipio.objects.none()

        if "fk_localidad" in self.data:
            try:
                localidad_id = int(self.data.get("fk_localidad"))
                self.fields["fk_localidad"].queryset = LegajoLocalidad.objects.filter(id=localidad_id).order_by("nombre")
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
            self.add_error("documento", "Ya existe un legajo con ese TIPO y NÚMERO de documento.")
        # validación de fecha de nacimiento
        if fecha_nacimiento and fecha_nacimiento > date.today():
            self.add_error("fecha_nacimiento", "La fecha de termino debe ser menor al día de hoy.")

        return cleaned_data

    class Meta:
        model = Legajos
        exclude = (
            "creado",
            "modificado",
        )
        widgets = {
            "fecha_nacimiento": forms.DateInput(attrs={"type": "date", "required": True}, format="%Y-%m-%d"),
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
            self.fields["fk_municipio"].choices = [(municipio_actual.id, municipio_actual.nombre_region)]
            self.fields["fk_localidad"].choices = [(localidad_actual.id, localidad_actual.nombre)]

    def clean(self):
        cleaned_data = super().clean()
        tipo_doc = cleaned_data.get("tipo_doc")
        documento = cleaned_data.get("documento")
        fecha_nacimiento = cleaned_data.get("fecha_nacimiento")
        instance = self.instance  # Obtener la instancia del objeto actual

        # Validación de campo unico, combinación de DNI + Tipo DNI
        if tipo_doc and documento:
            # Verificar si el tipo o el documento han cambiado
            if (tipo_doc != instance.tipo_doc or documento != instance.documento) and Legajos.objects.filter(
                tipo_doc=tipo_doc, documento=documento
            ).exists():
                self.add_error("tipo", "Ya existe otro objeto con el mismo tipo y documento")

        # validación de fecha de nacimiento
        if fecha_nacimiento and fecha_nacimiento > date.today():
            self.add_error("fecha_nacimiento", "La fecha de termino debe ser menor al día de hoy.")

        return cleaned_data

    class Meta:
        model = Legajos
        exclude = ("creado", "modificado", "m2m_familiares", "m2m_alertas")
        widgets = {
            "estado": forms.Select(choices=[(True, "Activo"), (False, "Inactivo")]),
            "fecha_nacimiento": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
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


class LegajoGrupoFamiliarForm(forms.ModelForm):
    class Meta:
        model = LegajoGrupoFamiliar
        fields = "__all__"


class NuevoLegajoFamiliarForm(forms.ModelForm):
    vinculo = forms.ChoiceField(choices=CHOICE_VINCULO_FAMILIAR, required=True)
    estado_relacion = forms.ChoiceField(choices=CHOICE_ESTADO_RELACION, required=True)
    conviven = forms.ChoiceField(choices=CHOICE_SINO, required=True)
    cuidador_principal = forms.ChoiceField(choices=CHOICE_SINO, required=True)
    documento = forms.IntegerField(
        required=False,
        validators=[MinValueValidator(3000000), MaxValueValidator(100000000)],
        widget=forms.NumberInput(),
    )

    class Meta:
        model = Legajos
        fields = [
            "apellido",
            "nombre",
            "fecha_nacimiento",
            "tipo_doc",
            "documento",
            "sexo",
            "vinculo",
            "estado_relacion",
            "conviven",
            "cuidador_principal",
        ]
        widgets = {
            "fecha_nacimiento": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }

    def clean(self):
        cleaned_data = super().clean()
        tipo_doc = cleaned_data.get("tipo_doc")
        documento = cleaned_data.get("documento")
        fecha_nacimiento = cleaned_data.get("fecha_nacimiento")

        # Validación de campo único, combinación de DNI + Tipo DNI
        if Legajos.objects.filter(tipo_doc=tipo_doc, documento=documento).exists():
            self.add_error("documento", "Ya existe un legajo con ese TIPO y NÚMERO de documento.")

        # Validación de fecha de nacimiento
        if fecha_nacimiento:
            if not isinstance(fecha_nacimiento, date):
                self.add_error(
                    "fecha_nacimiento",
                    "La fecha de nacimiento debe ser una fecha válida.",
                )
            elif fecha_nacimiento > date.today():
                self.add_error(
                    "fecha_nacimiento",
                    "La fecha de nacimiento debe ser menor o igual al día de hoy.",
                )

        return cleaned_data


#############HOGAR###########


class LegajoGrupoHogarForm(forms.ModelForm):
    vinculo = forms.ChoiceField(choices=CHOICE_VINCULO_FAMILIAR, required=True)
    documento = forms.IntegerField(
        required=False,
        validators=[MinValueValidator(3000000), MaxValueValidator(100000000)],
        widget=forms.NumberInput(),
    )

    class Meta:
        model = LegajoGrupoHogar
        fields = ["vinculo", "documento", "estado_relacion"]
        widgets = {
            "fecha_nacimiento": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }

    def clean(self):
        cleaned_data = super().clean()
        tipo_doc = cleaned_data.get("tipo_doc")
        documento = cleaned_data.get("documento")
        fecha_nacimiento = cleaned_data.get("fecha_nacimiento")
        print(fecha_nacimiento > date.today(), "--------------*********-----------------")

        # Validación de campo unico, combinación de DNI + Tipo DNI
        if Legajos.objects.filter(tipo_doc=tipo_doc, documento=documento).exists():
            self.add_error("documento", "Ya existe un legajo con ese TIPO y NÚMERO de documento.")
        # validación de fecha de nacimiento
        if fecha_nacimiento and fecha_nacimiento > date.today():
            self.add_error("fecha_nacimiento", "La fecha de termino debe ser menor al día de hoy.")

        return cleaned_data


class LegajosAlertasForm(forms.ModelForm):
    fk_categoria = forms.ModelChoiceField(
        required=True,
        label="Categoría",
        queryset=CategoriaAlertas.objects.all(),
        widget=forms.Select(attrs={"class": "select2"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fk_legajo"].widget = forms.HiddenInput()
        self.fields["creada_por"].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()
        fk_alerta = cleaned_data.get("fk_alerta")
        fk_legajo = cleaned_data.get("fk_legajo")
        if fk_alerta and fk_legajo and LegajoAlertas.objects.filter(fk_alerta=fk_alerta, fk_legajo=fk_legajo).exists():
            self.add_error("fk_alerta", "Ya existe esa alerta en el legajo")
        return cleaned_data

    class Meta:
        model = LegajoAlertas
        fields = "__all__"
        widgets = {
            "fk_alerta": forms.Select(attrs={"class": "select2"}),
        }
        labels = {"fk_alerta": "Alerta"}


class LegajosArchivosForm(forms.ModelForm):
    class Meta:
        model = LegajosArchivos
        fields = ["fk_legajo", "archivo"]


class LegajosDerivacionesForm(forms.ModelForm):
    archivos = forms.FileField(
        widget=forms.ClearableFileInput(
            attrs={
                "multiple": True,
            }
        ),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = LegajosDerivaciones
        fields = "__all__"
        exclude = ["motivo_rechazo", "obs_rechazo", "fecha_rechazo"]
        widgets = {
            "detalles": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                }
            ),
        }
        labels = {
            "fk_legajo": "Legajo",
            "fk_organismo": "Organismo relacionado",
            "m2m_alertas": "Alertas detectadas",
            "fk_programa": "Derivar a",
            "fk_programa_solicitante": "Derivar de",
        }


# Dimensiones
class DimensionFamiliaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fk_legajo"].widget = forms.HiddenInput()

    class Meta:
        model = DimensionFamilia
        fields = "__all__"
        widgets = {
            "obs_familia": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            "otro_responsable": forms.CheckboxInput(),
            #  'otro_responsable': forms.CheckboxInput(attrs={'class':'icheck-primary '}),
            "hay_embarazadas": forms.CheckboxInput(),
            "hay_prbl_smental": forms.CheckboxInput(),
            "hay_fam_discapacidad": forms.CheckboxInput(),
            "hay_enf_cronica": forms.CheckboxInput(),
            "hay_priv_libertad": forms.CheckboxInput(),
        }


class DimensionViviendaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fk_legajo"].widget = forms.HiddenInput()

    class Meta:
        model = DimensionVivienda
        fields = "__all__"
        widgets = {
            "obs_vivienda": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            #'hay_agua_caliente': forms.CheckboxInput(),
            #'hay_desmoronamiento': forms.CheckboxInput(),
            #'hay_banio': forms.CheckboxInput(),
            #'PoseenCeludar': forms.CheckboxInput(),
            #'PoseenPC': forms.CheckboxInput(),
            #'Poseeninternet': forms.CheckboxInput()
        }

    # <!-- ./Nuevos campos vivienda Form Editar o cargar -->


class DimensionSaludForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fk_legajo"].widget = forms.HiddenInput()

    class Meta:
        model = DimensionSalud
        fields = "__all__"
        widgets = {
            "obs_salud": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            "hay_obra_social": forms.CheckboxInput(),
            "hay_enfermedad": forms.CheckboxInput(),
            "hay_discapacidad": forms.CheckboxInput(),
            "hay_cud": forms.CheckboxInput(),
        }


class DimensionEducacionForm(forms.ModelForm):
    provinciaInstitucion = forms.ModelChoiceField(
        label="Provincia",
        queryset=LegajoProvincias.objects.all(),
    )
    municipioInstitucion = forms.ModelChoiceField(
        label="Municipio",
        queryset=LegajoMunicipio.objects.none(),
    )
    localidadInstitucion = forms.ModelChoiceField(
        label="Localidad",
        queryset=LegajoLocalidad.objects.none(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fk_legajo"].widget = forms.HiddenInput()

        # Configurar el queryset del campo 'provinciaInstitucion' para cargar solo las provincias
        self.fields["provinciaInstitucion"].queryset = LegajoProvincias.objects.all()
        # Configurar los querysets de los campos 'municipioInstitucion' y 'localidadInstitucion' para que estén vacíos inicialmente
        self.fields["municipioInstitucion"].queryset = LegajoMunicipio.objects.none()
        self.fields["localidadInstitucion"].queryset = LegajoLocalidad.objects.none()

        # Actualizar los querysets si los datos están presentes en el formulario
        if "municipioInstitucion" in self.data:
            try:
                municipio_id = int(self.data.get("municipioInstitucion"))
                self.fields["municipioInstitucion"].queryset = LegajoMunicipio.objects.filter(id=municipio_id).order_by("nombre_region")
            except (ValueError, TypeError):
                self.fields["municipioInstitucion"].queryset = LegajoMunicipio.objects.none()

        if "localidadInstitucion" in self.data:
            try:
                localidad_id = int(self.data.get("localidadInstitucion"))
                self.fields["localidadInstitucion"].queryset = LegajoLocalidad.objects.filter(id=localidad_id).order_by("nombre")
            except (ValueError, TypeError):
                self.fields["localidadInstitucion"].queryset = LegajoLocalidad.objects.none()

    class Meta:
        model = DimensionEducacion
        fields = "__all__"
        widgets = {
            "obs_educacion": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            "areaCurso": forms.SelectMultiple(
                attrs={
                    "class": "form-control",
                    "style": "width: 100%;",
                }
            ),
            "areaOficio": forms.SelectMultiple(
                attrs={
                    "class": "form-control",
                    "style": "width: 100%;",
                }
            ),
        }

    def clean_area_curso(self):
        data = self.cleaned_data["areaCurso"]
        if len(data) > 3:
            raise forms.ValidationError("Solo puedes seleccionar hasta 3 opciones.")
        return data


class DimensionEconomiaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fk_legajo"].widget = forms.HiddenInput()

    class Meta:
        model = DimensionEconomia
        fields = "__all__"
        widgets = {
            "obs_economia": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            #'recibe_plan': forms.CheckboxInput(),
            "m2m_planes": forms.SelectMultiple(
                attrs={
                    "class": "select2 w-100",
                    "style": "width: 100%;",
                    "multiple": True,
                }
            ),
        }
        labels = {"m2m_planes": "Planes sociales que recibe"}


class DimensionTrabajoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fk_legajo"].widget = forms.HiddenInput()

    class Meta:
        model = DimensionTrabajo
        fields = "__all__"
        widgets = {
            "obs_trabajo": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            #'tiene_trabajo': forms.CheckboxInput(),
            #'conviviente_trabaja': forms.CheckboxInput(),
        }


class DerivacionesRechazoForm(forms.ModelForm):
    class Meta:
        model = LegajosDerivaciones
        fields = ["motivo_rechazo", "obs_rechazo", "fecha_rechazo"]
        widgets = {
            "obs_rechazo": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
        }
        labels = {
            "motivo_rechazo": "Motivo de rechazo",
            "obs_rechazo": "Observaciones",
        }


class IntervencionForm(forms.ModelForm):
    class Meta:
        model = Intervencion
        fields = "__all__"
        widgets = {
            "detalles": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
        }
        labels = {
            "detalles": "Detalles de la intervención",
            "fk_subintervencion": "Subintervención",
            "fk_tipo_intervencion": "Tipo de intervención",
            "fk_estado": "Estado",
            "fk_direccion": "Dirección",
        }


class LlamadoForm(forms.ModelForm):
    class Meta:
        model = Llamado
        fields = "__all__"
        widgets = {
            "observaciones": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
        }
        labels = {
            "fk_subtipollamado": "Subintervención",
            "fk_tipo_llamado": "Tipo de intervención",
            "fk_estado": "Estado",
        }
