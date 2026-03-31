from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.utils import timezone

from ciudadanos.models import Ciudadano
from core.fields import UnicodeEmailField
from core.models import Localidad, Municipio, Provincia
from core.soft_delete import SoftDeleteModelMixin
from centrodeinfancia.formulario_cdi_schema import (
    CAMPOS_OPCIONES,
    CAMPOS_OPCIONES_MULTIPLES,
    OPCIONES_DIAS_SEMANA,
)
import centrodeinfancia.models_cdi_relaciones as _models_cdi_relaciones

FormularioCDIArticulationFrequency = (
    _models_cdi_relaciones.FormularioCDIArticulationFrequency
)
FormularioCDIRoomDistribution = _models_cdi_relaciones.FormularioCDIRoomDistribution
FormularioCDIWaitlistByAgeGroup = _models_cdi_relaciones.FormularioCDIWaitlistByAgeGroup
IntervencionCentroInfancia = _models_cdi_relaciones.IntervencionCentroInfancia
ObservacionCentroInfancia = _models_cdi_relaciones.ObservacionCentroInfancia


CUIT_VALIDATOR = RegexValidator(
    regex=r"^\d{11}$",
    message="Ingrese un CUIT válido de 11 dígitos.",
)
PHONE_VALIDATOR = RegexValidator(
    regex=r"^\d+(?:-\d+)*$",
    message=(
        "Ingrese un teléfono válido: solo números o grupos numéricos separados por "
        "guiones."
    ),
)

CODIGO_POSTAL_VALIDATORS = [
    MinValueValidator(0),
    MaxValueValidator(9999999999),
]


def normalizar_cuit(value):
    if value in (None, ""):
        return ""
    return "".join(ch for ch in str(value) if ch.isdigit())


def validar_opciones_multiples(field_name, value):
    allowed = {item[0] for item in CAMPOS_OPCIONES_MULTIPLES[field_name]}
    if value in (None, ""):
        return
    if not isinstance(value, list):
        raise ValidationError({field_name: "Seleccione opciones válidas."})
    invalid_values = [item for item in value if item not in allowed]
    if invalid_values:
        raise ValidationError({field_name: "Seleccione opciones válidas."})


class CentroDeInfancia(SoftDeleteModelMixin, models.Model):
    nombre = models.CharField(max_length=255)
    codigo_cdi = models.CharField(
        max_length=32,
        unique=True,
        blank=True,
        null=True,
        verbose_name="Codigo CDI",
    )
    organizacion = models.CharField(
        max_length=1000,
        null=True,
        blank=True,
        verbose_name="Denominación del organismo u organización que gestiona",
    )
    cuit_organizacion_gestiona = models.CharField(
        max_length=11,
        blank=True,
        null=True,
        validators=[CUIT_VALIDATOR],
        verbose_name="CUIT del organismo u organización que gestiona",
    )
    provincia = models.ForeignKey(
        Provincia,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    departamento = models.ForeignKey(
        "DepartamentoIpi",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Departamento",
    )
    municipio = models.ForeignKey(
        Municipio,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    localidad = models.ForeignKey(
        Localidad,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    codigo_postal = models.PositiveBigIntegerField(
        blank=True,
        null=True,
        validators=CODIGO_POSTAL_VALIDATORS,
        verbose_name="Código postal",
    )
    ambito = models.CharField(
        max_length=32,
        choices=CAMPOS_OPCIONES["ambito"],
        default="sin_informacion",
        verbose_name="Ámbito",
    )
    calle = models.CharField(max_length=255, blank=True, null=True)
    numero = models.CharField(max_length=50, blank=True, null=True)
    latitud = models.DecimalField(
        max_digits=8,
        decimal_places=6,
        blank=True,
        null=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    longitud = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )
    telefono = models.CharField(max_length=50, blank=True, null=True)
    mail = UnicodeEmailField(verbose_name="Mail", blank=True, null=True)
    nombre_referente = models.CharField(max_length=255, blank=True, null=True)
    apellido_referente = models.CharField(max_length=255, blank=True, null=True)
    email_referente = models.EmailField(blank=True, null=True)
    telefono_referente = models.CharField(max_length=50, blank=True, null=True)
    meses_funcionamiento = models.JSONField(default=list, blank=True)
    dias_funcionamiento = models.JSONField(default=list, blank=True)
    tipo_jornada = models.CharField(
        max_length=64,
        choices=CAMPOS_OPCIONES["tipo_jornada"],
        blank=True,
        null=True,
    )
    tipo_jornada_otra = models.CharField(max_length=255, blank=True, null=True)
    oferta_servicios = models.CharField(
        max_length=64,
        choices=CAMPOS_OPCIONES["oferta_servicios"],
        blank=True,
        null=True,
    )
    modalidad_gestion = models.CharField(
        max_length=64,
        choices=CAMPOS_OPCIONES["modalidad_gestion"],
        blank=True,
        null=True,
    )
    modalidad_gestion_otra = models.CharField(max_length=255, blank=True, null=True)
    fecha_inicio = models.DateField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Centro de Desarrollo Infantil"
        verbose_name_plural = "Centros de Desarrollo Infantil"
        ordering = ["nombre"]

    def __str__(self):
        return str(self.nombre)

    def clean(self):
        super().clean()
        errors = {}
        if (
            self.departamento_id
            and self.provincia_id
            and self.departamento.provincia_id != self.provincia_id
        ):
            errors["departamento"] = (
                "El departamento no pertenece a la provincia seleccionada."
            )

        for field_name in ("meses_funcionamiento", "dias_funcionamiento"):
            try:
                validar_opciones_multiples(field_name, getattr(self, field_name))
            except ValidationError as exc:
                errors.update(exc.message_dict)

        self.cuit_organizacion_gestiona = (
            normalizar_cuit(self.cuit_organizacion_gestiona) or None
        )

        if self.tipo_jornada == "other" and not (self.tipo_jornada_otra or "").strip():
            errors["tipo_jornada_otra"] = "Este campo es obligatorio."

        if self.tipo_jornada != "other":
            self.tipo_jornada_otra = ""

        if (
            self.modalidad_gestion == "otra"
            and not (self.modalidad_gestion_otra or "").strip()
        ):
            errors["modalidad_gestion_otra"] = "Este campo es obligatorio."

        if self.modalidad_gestion != "otra":
            self.modalidad_gestion_otra = ""

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.codigo_cdi:
            codigo_cdi = f"CDI-{self.pk:06d}"
            type(self).objects.filter(pk=self.pk).update(codigo_cdi=codigo_cdi)
            self.codigo_cdi = codigo_cdi


class CentroDeInfanciaHorarioFuncionamiento(models.Model):
    centro = models.ForeignKey(
        CentroDeInfancia,
        on_delete=models.CASCADE,
        related_name="horarios_funcionamiento",
    )
    dia = models.CharField(max_length=16, choices=OPCIONES_DIAS_SEMANA)
    hora_apertura = models.TimeField(blank=True, null=True)
    hora_cierre = models.TimeField(blank=True, null=True)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["centro", "dia"],
                name="uniq_cdi_horario_funcionamiento_dia",
            )
        ]
        verbose_name = "Horario de funcionamiento del CDI"
        verbose_name_plural = "Horarios de funcionamiento del CDI"

    def clean(self):
        super().clean()
        errors = {}
        if bool(self.hora_apertura) != bool(self.hora_cierre):
            errors["hora_cierre"] = (
                "Debe completar horario de apertura y cierre para el día."
            )
        if (
            self.hora_apertura
            and self.hora_cierre
            and self.hora_apertura >= self.hora_cierre
        ):
            errors["hora_cierre"] = (
                "El horario de cierre debe ser posterior al de apertura."
            )
        if errors:
            raise ValidationError(errors)


class DepartamentoIpi(models.Model):
    codigo_departamento = models.CharField(max_length=10, unique=True)
    provincia = models.ForeignKey(
        Provincia,
        on_delete=models.PROTECT,
        related_name="departamentos_ipi",
    )
    nombre = models.CharField(max_length=255)
    tamano_demografico = models.CharField(max_length=255, blank=True, null=True)
    decil_ipi = models.PositiveSmallIntegerField(blank=True, null=True)
    nivel_inequidad_ipi = models.CharField(max_length=64, blank=True, null=True)
    porcentaje_ninos_lista_espera_cdi = models.DecimalField(
        max_digits=20,
        decimal_places=15,
        blank=True,
        null=True,
    )
    poblacion_0_a_4_anios = models.PositiveIntegerField(blank=True, null=True)
    porcentaje_poblacion_0_a_4_anios = models.DecimalField(
        max_digits=20,
        decimal_places=15,
        blank=True,
        null=True,
    )
    porcentaje_poblacion_0_a_4_anios_con_nbi = models.DecimalField(
        max_digits=20,
        decimal_places=15,
        blank=True,
        null=True,
    )
    porcentaje_poblacion_0_a_4_anios_hogares_monoparentales = models.DecimalField(
        max_digits=20,
        decimal_places=15,
        blank=True,
        null=True,
    )
    tasa_natalidad_2018 = models.DecimalField(
        max_digits=20,
        decimal_places=15,
        blank=True,
        null=True,
    )
    tasa_mortalidad_infantil_2018 = models.DecimalField(
        max_digits=20,
        decimal_places=15,
        blank=True,
        null=True,
    )
    porcentaje_familias_barrios_populares = models.DecimalField(
        max_digits=20,
        decimal_places=15,
        blank=True,
        null=True,
    )
    cantidad_barrios_populares = models.PositiveIntegerField(blank=True, null=True)
    cantidad_asistentes_cdi = models.PositiveIntegerField(blank=True, null=True)
    cantidad_ninos_lista_espera_cdi = models.PositiveIntegerField(
        blank=True,
        null=True,
    )
    poblacion_0_a_4_anios_hogares_monoparentales = models.PositiveIntegerField(
        blank=True,
        null=True,
    )
    poblacion_0_a_4_anios_con_nbi = models.PositiveIntegerField(
        blank=True,
        null=True,
    )
    total_hogares_censo_2010 = models.PositiveIntegerField(blank=True, null=True)
    poblacion_total = models.PositiveIntegerField(blank=True, null=True)
    cantidad_familias_barrios_populares = models.PositiveIntegerField(
        blank=True,
        null=True,
    )
    cantidad_establecimientos_nivel_inicial = models.PositiveIntegerField(
        blank=True,
        null=True,
    )
    tasa_establecimientos_cada_mil_ninos = models.DecimalField(
        max_digits=20,
        decimal_places=15,
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["provincia__nombre", "nombre"]
        verbose_name = "Departamento IPI"
        verbose_name_plural = "Departamentos IPI"
        constraints = [
            models.UniqueConstraint(
                fields=["provincia", "nombre"],
                name="uniq_departamento_ipi_provincia_nombre",
            )
        ]

    def __str__(self):
        return f"{self.nombre} ({self.provincia})"


class Trabajador(SoftDeleteModelMixin, models.Model):
    class Rol(models.TextChoices):
        PROFESOR = "profesor", "Profesor"
        DIRECTOR = "director", "Director"
        ADMINISTRATIVO = "administrativo", "Administrativo"

    centro = models.ForeignKey(
        CentroDeInfancia,
        on_delete=models.CASCADE,
        related_name="trabajadores",
    )
    nombre = models.CharField(max_length=255)
    apellido = models.CharField(max_length=255)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    rol = models.CharField(max_length=20, choices=Rol.choices)

    class Meta:
        verbose_name = "Trabajador"
        verbose_name_plural = "Trabajadores"
        ordering = ["apellido", "nombre"]

    def __str__(self):
        return f"{self.apellido}, {self.nombre}"


class NominaCentroInfancia(SoftDeleteModelMixin, models.Model):
    class RespuestaSiNoNsNc(models.TextChoices):
        SI = "si", "Si"
        NO = "no", "No"
        NS_NC = "ns_nc", "Ns/Nc"

    class TipoDiscapacidad(models.TextChoices):
        MOTORA = "motora", "Motora"
        VISUAL = "visual", "Visual"
        AUDITIVA = "auditiva", "Auditiva"
        INTELECTUAL = "intelectual", "Intelectual"
        MENTAL = "mental", "Mental"
        VISCERAL = "visceral", "Visceral"
        MULTIPLE = "multiple", "Múltiple"
        NS_NC = "ns_nc", "Ns/Nc"

    class SexoChoices(models.TextChoices):
        FEMENINO = "Femenino", "Femenino"
        MASCULINO = "Masculino", "Masculino"
        X = "X", "X"

    ESTADO_PENDIENTE = "pendiente"
    ESTADO_ACTIVO = "activo"
    ESTADO_BAJA = "baja"

    ESTADO_CHOICES = [
        (ESTADO_ACTIVO, "Activo"),
        (ESTADO_PENDIENTE, "Pendiente"),
        (ESTADO_BAJA, "Baja"),
    ]

    centro = models.ForeignKey(
        CentroDeInfancia,
        on_delete=models.CASCADE,
        related_name="nominas",
    )
    ciudadano = models.ForeignKey(
        Ciudadano,
        on_delete=models.CASCADE,
        related_name="nominas_centros_infancia",
    )
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default=ESTADO_PENDIENTE,
    )
    dni = models.PositiveBigIntegerField(blank=True, null=True)
    apellido = models.CharField(max_length=255, blank=True, null=True)
    nombre = models.CharField(max_length=255, blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    sexo = models.CharField(
        max_length=20,
        choices=SexoChoices.choices,
        blank=True,
        null=True,
    )
    nacionalidad = models.CharField(max_length=255, blank=True, null=True)
    sala = models.CharField(max_length=255, blank=True, null=True)

    pertenece_pueblo_originario = models.CharField(
        max_length=16,
        choices=RespuestaSiNoNsNc.choices,
        blank=True,
        null=True,
    )
    pueblo_originario_cual = models.CharField(max_length=255, blank=True, null=True)
    habla_lengua_originaria_hogar = models.CharField(
        max_length=16,
        choices=RespuestaSiNoNsNc.choices,
        blank=True,
        null=True,
    )

    talla = models.CharField(max_length=50, blank=True, null=True)
    peso = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    calendario_vacunacion_al_dia = models.BooleanField(blank=True, null=True)
    tiene_discapacidad = models.CharField(
        max_length=16,
        choices=RespuestaSiNoNsNc.choices,
        blank=True,
        null=True,
    )
    discapacidad_tipo = models.CharField(
        max_length=32,
        choices=TipoDiscapacidad.choices,
        blank=True,
        null=True,
    )
    recibe_apoyo_discapacidad = models.BooleanField(blank=True, null=True)
    posee_cud = models.BooleanField(blank=True, null=True)
    posee_obra_social = models.BooleanField(blank=True, null=True)

    calle_domicilio = models.CharField(max_length=255, blank=True, null=True)
    altura_domicilio = models.PositiveIntegerField(blank=True, null=True)
    piso_domicilio = models.CharField(max_length=50, blank=True, null=True)
    departamento_domicilio = models.CharField(max_length=50, blank=True, null=True)
    provincia_domicilio = models.ForeignKey(
        Provincia,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="+",
    )
    municipio_domicilio = models.ForeignKey(
        Municipio,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="+",
    )
    localidad_domicilio = models.ForeignKey(
        Localidad,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="+",
    )

    responsable_legal_1_apellido = models.CharField(
        max_length=255, blank=True, null=True
    )
    responsable_legal_1_nombre = models.CharField(max_length=255, blank=True, null=True)
    responsable_legal_1_dni = models.PositiveBigIntegerField(blank=True, null=True)
    responsable_legal_1_telefono = models.PositiveBigIntegerField(blank=True, null=True)
    responsable_legal_1_percibe_auh = models.CharField(
        max_length=16,
        choices=RespuestaSiNoNsNc.choices,
        blank=True,
        null=True,
    )
    responsable_legal_1_percibe_alimenta = models.CharField(
        max_length=16,
        choices=RespuestaSiNoNsNc.choices,
        blank=True,
        null=True,
    )

    responsable_legal_2_apellido = models.CharField(
        max_length=255, blank=True, null=True
    )
    responsable_legal_2_nombre = models.CharField(max_length=255, blank=True, null=True)
    responsable_legal_2_dni = models.PositiveBigIntegerField(blank=True, null=True)
    responsable_legal_2_telefono = models.PositiveBigIntegerField(blank=True, null=True)
    responsable_legal_2_percibe_auh = models.CharField(
        max_length=16,
        choices=RespuestaSiNoNsNc.choices,
        blank=True,
        null=True,
    )
    responsable_legal_2_percibe_alimenta = models.CharField(
        max_length=16,
        choices=RespuestaSiNoNsNc.choices,
        blank=True,
        null=True,
    )

    adulto_responsable_apellido = models.CharField(
        max_length=255, blank=True, null=True
    )
    adulto_responsable_nombre = models.CharField(max_length=255, blank=True, null=True)
    adulto_responsable_dni = models.PositiveBigIntegerField(blank=True, null=True)
    adulto_responsable_telefono = models.CharField(max_length=50, blank=True, null=True)
    adulto_responsable_parentesco = models.CharField(
        max_length=255, blank=True, null=True
    )
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Nómina Centro de Desarrollo Infantil"
        verbose_name_plural = "Nóminas Centro de Desarrollo Infantil"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.ciudadano} en {self.centro} ({self.get_estado_display()})"

    @property
    def edad(self):
        if not self.fecha_nacimiento:
            return None
        hoy = timezone.now().date()
        return (
            hoy.year
            - self.fecha_nacimiento.year
            - (
                (hoy.month, hoy.day)
                < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
            )
        )

    def clean(self):
        super().clean()
        errors = {}

        if self.pertenece_pueblo_originario != self.RespuestaSiNoNsNc.SI:
            self.pueblo_originario_cual = None
        elif not self.pueblo_originario_cual:
            errors["pueblo_originario_cual"] = (
                "Este campo es obligatorio cuando pertenece a un pueblo originario."
            )

        if self.tiene_discapacidad != self.RespuestaSiNoNsNc.SI:
            self.discapacidad_tipo = None
            self.recibe_apoyo_discapacidad = None
        elif not self.discapacidad_tipo:
            errors["discapacidad_tipo"] = (
                "Este campo es obligatorio cuando indica discapacidad."
            )

        relation_rules = (
            (
                "municipio_domicilio",
                "provincia_domicilio",
                "provincia_id",
                "El municipio no pertenece a la provincia indicada.",
            ),
            (
                "localidad_domicilio",
                "municipio_domicilio",
                "municipio_id",
                "La localidad no pertenece al municipio indicado.",
            ),
        )
        for child_field, parent_field, relation_attr, message in relation_rules:
            child_value = getattr(self, child_field)
            parent_id = getattr(self, f"{parent_field}_id")
            if (
                child_value
                and parent_id
                and getattr(child_value, relation_attr) != parent_id
            ):
                errors[child_field] = message

        if errors:
            raise ValidationError(errors)


class FormularioCDI(SoftDeleteModelMixin, models.Model):
    centro = models.ForeignKey(
        CentroDeInfancia,
        on_delete=models.CASCADE,
        related_name="formularios",
    )
    source_form_version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="formularios_cdi_creados",
    )

    fecha_relevamiento = models.DateField(blank=True, null=True)
    nombre_completo_respondente = models.CharField(
        max_length=255, blank=True, null=True
    )
    rol_respondente = models.CharField(max_length=255, blank=True, null=True)
    email_respondente = models.EmailField(max_length=255, blank=True, null=True)

    nombre_cdi = models.CharField(max_length=255, blank=True, null=True)
    codigo_cdi = models.CharField(max_length=32, blank=True, null=True, db_index=True)
    provincia_cdi = models.ForeignKey(
        Provincia,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="+",
    )
    departamento_cdi = models.ForeignKey(
        DepartamentoIpi,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="+",
    )
    municipio_cdi = models.ForeignKey(
        Municipio,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="+",
    )
    localidad_cdi = models.ForeignKey(
        Localidad,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="+",
    )
    ambito = models.CharField(
        max_length=32,
        choices=CAMPOS_OPCIONES["ambito"],
        default="sin_informacion",
        blank=True,
    )
    calle_cdi = models.CharField(max_length=255, blank=True, null=True)
    numero_puerta_cdi = models.CharField(max_length=255, blank=True, null=True)
    codigo_postal_cdi = models.PositiveBigIntegerField(
        blank=True,
        null=True,
        validators=CODIGO_POSTAL_VALIDATORS,
    )
    latitud_geografica_cdi = models.DecimalField(
        max_digits=8,
        decimal_places=6,
        blank=True,
        null=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    longitud_geografica_cdi = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )
    telefono_cdi = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[PHONE_VALIDATOR],
    )
    email_cdi = models.EmailField(max_length=255, blank=True, null=True)
    nombre_referente_cdi = models.CharField(max_length=255, blank=True, null=True)
    apellido_referente_cdi = models.CharField(max_length=255, blank=True, null=True)
    telefono_referente_cdi = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[PHONE_VALIDATOR],
    )
    email_referente_cdi = models.EmailField(max_length=255, blank=True, null=True)
    meses_funcionamiento = models.JSONField(default=list, blank=True)
    dias_funcionamiento = models.JSONField(default=list, blank=True)
    horario_apertura = models.TimeField(blank=True, null=True)
    horario_cierre = models.TimeField(blank=True, null=True)
    tipo_jornada = models.CharField(
        max_length=64,
        choices=CAMPOS_OPCIONES["tipo_jornada"],
        blank=True,
        null=True,
    )
    tipo_jornada_otra = models.CharField(max_length=255, blank=True, null=True)
    oferta_servicios = models.CharField(
        max_length=64,
        choices=CAMPOS_OPCIONES["oferta_servicios"],
        blank=True,
        null=True,
    )
    cantidad_total_ninos = models.PositiveIntegerField(blank=True, null=True)
    cantidad_total_personal = models.PositiveIntegerField(blank=True, null=True)

    modalidad_gestion = models.CharField(
        max_length=64,
        choices=CAMPOS_OPCIONES["modalidad_gestion"],
        blank=True,
        null=True,
    )
    modalidad_gestion_otra = models.CharField(max_length=255, blank=True, null=True)
    nombre_organizacion_gestora = models.CharField(
        max_length=1000, blank=True, null=True
    )
    cuit_organizacion_gestora = models.CharField(
        max_length=11,
        blank=True,
        null=True,
        validators=[CUIT_VALIDATOR],
    )
    provincia_organizacion = models.ForeignKey(
        Provincia,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="+",
    )
    departamento_organizacion = models.ForeignKey(
        DepartamentoIpi,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="+",
    )
    municipio_organizacion = models.ForeignKey(
        Municipio,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="+",
    )
    localidad_organizacion = models.ForeignKey(
        Localidad,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="+",
    )
    calle_organizacion = models.CharField(max_length=255, blank=True, null=True)
    numero_organizacion = models.PositiveIntegerField(blank=True, null=True)
    codigo_postal_organizacion = models.CharField(max_length=12, blank=True, null=True)
    edificio_organizacion = models.CharField(max_length=255, blank=True, null=True)
    piso_organizacion = models.CharField(max_length=255, blank=True, null=True)
    departamento_domicilio_organizacion = models.CharField(
        max_length=255, blank=True, null=True
    )
    oficina_organizacion = models.CharField(max_length=255, blank=True, null=True)
    telefono_organizacion = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[PHONE_VALIDATOR],
    )
    email_organizacion = models.EmailField(max_length=255, blank=True, null=True)
    nombre_referente_organizacion = models.CharField(
        max_length=255, blank=True, null=True
    )
    apellido_referente_organizacion = models.CharField(
        max_length=255, blank=True, null=True
    )
    telefono_referente_organizacion = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[PHONE_VALIDATOR],
    )
    email_referente_organizacion = models.EmailField(
        max_length=255, blank=True, null=True
    )
    modalidad_tenencia = models.CharField(
        max_length=64,
        choices=CAMPOS_OPCIONES["modalidad_tenencia"],
        blank=True,
        null=True,
    )
    modalidad_tenencia_otra = models.CharField(max_length=255, blank=True, null=True)
    uso_exclusivo_espacio = models.BooleanField(blank=True, null=True)
    cantidad_ambientes_sin_areas_servicio = models.PositiveIntegerField(
        blank=True, null=True
    )

    acceso_energia = models.CharField(
        max_length=64,
        choices=CAMPOS_OPCIONES["acceso_energia"],
        blank=True,
        null=True,
    )
    seguridad_electrica = models.CharField(
        max_length=64,
        choices=CAMPOS_OPCIONES["seguridad_electrica"],
        blank=True,
        null=True,
    )
    acceso_agua = models.CharField(
        max_length=64,
        choices=CAMPOS_OPCIONES["acceso_agua"],
        blank=True,
        null=True,
    )
    fuente_agua_segura_consumo = models.CharField(
        max_length=64,
        choices=CAMPOS_OPCIONES["fuente_agua_segura_consumo"],
        blank=True,
        null=True,
    )
    eliminacion_excretas = models.CharField(
        max_length=64,
        choices=CAMPOS_OPCIONES["eliminacion_excretas"],
        blank=True,
        null=True,
    )
    tiene_extintores_vigentes = models.BooleanField(blank=True, null=True)
    estado_botiquin_primeros_auxilios = models.CharField(
        max_length=128,
        choices=CAMPOS_OPCIONES["estado_botiquin_primeros_auxilios"],
        blank=True,
        null=True,
    )
    tiene_computadora_funcionando = models.BooleanField(blank=True, null=True)
    acceso_internet_personal = models.CharField(
        max_length=128,
        choices=CAMPOS_OPCIONES["acceso_internet_personal"],
        blank=True,
        null=True,
    )
    tiene_espacio_cocina = models.CharField(
        max_length=32,
        choices=CAMPOS_OPCIONES["tiene_espacio_cocina"],
        blank=True,
        null=True,
    )
    combustible_cocinar = models.CharField(
        max_length=64,
        choices=CAMPOS_OPCIONES["combustible_cocinar"],
        blank=True,
        null=True,
    )
    tiene_espacio_exterior = models.CharField(
        max_length=32,
        choices=CAMPOS_OPCIONES["tiene_espacio_exterior"],
        blank=True,
        null=True,
    )
    tiene_juegos_exteriores = models.CharField(
        max_length=32,
        choices=CAMPOS_OPCIONES["tiene_juegos_exteriores"],
        blank=True,
        null=True,
    )
    plan_evacuacion_y_simulacros = models.CharField(
        max_length=128,
        choices=CAMPOS_OPCIONES["plan_evacuacion_y_simulacros"],
        blank=True,
        null=True,
    )
    cobertura_capacitacion_primeros_auxilios = models.CharField(
        max_length=64,
        choices=CAMPOS_OPCIONES["cobertura_capacitacion_primeros_auxilios"],
        blank=True,
        null=True,
    )
    servicio_emergencia_medica = models.CharField(
        max_length=64,
        choices=CAMPOS_OPCIONES["servicio_emergencia_medica"],
        blank=True,
        null=True,
    )
    items_protocolo_salud = models.JSONField(default=list, blank=True)

    prestaciones_alimentarias = models.JSONField(default=list, blank=True)
    prestaciones_alimentarias_otra = models.CharField(
        max_length=255, blank=True, null=True
    )
    calidad_elaboracion_menu = models.CharField(
        max_length=128,
        choices=CAMPOS_OPCIONES["calidad_elaboracion_menu"],
        blank=True,
        null=True,
    )
    evaluacion_periodica_menu = models.CharField(
        max_length=128,
        choices=CAMPOS_OPCIONES["evaluacion_periodica_menu"],
        blank=True,
        null=True,
    )
    cobertura_capacitacion_manipulacion_alimentos = models.CharField(
        max_length=64,
        choices=CAMPOS_OPCIONES["cobertura_capacitacion_manipulacion_alimentos"],
        blank=True,
        null=True,
    )
    condiciones_almacenamiento_leche_humana = models.CharField(
        max_length=128,
        choices=CAMPOS_OPCIONES["condiciones_almacenamiento_leche_humana"],
        blank=True,
        null=True,
    )
    acciones_sensibilizacion_lactancia = models.CharField(
        max_length=64,
        choices=CAMPOS_OPCIONES["acciones_sensibilizacion_lactancia"],
        blank=True,
        null=True,
    )

    tiene_registro_lista_espera = models.CharField(
        max_length=16,
        choices=CAMPOS_OPCIONES["tiene_registro_lista_espera"],
        blank=True,
        null=True,
    )
    tiene_instrumento_priorizacion_ingreso = models.BooleanField(blank=True, null=True)
    cantidad_ninos_discapacidad = models.PositiveIntegerField(blank=True, null=True)
    cantidad_ninos_etnia_especifica = models.PositiveIntegerField(blank=True, null=True)
    tiene_personal_entrada_salida = models.CharField(
        max_length=16,
        choices=CAMPOS_OPCIONES["tiene_personal_entrada_salida"],
        blank=True,
        null=True,
    )

    frecuencia_comunicacion_familias = models.CharField(
        max_length=128,
        choices=CAMPOS_OPCIONES["frecuencia_comunicacion_familias"],
        blank=True,
        null=True,
    )
    frecuencia_talleres_crianza = models.CharField(
        max_length=64,
        choices=CAMPOS_OPCIONES["frecuencia_talleres_crianza"],
        blank=True,
        null=True,
    )
    realiza_acciones_promocion_acceso_derechos = models.CharField(
        max_length=16,
        choices=CAMPOS_OPCIONES["realiza_acciones_promocion_acceso_derechos"],
        blank=True,
        null=True,
    )
    realiza_acciones_acompanamiento_vulneracion_derechos = models.CharField(
        max_length=16,
        choices=CAMPOS_OPCIONES["realiza_acciones_acompanamiento_vulneracion_derechos"],
        blank=True,
        null=True,
    )

    nivel_trabajo_red = models.CharField(
        max_length=128,
        choices=CAMPOS_OPCIONES["nivel_trabajo_red"],
        blank=True,
        null=True,
    )
    protocolo_vulneracion_derechos = models.CharField(
        max_length=128,
        choices=CAMPOS_OPCIONES["protocolo_vulneracion_derechos"],
        blank=True,
        null=True,
    )

    nivel_equipo_tecnico = models.CharField(
        max_length=64,
        choices=CAMPOS_OPCIONES["nivel_equipo_tecnico"],
        blank=True,
        null=True,
    )

    frecuencia_registro_desarrollo_nino = models.CharField(
        max_length=32,
        choices=CAMPOS_OPCIONES["frecuencia_registro_desarrollo_nino"],
        blank=True,
        null=True,
    )
    frecuencia_registro_informacion_familiar = models.CharField(
        max_length=32,
        choices=CAMPOS_OPCIONES["frecuencia_registro_informacion_familiar"],
        blank=True,
        null=True,
    )
    frecuencia_registro_salud_vacunas = models.CharField(
        max_length=32,
        choices=CAMPOS_OPCIONES["frecuencia_registro_salud_vacunas"],
        blank=True,
        null=True,
    )
    participantes_proyecto_socioeducativo = models.CharField(
        max_length=128,
        choices=CAMPOS_OPCIONES["participantes_proyecto_socioeducativo"],
        blank=True,
        null=True,
    )
    planificacion_actividades_sala = models.CharField(
        max_length=128,
        choices=CAMPOS_OPCIONES["planificacion_actividades_sala"],
        blank=True,
        null=True,
    )
    planificacion_integral = models.CharField(
        max_length=128,
        choices=CAMPOS_OPCIONES["planificacion_integral"],
        blank=True,
        null=True,
    )
    formacion_direccion_primera_infancia = models.CharField(
        max_length=64,
        choices=CAMPOS_OPCIONES["formacion_direccion_primera_infancia"],
        blank=True,
        null=True,
    )

    cobertura_duplas_pedagogicas = models.CharField(
        max_length=32,
        choices=CAMPOS_OPCIONES["cobertura_duplas_pedagogicas"],
        blank=True,
        null=True,
    )
    cobertura_educadora_titulo_habilitante = models.CharField(
        max_length=32,
        choices=CAMPOS_OPCIONES["cobertura_educadora_titulo_habilitante"],
        blank=True,
        null=True,
    )
    cobertura_formacion_auxiliares = models.CharField(
        max_length=32,
        choices=CAMPOS_OPCIONES["cobertura_formacion_auxiliares"],
        blank=True,
        null=True,
    )
    modalidad_contratacion_principal = models.CharField(
        max_length=64,
        choices=CAMPOS_OPCIONES["modalidad_contratacion_principal"],
        blank=True,
        null=True,
    )

    frecuencia_reuniones_personal_sala = models.CharField(
        max_length=32,
        choices=CAMPOS_OPCIONES["frecuencia_reuniones_personal_sala"],
        blank=True,
        null=True,
    )
    frecuencia_reuniones_personal_no_docente = models.CharField(
        max_length=32,
        choices=CAMPOS_OPCIONES["frecuencia_reuniones_personal_no_docente"],
        blank=True,
        null=True,
    )
    frecuencia_reuniones_todo_personal = models.CharField(
        max_length=32,
        choices=CAMPOS_OPCIONES["frecuencia_reuniones_todo_personal"],
        blank=True,
        null=True,
    )
    instancias_capacitacion_todo_personal_ultimos_3_anios = models.CharField(
        max_length=32,
        choices=CAMPOS_OPCIONES[
            "instancias_capacitacion_todo_personal_ultimos_3_anios"
        ],
        blank=True,
        null=True,
    )
    instancias_capacitacion_personal_sala_ultimos_3_anios = models.CharField(
        max_length=32,
        choices=CAMPOS_OPCIONES[
            "instancias_capacitacion_personal_sala_ultimos_3_anios"
        ],
        blank=True,
        null=True,
    )
    instancias_capacitacion_equipo_tecnico_ultimos_3_anios = models.CharField(
        max_length=32,
        choices=CAMPOS_OPCIONES[
            "instancias_capacitacion_equipo_tecnico_ultimos_3_anios"
        ],
        blank=True,
        null=True,
    )
    instancias_capacitacion_personal_cocina_ultimos_3_anios = models.CharField(
        max_length=32,
        choices=CAMPOS_OPCIONES[
            "instancias_capacitacion_personal_cocina_ultimos_3_anios"
        ],
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["-fecha_relevamiento", "-created_at", "-id"]
        verbose_name = "Formulario CDI"
        verbose_name_plural = "Formularios CDI"

    def __str__(self):
        fecha = (
            self.fecha_relevamiento.strftime("%Y-%m-%d")
            if self.fecha_relevamiento
            else "sin fecha"
        )
        return f"Formulario CDI #{self.pk} - {self.centro} - {fecha}"

    @staticmethod
    def _validate_multi_choice_field(field_name, value):
        allowed = {item[0] for item in CAMPOS_OPCIONES_MULTIPLES[field_name]}
        if value in (None, ""):
            return
        if not isinstance(value, list):
            raise ValueError(field_name)
        invalid_values = [item for item in value if item not in allowed]
        if invalid_values:
            raise ValueError(
                f"{field_name}:{','.join(str(item) for item in invalid_values)}"
            )

    def _collect_multi_choice_errors(self):
        errors = {}
        for field_name in CAMPOS_OPCIONES_MULTIPLES:
            try:
                self._validate_multi_choice_field(field_name, getattr(self, field_name))
            except ValueError:
                errors[field_name] = "Seleccione opciones validas."
        return errors

    def _collect_required_field_errors(self):
        errors = {}
        conditional_required_fields = (
            ("tipo_jornada", "other", "tipo_jornada_otra"),
            ("modalidad_gestion", "otra", "modalidad_gestion_otra"),
            ("modalidad_tenencia", "otra", "modalidad_tenencia_otra"),
        )

        for field_name, expected_value, detail_field in conditional_required_fields:
            if getattr(self, field_name) == expected_value and not getattr(
                self, detail_field
            ):
                errors[detail_field] = "Este campo es obligatorio."

        meals = self.prestaciones_alimentarias or []
        if "otra" in meals and not self.prestaciones_alimentarias_otra:
            errors["prestaciones_alimentarias_otra"] = "Este campo es obligatorio."

        return errors

    def _collect_consistency_errors(self):
        errors = {}
        meals = self.prestaciones_alimentarias or []

        if (
            self.horario_apertura
            and self.horario_cierre
            and self.horario_apertura >= self.horario_cierre
        ):
            errors["horario_cierre"] = (
                "El horario de cierre debe ser posterior al de apertura."
            )

        if "ninguna" in meals and len(meals) > 1:
            errors["prestaciones_alimentarias"] = (
                "No puede combinar 'ninguna' con otras opciones."
            )

        dependent_field_rules = (
            (
                "tiene_espacio_cocina",
                "no",
                "combustible_cocinar",
                "Este campo debe quedar vacio cuando no hay cocina.",
            ),
            (
                "tiene_espacio_exterior",
                "no",
                "tiene_juegos_exteriores",
                "Este campo debe quedar vacio cuando no hay espacio exterior.",
            ),
        )

        for (
            controller_field,
            expected_value,
            dependent_field,
            message,
        ) in dependent_field_rules:
            if getattr(self, controller_field) == expected_value and getattr(
                self, dependent_field
            ):
                errors[dependent_field] = message

        return errors

    def _collect_geography_errors(self):
        errors = {}
        relation_rules = (
            (
                "departamento_cdi",
                "provincia_cdi",
                "provincia_id",
                "El departamento no pertenece a la provincia indicada.",
            ),
            (
                "municipio_cdi",
                "provincia_cdi",
                "provincia_id",
                "El municipio no pertenece a la provincia indicada.",
            ),
            (
                "localidad_cdi",
                "municipio_cdi",
                "municipio_id",
                "La localidad no pertenece al municipio indicado.",
            ),
            (
                "departamento_organizacion",
                "provincia_organizacion",
                "provincia_id",
                "El departamento no pertenece a la provincia indicada.",
            ),
            (
                "municipio_organizacion",
                "provincia_organizacion",
                "provincia_id",
                "El municipio no pertenece a la provincia indicada.",
            ),
            (
                "localidad_organizacion",
                "municipio_organizacion",
                "municipio_id",
                "La localidad no pertenece al municipio indicado.",
            ),
        )

        for child_field, parent_field, relation_attr, message in relation_rules:
            child_value = getattr(self, child_field)
            parent_id = getattr(self, f"{parent_field}_id")
            if (
                child_value
                and parent_id
                and getattr(child_value, relation_attr) != parent_id
            ):
                errors[child_field] = message

        return errors

    def clean(self):
        super().clean()
        errors = {}
        errors.update(self._collect_multi_choice_errors())
        errors.update(self._collect_required_field_errors())
        errors.update(self._collect_consistency_errors())
        errors.update(self._collect_geography_errors())
        self.cuit_organizacion_gestora = (
            normalizar_cuit(self.cuit_organizacion_gestora) or None
        )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if not self.codigo_cdi and self.centro_id:
            self.codigo_cdi = self.centro.codigo_cdi
        super().save(*args, **kwargs)


class FormularioCDIHorarioFuncionamiento(models.Model):
    formulario = models.ForeignKey(
        FormularioCDI,
        on_delete=models.CASCADE,
        related_name="horarios_funcionamiento",
    )
    dia = models.CharField(max_length=16, choices=OPCIONES_DIAS_SEMANA)
    hora_apertura = models.TimeField(blank=True, null=True)
    hora_cierre = models.TimeField(blank=True, null=True)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["formulario", "dia"],
                name="uniq_formulario_cdi_horario_funcionamiento_dia",
            )
        ]
        verbose_name = "Horario de funcionamiento del formulario CDI"
        verbose_name_plural = "Horarios de funcionamiento del formulario CDI"

    def clean(self):
        super().clean()
        errors = {}
        if bool(self.hora_apertura) != bool(self.hora_cierre):
            errors["hora_cierre"] = (
                "Debe completar horario de apertura y cierre para el día."
            )
        if (
            self.hora_apertura
            and self.hora_cierre
            and self.hora_apertura >= self.hora_cierre
        ):
            errors["hora_cierre"] = (
                "El horario de cierre debe ser posterior al de apertura."
            )
        if errors:
            raise ValidationError(errors)
