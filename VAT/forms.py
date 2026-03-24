from django import forms
from django.contrib.auth.models import User
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
    AutoridadInstitucional,
    InstitucionIdentificadorHist,
    InstitucionUbicacion,
    OfertaInstitucional,
    Comision,
    ComisionHorario,
    Inscripcion,
    Evaluacion,
    ResultadoEvaluacion,
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
            "modalidad_institucional",
            "tipo_gestion",
            "clase_institucion",
            "situacion",
            "fecha_alta",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["referente"].queryset = User.objects.filter(
            groups__name="ReferenteCentroVAT"
        ).only("id", "username", "first_name", "last_name")

        self.fields["organizacion_asociada"].empty_label = "Seleccionar organización..."


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
        widget=forms.Textarea(
            attrs={"class": "form-control", "rows": 4}
        ),
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
        widget=forms.Textarea(
            attrs={"class": "form-control", "rows": 4}
        ),
    )

    class Meta:
        model = Subsector
        fields = ["sector", "nombre", "descripcion"]


class TituloReferenciaForm(forms.ModelForm):
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
        widget=forms.Textarea(
            attrs={"class": "form-control", "rows": 4}
        ),
    )
    activo = forms.BooleanField(
        label="Activo",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    class Meta:
        model = TituloReferencia
        fields = ["sector", "subsector", "nombre", "codigo_referencia", "descripcion", "activo"]


class ModalidadCursadaForm(forms.ModelForm):
    nombre = forms.CharField(
        label="Nombre de la Modalidad",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    descripcion = forms.CharField(
        label="Descripción",
        required=False,
        widget=forms.Textarea(
            attrs={"class": "form-control", "rows": 4}
        ),
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
    titulo_referencia = forms.ModelChoiceField(
        queryset=TituloReferencia.objects.all(),
        label="Título de Referencia",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    modalidad_cursada = forms.ModelChoiceField(
        queryset=ModalidadCursada.objects.all(),
        label="Modalidad de Cursado",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    version = forms.CharField(
        label="Versión",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    normativa = forms.CharField(
        label="Normativa",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
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
            ("titulo_tecnico", "Título Técnico"),
        ],
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    frecuencia = forms.ChoiceField(
        label="Frecuencia",
        required=False,
        choices=[
            ("", "---------"),
            ("1_vez", "1 vez por semana"),
            ("2_veces", "2 veces por semana"),
            ("3_veces", "3 veces por semana"),
            ("4_veces", "4 veces por semana"),
            ("5_veces", "5 veces por semana"),
            ("intensivo", "Intensivo"),
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
            "titulo_referencia",
            "modalidad_cursada",
            "version",
            "normativa",
            "horas_reloj",
            "nivel_requerido",
            "nivel_certifica",
            "frecuencia",
            "activo",
        ]


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
    tipo = forms.ChoiceField(
        label="Tipo de Contacto",
        choices=InstitucionContacto.TIPO_CONTACTO_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    valor = forms.CharField(
        label="Valor",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    es_principal = forms.BooleanField(
        label="Es Principal",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    observaciones = forms.CharField(
        label="Observaciones",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
    )
    vigencia_hasta = forms.DateField(
        label="Vigencia Hasta",
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )

    class Meta:
        model = InstitucionContacto
        fields = ["centro", "tipo", "valor", "es_principal", "observaciones", "vigencia_hasta"]


class AutoridadInstitucionalForm(forms.ModelForm):
    centro = forms.ModelChoiceField(
        queryset=Centro.objects.all(),
        label="Centro",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    nombre_completo = forms.CharField(
        label="Nombre Completo",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    dni = forms.CharField(
        label="DNI",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    CARGO_CHOICES = [
        ("", "---------"),
        ("Director/a", "Director/a"),
        ("Vicedirector/a", "Vicedirector/a"),
        ("Coordinador/a Pedagógico/a", "Coordinador/a Pedagógico/a"),
        ("Coordinador/a Técnico/a", "Coordinador/a Técnico/a"),
        ("Secretario/a", "Secretario/a"),
        ("Pro-Secretario/a", "Pro-Secretario/a"),
        ("Representante Legal", "Representante Legal"),
        ("otro", "Otro"),
    ]

    cargo = forms.ChoiceField(
        label="Cargo",
        choices=CARGO_CHOICES,
        widget=forms.Select(attrs={"class": "form-control", "id": "id_cargo"}),
    )
    cargo_otro = forms.CharField(
        label="Especificar cargo",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Descripción del cargo"}),
    )
    email = forms.EmailField(
        label="Email",
        required=False,
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )
    telefono = forms.CharField(
        label="Teléfono",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    es_actual = forms.BooleanField(
        label="Es la Autoridad Actual",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    vigencia_hasta = forms.DateField(
        label="Vigencia Hasta",
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si el valor guardado no está en las opciones, es un "otro" personalizado
        instance = kwargs.get("instance")
        if instance and instance.cargo:
            valores_conocidos = [c[0] for c in self.CARGO_CHOICES if c[0]]
            if instance.cargo not in valores_conocidos:
                self.fields["cargo"].initial = "otro"
                self.fields["cargo_otro"].initial = instance.cargo

    def clean(self):
        cleaned_data = super().clean()
        cargo = cleaned_data.get("cargo")
        cargo_otro = cleaned_data.get("cargo_otro", "").strip()
        if cargo == "otro":
            if not cargo_otro:
                self.add_error("cargo_otro", "Debe especificar el cargo.")
            else:
                cleaned_data["cargo"] = cargo_otro
        return cleaned_data

    class Meta:
        model = AutoridadInstitucional
        fields = ["centro", "nombre_completo", "dni", "cargo", "email", "telefono", "es_actual", "vigencia_hasta"]


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
    rol_institucional = forms.ChoiceField(
        label="Rol Institucional",
        choices=[("", "---")] + list(InstitucionIdentificadorHist.ROL_INSTITUCIONAL_CHOICES),
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

    class Meta:
        model = InstitucionIdentificadorHist
        fields = ["centro", "tipo_identificador", "valor_identificador", "rol_institucional", "es_actual", "vigencia_hasta", "motivo"]


class InstitucionUbicacionForm(forms.ModelForm):
    centro = forms.ModelChoiceField(
        queryset=Centro.objects.all(),
        label="Centro",
        widget=forms.Select(attrs={"class": "form-control", "id": "id_centro_ubicacion"}),
    )
    localidad = forms.ModelChoiceField(
        queryset=Localidad.objects.none(),
        label="Localidad",
        widget=forms.Select(attrs={"class": "form-control", "id": "id_localidad_ubicacion"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # En edición: pre-filtrar localidades por el municipio del centro guardado
        centro = None
        if self.instance and self.instance.pk and self.instance.centro_id:
            centro = self.instance.centro
        elif "centro" in self.data:
            try:
                from VAT.models import Centro as CentroModel
                centro = CentroModel.objects.select_related("municipio", "provincia").get(pk=self.data["centro"])
            except (CentroModel.DoesNotExist, ValueError):
                pass
        if centro:
            qs = Localidad.objects.order_by("nombre")
            if centro.municipio_id:
                qs = qs.filter(municipio_id=centro.municipio_id)
            elif centro.provincia_id:
                qs = qs.filter(municipio__provincia_id=centro.provincia_id)
            self.fields["localidad"].queryset = qs
    rol_ubicacion = forms.ChoiceField(
        label="Rol de Ubicación",
        choices=InstitucionUbicacion.ROL_UBICACION_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    domicilio = forms.CharField(
        label="Domicilio",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    es_principal = forms.BooleanField(
        label="Es Principal",
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
        fields = ["centro", "localidad", "rol_ubicacion", "domicilio", "es_principal", "observaciones"]


# ============================================================================
# PHASE 4 - OFERTA INSTITUCIONAL FORMS
# ============================================================================

class OfertaInstitucionalForm(forms.ModelForm):
    centro = forms.ModelChoiceField(
        queryset=Centro.objects.all(),
        label="Centro",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    plan_curricular = forms.ModelChoiceField(
        queryset=PlanVersionCurricular.objects.all(),
        label="Plan Curricular",
        widget=forms.Select(attrs={"class": "form-control"}),
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
        fields = ["centro", "plan_curricular", "programa", "nombre_local", "ciclo_lectivo", "estado", "costo", "usa_voucher", "fecha_publicacion", "observaciones"]


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
        fields = ["oferta", "ubicacion", "codigo_comision", "nombre", "fecha_inicio", "fecha_fin", "cupo", "estado", "observaciones"]


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
        fields = ["comision", "dia_semana", "hora_desde", "hora_hasta", "aula_espacio", "vigente"]


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
        fields = ["ciudadano", "comision", "programa", "estado", "origen_canal", "observaciones"]


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
        fields = ["comision", "tipo", "nombre", "descripcion", "fecha", "es_final", "ponderacion", "observaciones"]


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
            attrs={"class": "form-control"}
        ),
    )
    observaciones = forms.CharField(
        label="Observaciones",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
    )

    class Meta:
        model = ResultadoEvaluacion
        fields = ["evaluacion", "inscripcion", "calificacion", "aprobo", "observaciones"]


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
        choices=[("suma", "Sumar al saldo existente"), ("reinicia", "Reiniciar al valor configurado")],
        widget=forms.RadioSelect(),
        initial="suma",
    )

    def clean_fecha_vencimiento(self):
        from datetime import date
        fecha = self.cleaned_data.get("fecha_vencimiento")
        if fecha and fecha <= date.today():
            raise forms.ValidationError("La fecha de vencimiento debe ser posterior a hoy.")
        return fecha

    class Meta:
        from VAT.models import VoucherParametria
        model = VoucherParametria
        fields = ["nombre", "descripcion", "programa", "cantidad_inicial", "fecha_vencimiento", "renovacion_mensual", "cantidad_renovacion", "renovacion_tipo"]

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
        from datetime import date
        fecha = self.cleaned_data.get("fecha_vencimiento")
        if fecha and fecha <= date.today():
            raise forms.ValidationError("La fecha de vencimiento debe ser posterior a hoy.")
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
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 5,
            "placeholder": "Ej: 12345678, 23456789, 34567890",
        }),
    )

    def clean_dnis(self):
        raw = self.cleaned_data["dnis"]
        import re
        dnis = [d.strip() for d in re.split(r"[\s,;]+", raw) if d.strip()]
        if not dnis:
            raise forms.ValidationError("Ingresá al menos un DNI.")
        if len(dnis) > 500:
            raise forms.ValidationError("No se pueden asignar más de 500 vouchers a la vez.")
        return dnis
