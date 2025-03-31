from datetime import date

from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator

from ciudadanos.models import (
    CategoriaAlertas,
    Ciudadano,
    DimensionEconomia,
    DimensionEducacion,
    DimensionFamilia,
    DimensionSalud,
    DimensionTrabajo,
    DimensionVivienda,
    Intervencion,
    Alerta,
    GrupoFamiliar,
    Llamado,
    CiudadanoPrograma,
    EstadoRelacion,
    VinculoFamiliar,
)
from config.validators import MaxSizeFileValidator
from configuraciones.models import (
    Asentamiento,
    Departamento,
    Localidad,
    Municipio,
    Provincia,
)

BOOLEAN_CHOICE = [
    (False, "No"),
    (True, "Si"),
]


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class CiudadanoForm(forms.ModelForm):
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
    provincia = forms.ModelChoiceField(
        required=False,
        label="Provincia",
        queryset=Provincia.objects.all(),
    )
    municipio = forms.ModelChoiceField(
        required=False,
        label="Municipio",
        queryset=Municipio.objects.none(),
    )
    localidad = forms.ModelChoiceField(
        required=False,
        label="Localidad",
        queryset=Localidad.objects.none(),
    )
    departamento = forms.ModelChoiceField(
        required=False,
        label="Departamento",
        queryset=Departamento.objects.none(),
    )
    asentamiento = forms.ModelChoiceField(
        required=False,
        label="Asentamiento",
        queryset=Asentamiento.objects.none(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Configurar el queryset del campo 'provincia' para cargar solo las provincias
        self.fields["provincia"].queryset = Provincia.objects.all()
        # Configurar los querysets de los campos 'municipio' y 'localidad' para que estén vacíos inicialmente
        self.fields["municipio"].queryset = Municipio.objects.none()
        self.fields["localidad"].queryset = Localidad.objects.none()
        self.fields["departamento"].queryset = Departamento.objects.none()
        self.fields["asentamiento"].queryset = Asentamiento.objects.none()
        # Actualizar los querysets si los datos están presentes en el formulario
        if "municipio" in self.data:
            try:
                municipio_id = int(self.data.get("municipio"))
                self.fields["municipio"].queryset = Municipio.objects.filter(
                    id=municipio_id
                ).order_by("nombre")
            except (ValueError, TypeError):
                self.fields["municipio"].queryset = Municipio.objects.none()

        if "localidad" in self.data:
            try:
                localidad_id = int(self.data.get("localidad"))
                self.fields["localidad"].queryset = Localidad.objects.filter(
                    id=localidad_id
                ).order_by("nombre")
            except (ValueError, TypeError):
                self.fields["localidad"].queryset = Localidad.objects.none()

        if "departamento" in self.data:
            try:
                departamento_id = int(self.data.get("departamento"))
                self.fields["departamento"].queryset = Departamento.objects.filter(
                    id=departamento_id
                ).order_by("nombre")
            except (ValueError, TypeError):
                self.fields["departamento"].queryset = Departamento.objects.none()

        if "asentamiento" in self.data:
            try:
                asentameinto_id = int(self.data.get("asentamiento"))
                self.fields["asentamiento"].queryset = Asentamiento.objects.filter(
                    id=asentameinto_id
                ).order_by("nombre")
            except (ValueError, TypeError):
                self.fields["asentamiento"].queryset = Asentamiento.objects.none()

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
            and Ciudadano.objects.filter(
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
        # validación de fecha de nacimiento
        if fecha_nacimiento and fecha_nacimiento > date.today():
            self.add_error(
                "fecha_nacimiento", "La fecha de termino debe ser menor al día de hoy."
            )

        return cleaned_data

    class Meta:
        model = Ciudadano
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
            "municipio": forms.Select(attrs={"class": "select2 municipio-select"}),
            "localidad": forms.Select(attrs={"class": "select2 localidad-select"}),
            "provincia": forms.Select(attrs={"class": "select2 provincia-select"}),
            "departamento": forms.Select(
                attrs={"class": "select2 departamento-select"}
            ),
            "asentamiento": forms.Select(
                attrs={"class": "select2 asentamiento-select"}
            ),
        }
        labels = {
            "provincia": "Provincia",
            "localidad": "Localidad",
            "municipio": "Municipio",
            "nombre": "Nombre",
            "apellido": "Apellidos",
            "foto": "",
            "m2m_alertas": "",
            "Longitud": "Longitud",
            "Latitud": "Latitud",
            "departamento": "Departamento",
            "asentamiento": "Asentamiento",
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

    provincia = forms.ModelChoiceField(
        required=True,
        label="Provincia",
        queryset=Provincia.objects.all(),
    )
    municipio = forms.ModelChoiceField(
        required=False,
        label="Municipio",
        queryset=Municipio.objects.all(),
    )
    localidad = forms.ModelChoiceField(
        required=False,
        label="Localidad",
        queryset=Localidad.objects.all(),
    )
    departamento = forms.ModelChoiceField(
        required=False,
        label="Departamento",
        queryset=Departamento.objects.all(),
    )
    asentamiento = forms.ModelChoiceField(
        required=False,
        label="Asentamiento",
        queryset=Asentamiento.objects.all(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["provincia"].queryset = Provincia.objects.all()
        if self.instance and self.instance.pk:
            municipio_actual = self.instance.municipio
            localidad_actual = self.instance.localidad
            departamento_actual = self.instance.departamento
            asentamiento_actual = self.instance.asentamiento

            if municipio_actual:
                self.fields["municipio"].choices = [
                    (municipio_actual.id, municipio_actual.nombre)
                ]
            if localidad_actual:
                self.fields["localidad"].choices = [
                    (localidad_actual.id, localidad_actual.nombre)
                ]
            if departamento_actual:
                self.fields["departamento"].choices = [
                    (departamento_actual.id, departamento_actual.nombre)
                ]
            if asentamiento_actual:
                self.fields["asentamiento"].choices = [
                    (asentamiento_actual.id, asentamiento_actual.nombre)
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
            ) and Ciudadano.objects.filter(
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

    class Meta:
        model = Ciudadano
        exclude = ("creado", "modificado", "m2m_familiares", "m2m_alertas")
        widgets = {
            "estado": forms.Select(choices=[(True, "Activo"), (False, "Inactivo")]),
            "fecha_nacimiento": forms.DateInput(
                attrs={"type": "date"}, format="%Y-%m-%d"
            ),
            "municipio": forms.Select(attrs={"class": "select2 municipio-select"}),
            "departamento": forms.Select(
                attrs={"class": "select2 departamento-select"}
            ),
            "asentamiento": forms.Select(
                attrs={"class": "select2 asentamiento-select"}
            ),
            "localidad": forms.Select(attrs={"class": "select2 localidad-select"}),
            "provincia": forms.Select(attrs={"class": "select2 provincia-select"}),
        }
        labels = {
            "nombre": "Nombre",
            "apellido": "Apellidos",
            "foto": "",
            "provincia": "Provincia",
            "localidad": "Localidad",
            "municipio": "Municipio",
            "departamento": "Departamento",
            "asentamiento": "Asentamiento",
        }


class LegajoGrupoFamiliarForm(forms.ModelForm):
    class Meta:
        model = GrupoFamiliar
        fields = "__all__"


class NuevoLegajoFamiliarForm(forms.ModelForm):
    vinculo = forms.ModelChoiceField(
        queryset=VinculoFamiliar.objects.all(), required=True, label="Vínculo Familiar"
    )
    estado_relacion = forms.ModelChoiceField(
        queryset=EstadoRelacion.objects.all(), required=True, label="Estado de Relación"
    )
    conviven = forms.ChoiceField(choices=BOOLEAN_CHOICE, required=True)
    cuidador_principal = forms.ChoiceField(choices=BOOLEAN_CHOICE, required=True)
    documento = forms.IntegerField(
        required=False,
        validators=[MinValueValidator(3000000), MaxValueValidator(100000000)],
        widget=forms.NumberInput(),
    )

    class Meta:
        model = Ciudadano
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
            "fecha_nacimiento": forms.DateInput(
                attrs={"type": "date"}, format="%Y-%m-%d"
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        tipo_doc = cleaned_data.get("tipo_doc")
        documento = cleaned_data.get("documento")
        fecha_nacimiento = cleaned_data.get("fecha_nacimiento")

        # Validación de campo único, combinación de DNI + Tipo DNI
        if Ciudadano.objects.filter(tipo_doc=tipo_doc, documento=documento).exists():
            self.add_error(
                "documento", "Ya existe un legajo con ese TIPO y NÚMERO de documento."
            )

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


class GrupoHogarForm(forms.ModelForm):
    vinculo = forms.ModelChoiceField(
        queryset=VinculoFamiliar.objects.all(), required=True, label="Vínculo Familiar"
    )
    estado_relacion = forms.ModelChoiceField(
        queryset=EstadoRelacion.objects.all(), required=True, label="Estado de Relación"
    )
    documento = forms.IntegerField(
        required=False,
        validators=[MinValueValidator(3000000), MaxValueValidator(100000000)],
        widget=forms.NumberInput(),
    )

    class Meta:
        model = LegajoGrupoHogar
        fields = ["vinculo", "documento", "estado_relacion"]
        widgets = {
            "fecha_nacimiento": forms.DateInput(
                attrs={"type": "date"}, format="%Y-%m-%d"
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        tipo_doc = cleaned_data.get("tipo_doc")
        documento = cleaned_data.get("documento")
        fecha_nacimiento = cleaned_data.get("fecha_nacimiento")
        # Validación de campo unico, combinación de DNI + Tipo DNI
        if Ciudadano.objects.filter(tipo_doc=tipo_doc, documento=documento).exists():
            self.add_error(
                "documento", "Ya existe un legajo con ese TIPO y NÚMERO de documento."
            )
        # validación de fecha de nacimiento
        if fecha_nacimiento and fecha_nacimiento > date.today():
            self.add_error(
                "fecha_nacimiento", "La fecha de termino debe ser menor al día de hoy."
            )

        return cleaned_data


class AlertasForm(forms.ModelForm):
    categoria = forms.ModelChoiceField(
        required=True,
        label="Categoría",
        queryset=CategoriaAlertas.objects.all(),
        widget=forms.Select(attrs={"class": "select2"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["legajo"].widget = forms.HiddenInput()
        self.fields["creada_por"].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()
        alerta = cleaned_data.get("alerta")
        legajo = cleaned_data.get("legajo")
        if (
            alerta
            and legajo
            and Alerta.objects.filter(alerta=alerta, legajo=legajo).exists()
        ):
            self.add_error("alerta", "Ya existe esa alerta en el legajo")
        return cleaned_data

    class Meta:
        model = Alerta
        fields = "__all__"
        widgets = {
            "alerta": forms.Select(attrs={"class": "select2"}),
        }
        labels = {"alerta": "Alerta"}


class LegajosArchivosForm(forms.ModelForm):
    class Meta:
        model = LegajosArchivos
        fields = ["legajo", "archivo"]


class LegajosDerivacionesForm(forms.ModelForm):
    archivos = MultipleFileField(label="Seleccionar archivos", required=False)
    # archivos = forms.FileField(
    #     widget=forms.ClearableFileInput(
    #         attrs={
    #             "multiple": True,
    #         }
    #     ),
    #     required=False,
    # )

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
            "legajo": "Legajo",
            "organismo": "Organismo relacionado",
            "m2m_alertas": "Alertas detectadas",
            "programa": "Derivar a",
            "programa_solicitante": "Derivar de",
        }


# Dimensiones
class DimensionFamiliaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["legajo"].widget = forms.HiddenInput()

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
    hay_desmoronamiento = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿Existe riesgo de desmoronamiento?",
        required=False,
    )
    PoseenCelular = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿En tu hogar cuentan con Teléfonos celulares?",
        required=False,
    )
    PoseenPC = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿En tu hogar cuentan con Computadoras? (de escritorio / laptop / tablet) ?",
        required=False,
    )
    Poseeninternet = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿En tu hogar cuentan con Internet (a través del celular o por conexión en la vivienda - wifi)?",
        required=False,
    )
    hay_agua_caliente = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿Tienen agua caliente?",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["legajo"].widget = forms.HiddenInput()

    class Meta:
        model = DimensionVivienda
        fields = "__all__"
        labels = {
            "posesion": "Posesión de la vivienda",
            "tipo": "Tipo de vivienda",
            "material": "Material de construcción",
            "pisos": "Material principal de los pisos interiores",
            "cant_ambientes": "¿Cuántas habitaciones tiene el hogar? (sin contar baño/s, cocina,pasillo/s, lavadero)",
            "cant_convivientes": "¿Cuantas personas viven en la vivienda?",
            "cant_menores": "¿Cuántos de ellos son menores de 18 años?",
            "cant_camas": "¿Cuántas camas/ colchones tienen?",
            "cant_hogares": "¿Cuantos hogares hay en la vivienda?",
            "obs_vivienda": "Observaciones",
            "ContextoCasa": "La vivienda está ubicada...",
            "gas": "¿Que utilizan principalmente para cocinar?",
            "techos": "Material de la cubierta exterior de la vivienda",
            "agua": "El agua que utilizan para cocinar proviene de...",
            "desague": "El desagüe del inodoro es...",
            "hay_banio": "Baño dentro de la vivienda con descarga",
        }
        widgets = {
            "obs_vivienda": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
        }

    # <!-- ./Nuevos campos vivienda Form Editar o cargar -->


class DimensionSaludForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["legajo"].widget = forms.HiddenInput()

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
        queryset=Provincia.objects.all(),
    )
    municipioInstitucion = forms.ModelChoiceField(
        label="Municipio",
        queryset=Municipio.objects.none(),
    )
    localidadInstitucion = forms.ModelChoiceField(
        label="Localidad",
        queryset=Localidad.objects.none(),
    )
    interesCapLab = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿Tenés interés en realizar cursos de capacitación laboral?",
    )
    realizandoCurso = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿Actualmente te encontrás haciendo algún curso de capacitación?",
    )
    oficio = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿Tenés conocimiento de algún oficio?",
    )
    interesEstudio = forms.ChoiceField(
        choices=BOOLEAN_CHOICE, widget=forms.Select, label="¿Tenés interés en estudiar?"
    )
    interesCurso = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿Tenés interés en realizar algún curso?",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["legajo"].widget = forms.HiddenInput()

        # Configurar el queryset del campo 'provinciaInstitucion' para cargar solo las provincias
        self.fields["provinciaInstitucion"].queryset = Provincia.objects.all()
        # Configurar los querysets de los campos 'municipioInstitucion' y 'localidadInstitucion' para que estén vacíos inicialmente
        self.fields["municipioInstitucion"].queryset = Municipio.objects.none()
        self.fields["localidadInstitucion"].queryset = Localidad.objects.none()

        # Actualizar los querysets si los datos están presentes en el formulario
        if "municipioInstitucion" in self.data:
            try:
                municipio_id = int(self.data.get("municipioInstitucion"))
                self.fields["municipioInstitucion"].queryset = Municipio.objects.filter(
                    id=municipio_id
                ).order_by("nombre")
            except (ValueError, TypeError):
                self.fields["municipioInstitucion"].queryset = Municipio.objects.none()

        if "localidadInstitucion" in self.data:
            try:
                localidad_id = int(self.data.get("localidadInstitucion"))
                self.fields["localidadInstitucion"].queryset = Localidad.objects.filter(
                    id=localidad_id
                ).order_by("nombre")
            except (ValueError, TypeError):
                self.fields["localidadInstitucion"].queryset = Localidad.objects.none()

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
    recibe_plan = forms.ChoiceField(
        choices=BOOLEAN_CHOICE, widget=forms.Select, label="¿Recibe planes sociales?"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["legajo"].widget = forms.HiddenInput()

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
    busquedaLaboral = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿Buscaste trabajo en los últimos 30 días?",
    )
    conviviente_trabaja = forms.ChoiceField(
        choices=BOOLEAN_CHOICE, widget=forms.Select, label="¿Conviviente trabaja?"
    )
    tiene_trabajo = forms.ChoiceField(
        choices=BOOLEAN_CHOICE,
        widget=forms.Select,
        label="¿Actualmente realizás alguna actividad laboral, productiva o comunitaria?",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["legajo"].widget = forms.HiddenInput()

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
            "subintervencion": forms.Select(
                attrs={"class": "select2 subintervencion-select"}
            ),
            "tipo_intervencion": forms.Select(
                attrs={"class": "select2 tipo_intervencion-select"}
            ),
        }
        labels = {
            "detalles": "Detalles de la intervención",
            "subintervencion": "Subintervención",
            "tipo_intervencion": "Tipo de intervención",
            "estado": "Estado",
            "direccion": "Dirección",
        }


class LlamadoForm(forms.ModelForm):
    subtipollamado = forms.FileField(
        widget=forms.Select(attrs={"class": "select2 subtipollamado-select"}),
        required=False,
        label="Subtipo de llamado",
    )

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
            "tipo_llamado": forms.Select(
                attrs={"class": "select2 tipo_llamado-select"}
            ),
            "programas_llamados": forms.Select(
                attrs={"class": "select2 programasllamado-select"}
            ),
        }
        labels = {
            "subtipollamado": "Subtipo de llamado",
            "tipo_llamado": "Tipo de llamado",
            "estado": "Estado",
            "programas_llamados": "Programa llamado",
        }


class LegajoProgramasForm(forms.ModelForm):
    class Meta:
        model = CiudadanoPrograma
        fields = ["programas"]
        widgets = {
            "programas": forms.SelectMultiple(
                attrs={
                    "class": "select2 w-100",
                    "style": "width: 100%;",
                    "multiple": True,
                },
            ),
        }
        labels = {
            "programas": "",
        }
