# pylint: disable=too-many-lines

from datetime import date

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


class OfertaServicio(models.Model):
    codigo = models.CharField(
        max_length=32,
        choices=CAMPOS_OPCIONES["oferta_servicios"],
        unique=True,
    )
    orden = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["orden", "codigo"]
        verbose_name = "Oferta de servicio del CDI"
        verbose_name_plural = "Ofertas de servicio del CDI"

    def __str__(self):
        return self.get_codigo_display()


class CentroDeInfancia(SoftDeleteModelMixin, models.Model):
    nombre = models.CharField(max_length=255, verbose_name="Nombre del CDI")
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
        verbose_name="Denominación del organismo u organización que gestiona el CDI",
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
    oferta_servicios = models.ManyToManyField(
        "OfertaServicio",
        blank=True,
        related_name="centros",
    )
    modalidad_gestion = models.CharField(
        max_length=64,
        choices=CAMPOS_OPCIONES["modalidad_gestion"],
        blank=True,
        null=True,
    )
    modalidad_gestion_otra = models.CharField(max_length=255, blank=True, null=True)
    fecha_inicio = models.DateField(
        blank=True,
        null=True,
        verbose_name="Año de inicio de actividades del CDI",
        validators=[MinValueValidator(date(1990, 1, 1))],
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Centro de Desarrollo Infantil"
        verbose_name_plural = "Centros de Desarrollo Infantil"
        ordering = ["nombre"]

    def __str__(self):
        return str(self.nombre)

    def get_oferta_servicios_display(self):
        return ", ".join(str(oferta) for oferta in self.oferta_servicios.all())

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


TRABAJADOR_SUBCOMPONENTE_CHOICES = [
    ("pfpi", "PFPI"),
    ("egp", "EGP"),
    ("cdi", "CDI"),
    ("uaf", "UAF"),
]

TRABAJADOR_FUNCION_EGP_CHOICES = [
    ("coordinacion_general", "Coordinación General"),
    ("ref_calidad_cdi", "Referente de Calidad de los CDI"),
    ("ref_saf", "Referente del Servicio de Acompañamiento Familiar (SAF)"),
    ("ref_monitoreo", "Referente de Monitoreo"),
    ("ref_capacitacion", "Referente de capacitación"),
    ("apoyo_administrativo", "Apoyo administrativo"),
    ("no_corresponde", "No corresponde"),
]

TRABAJADOR_FUNCION_CDI_CHOICES = [
    ("educador_docente_sala", "Educador o docente de sala"),
    ("auxiliar_sala", "Auxiliar de sala"),
    ("director_coordinador", "Director/a o coordinador/a"),
    ("administrativo", "Administrativo/a"),
    ("equipo_tecnico", "Equipo técnico"),
    ("seguridad", "Seguridad"),
    ("limpieza", "Limpieza"),
    ("cocina", "Cocina"),
    ("mantenimiento", "Mantenimiento"),
    ("otro", "Otro"),
]

TRABAJADOR_SALA_CDI_CHOICES = [
    ("no_corresponde", "No corresponde"),
    ("menores_1_anio", "Menores de 1 año"),
    ("1_anio", "1 año"),
    ("2_anios", "2 años"),
    ("3_anios", "3 años"),
    ("4_anios", "4 años"),
    ("multiedad", "Multiedad"),
]

TRABAJADOR_TIPO_DOCUMENTACION_CHOICES = [
    ("ninguna", "Ninguna documentación"),
    (
        "origen_con_tramite",
        "Sólo tengo mi documento de origen, pero inicié los trámites de radicación",
    ),
    (
        "origen_sin_tramite",
        "Sólo tengo mi documento de origen y no inicié ningún trámite de radicación",
    ),
    ("res_precaria_migraciones", "Certificado de residencia precaria de Migraciones"),
    ("res_precaria_conare", "Certificado de residencia precaria de la CONARE"),
    ("dni_temporario", "DNI temporario"),
    ("res_transitoria", "Residencia transitoria"),
    ("dni_permanente", "DNI permanente"),
    ("naturalizacion", "Naturalización / Ciudadanía argentina"),
]

TRABAJADOR_SEXO_REGISTRAL_CHOICES = [
    ("varon", "Varón"),
    ("mujer", "Mujer"),
    ("indeterminado", "Indeterminado"),
]

TRABAJADOR_NIVEL_EDUCATIVO_CHOICES = [
    ("nunca", "Nunca asistió a un establecimiento educativo"),
    ("inicial_incompleto", "Inicial incompleto"),
    ("inicial_en_curso", "Inicial en curso"),
    ("inicial_completo", "Inicial completo"),
    ("primario_incompleto", "Primario incompleto"),
    ("primario_en_curso", "Primario en curso"),
    ("primario_completo", "Primario completo"),
    ("secundario_incompleto", "Secundario incompleto"),
    ("secundario_en_curso", "Secundario en curso"),
    ("secundario_completo", "Secundario completo"),
    ("superior_incompleto", "Superior incompleto"),
    ("superior_en_curso", "Superior en curso"),
    ("superior_completo", "Superior completo"),
]

TRABAJADOR_FORMACION_ACADEMICA_CHOICES = [
    ("artes_visuales", "Artes visuales"),
    ("atencion_temprana", "Atención temprana"),
    ("auxiliar_jardin_maternal", "Auxiliar de jardín maternal"),
    ("ciencias_educacion", "Ciencias de la educación"),
    ("educacion_fisica", "Educación física"),
    ("estimulacion_temprana", "Estimulación temprana"),
    ("gestion_educativa", "Gestión educativa"),
    ("magisterio", "Magisterio"),
    ("musica", "Música"),
    ("musicoterapia", "Musicoterapia"),
    ("nutricion", "Nutrición"),
    ("profesorado_nivel_inicial", "Profesorado de nivel inicial"),
    ("psicologia", "Psicología"),
    ("psicomotricidad", "Psicomotricidad"),
    ("psicopedagogia", "Psicopedagogía"),
    ("trabajo_social", "Trabajo social"),
    ("otro", "Otro"),
]

TRABAJADOR_CAPACITACIONES_CHOICES = [
    ("cuidados_primera_infancia", "Cuidados en la primera infancia"),
    ("desarrollo_infantil", "Desarrollo infantil"),
    ("discapacidad", "Discapacidad"),
    ("ecologia_medio_ambiente", "Ecología y medio ambiente"),
    ("educacion_comunitaria", "Educación comunitaria"),
    ("educacion_sexual_integral", "Educación Sexual Integral"),
    ("educacion_aprendizaje", "Educación y aprendizaje"),
    ("estimulacion_temprana", "Estimulación temprana"),
    ("herramientas_gestion", "Herramientas de gestión"),
    ("infancia_derechos", "Infancia y derechos"),
    ("interculturalidad", "Interculturalidad"),
    ("juego", "Juego"),
    ("lactancia", "Lactancia"),
    ("limites_crianza", "Límites y crianza"),
    ("nuevas_tecnologias", "Nuevas tecnologías"),
    ("nutricion_infantil", "Nutrición infantil"),
    ("planificacion_pedagogica", "Planificación pedagógica"),
    ("prevencion_violencias", "Prevención contra las violencias"),
    ("primeros_auxilios", "Primeros auxilios"),
    ("seguridad_alimentos", "Seguridad de los alimentos"),
    ("virtualidad_digital", "Virtualidad y contextos digitales"),
    ("otras", "Otras"),
]

TRABAJADOR_ANOS_TRABAJO_CHOICES = [
    ("1", "1"),
    ("2", "2"),
    ("3", "3"),
    ("4", "4"),
    ("5", "5"),
    ("6", "6"),
    ("7", "7"),
    ("8", "8"),
    ("9", "9"),
    ("10_o_mas", "10 o más"),
]

TRABAJADOR_TIPO_CONTRATACION_CHOICES = [
    ("relacion_dependencia", "Relación de dependencia"),
    ("contrato_anual", "Contratación renovable anualmente"),
    ("contrato_temporal", "Contratación temporal"),
    ("pasantia", "Pasantía"),
    ("voluntariado", "Voluntariado"),
    ("inclusion_social", "Programa de inclusión social"),
]

TRABAJADOR_TIPO_BARRIO_CHOICES = [
    ("urbano", "Urbano"),
    ("rural", "Rural"),
    ("villa", "Villa"),
    ("asentamiento", "Asentamiento"),
    ("urbanizacion_informal", "Urbanización informal"),
]

TRABAJADOR_GRUPO_PERTENENCIA_CHOICES = [
    ("africano", "Africano/a/e y/o afrodescendiente"),
    ("indigena", "Indígena, descendiente de pueblos originarios o mestizo/a/e"),
    ("asiatico", "Asiático/a/e y/o descendiente de asiático/a/e"),
    ("ninguno", "Ninguno de los anteriores"),
]

TRABAJADOR_PUEBLO_ORIGINARIO_CHOICES = [
    ("atacama", "Atacama"),
    ("ava_guarani", "Ava Guaraní"),
    ("chane", "Chané"),
    ("chane_guarani", "Chané - Guaraní"),
    ("charrua", "Charrúa"),
    ("chicha", "Chicha"),
    ("chorote", "Chorote"),
    ("chorote_wichi", "Chorote - Wichí"),
    ("chulup_nivcale", "Chulupí (Nivaclé)"),
    ("chulup_nivcale_omaguaca", "Chulupí (Nivaclé) - Omaguaca"),
    ("comechingon", "Comechingón"),
    ("comechingon_sanaviron", "Comechingón - Sanavirón"),
    ("corundi", "Corundí"),
    ("diaguita", "Diaguita"),
    ("diaguita_cacano", "Diaguita (Cacano)"),
    ("diaguita_calchaqui", "Diaguita Calchaquí"),
    ("diaguita_calchaqui_wichi_lule", "Diaguita Calchaquí - Wichí - Lule"),
    ("fiscara", "Fiscara"),
    ("guarani", "Guaraní"),
    ("guarani_chane", "Guaraní - Chané"),
    ("guaycuru", "Guaycurú"),
    ("huarpe", "Huarpe"),
    ("iogys", "Iogys"),
    ("kolla", "Kolla"),
    ("kolla_guarani", "Kolla - Guaraní"),
    ("kolla_wichi_guarani", "Kolla - Wichí - Guaraní"),
    ("kolla_atacameno", "Kolla Atacameño"),
    ("lule", "Lule"),
    ("lule_vilela", "Lule Vilela"),
    ("mapuche", "Mapuche"),
    ("mapuche_pehuenche", "Mapuche Pehuenche"),
    ("mapuche_tehuelche", "Mapuche Tehuelche"),
    ("mbya_guarani", "Mbya Guaraní"),
    ("moqoit_mocovi", "Moqoit (Mocoví)"),
    ("moqoit_mocovi_qom_toba", "Moqoit (Mocoví) - Qom (Toba)"),
    ("ocloya", "Ocloya"),
    ("omaguaca", "Omaguaca"),
    ("pilaga", "Pilagá"),
    ("qom_toba", "Qom (Toba)"),
    ("qom_toba_moqoit_mocovi", "Qom (Toba) - Moqoit (Mocoví)"),
    ("qom_toba_pilaga_wichi", "Qom (Toba) - Pilagá - Wichí"),
    ("quechua", "Quechua"),
    ("ranquel", "Ranquel"),
    ("ranquel_mapuche", "Ranquel - Mapuche"),
    ("sanaviron", "Sanavirón"),
    ("selknam_onas", "Selk'Nam (Onas)"),
    ("sin_dato", "Sin dato"),
    ("tapiete", "Tapiete"),
    ("tastil", "Tastil"),
    ("tehuelche", "Tehuelche"),
    ("tehuelche_mapuche", "Tehuelche Mapuche"),
    ("tilian", "Tilián"),
    ("toara", "Toara"),
    ("tonokote", "Tonokoté"),
    ("tupi_guarani", "Tupí Guaraní"),
    ("vilela", "Vilela"),
    ("wichi", "Wichí"),
    ("wichi_chiriguano", "Wichí - Chiriguano"),
    ("wichi_chorote", "Wichí - Chorote"),
    ("wichi_guarani", "Wichí - Guaraní"),
    ("wichi_qom_toba", "Wichí - Qom (Toba)"),
    ("yagan", "Yagán"),
]

TRABAJADOR_LENGUAJES_CHOICES = [
    ("espanol_castellano", "Español / Castellano"),
    ("ava_guarani_chiriguano", "Ava Guaraní / Chiriguano"),
    ("aymara", "Aymara"),
    ("chana", "Chaná"),
    ("chane", "Chané"),
    ("chorote", "Chorote"),
    ("guarani", "Guaraní"),
    ("gunun_a_iajuch", "Günün a iajüch"),
    ("kakan", "Kakan"),
    ("lule", "Lule"),
    ("mapuche_mapuzungun_chezungun", "Mapuche / Mapuzungun / Chezungun"),
    ("mbya_guarani", "Mbya Guaraní"),
    ("mocovi_moqoit_amacowit", "Mocoví / Moqoit / Amacowit"),
    ("nivacle_chulupih", "Nivaclé / Chulupíh"),
    ("pilaga", "Pilagá"),
    ("qom_toba_qom_laqtac", "Qom / Toba - Qom / Qom la'qtac"),
    ("quechua_runa_simi", "Quechua / Runa simi"),
    ("quichua", "Quichua"),
    ("rankulche", "Rankulche"),
    ("sellknam", "Sellk'nam"),
    ("tapiete", "Tapiete"),
    ("vilela", "Vilela"),
    ("wichi", "Wichí"),
    ("yagan", "Yagán"),
    ("lsa", "Lengua de Señas de Argentina (LSA)"),
    ("otro", "Otro"),
]

TRABAJADOR_TIPO_DISCAPACIDAD_CHOICES = [
    ("motora", "Motora"),
    ("visual", "Visual"),
    ("auditiva", "Auditiva"),
    ("intelectual", "Intelectual"),
    ("psicosocial", "Psicosocial"),
    ("visceral", "Visceral"),
    ("no_sabe", "No sabe"),
]

_TRABAJADOR_NIVELES_HABILITAN_FORMACION = frozenset(
    {
        "secundario_completo",
        "superior_incompleto",
        "superior_en_curso",
        "superior_completo",
    }
)

# ─────────────────────────────────────────────────────────────────────────────
# Constantes de choices para NominaCentroInfancia (Destinatarios CDI)
# ─────────────────────────────────────────────────────────────────────────────

NOMINA_TIPO_REGISTRO_CHOICES = [
    ("alta", "Alta"),
    ("seguimiento", "Seguimiento"),
    ("baja", "Baja"),
]

NOMINA_RELACION_RESPONSABLE_CHOICES = [
    ("madre", "Madre"),
    ("padre", "Padre"),
    ("abuela", "Abuela"),
    ("abuelo", "Abuelo"),
    ("tutora", "Tutora"),
    ("tutor", "Tutor"),
    ("curadora", "Curadora"),
    ("curador", "Curador"),
    ("referente_afectivo", "Referente afectivo/a"),
    ("acompanante", "Acompañante"),
    ("otro", "Otro"),
]

NOMINA_SALA_CHOICES = [
    ("menos_1_anio", "Menos de un año"),
    ("1_anio", "1 año"),
    ("2_anios", "2 años"),
    ("3_anios", "3 años"),
    ("4_anios", "4 años"),
    ("multiedad", "Multiedad"),
]

NOMINA_EDAD_UNIDAD_CHOICES = [
    ("meses", "Meses"),
    ("anios", "Años"),
]

NOMINA_COBERTURA_SALUD_CHOICES = [
    ("publica_exclusiva", "Pública exclusiva"),
    ("obra_social", "Obra social"),
    ("prepaga", "Prepaga / medicina privada"),
    ("no_corresponde", "No corresponde"),
]

NOMINA_CONTROLES_SANITARIOS_CHOICES = [
    ("0", "0 controles"),
    ("1", "1 control"),
    ("2", "2 controles"),
    ("3", "3 controles"),
    ("4", "4 controles"),
    ("5", "5 controles"),
    ("6", "6 controles"),
    ("7", "7 controles"),
]

NOMINA_LACTANCIA_CHOICES = [
    ("exclusiva", "Exclusiva"),
    ("complementaria", "Complementaria"),
    ("continuada", "Continuada"),
    ("no_lactante", "No es lactante"),
]

NOMINA_DX_PESO_CHOICES = [
    ("pn", "PN (Peso normal)"),
    ("s", "S (Sobrepeso)"),
    ("o", "O (Obesidad)"),
    ("dc", "DC (Desnutrición crónica)"),
    ("dg", "DG (Desnutrición global)"),
    ("dl", "DL (Desnutrición leve)"),
    ("dm", "DM (Desnutrición moderada)"),
]

NOMINA_DX_TALLA_CHOICES = [
    ("tn", "TN (Talla normal)"),
    ("bt", "BT (Baja talla)"),
    ("btg", "BTG (Baja talla grave)"),
    ("dt", "DT (Desarrollo talla)"),
    ("e", "E (Elevado)"),
]

NOMINA_ORIENTACION_MSAL_CHOICES = [
    ("a", "A"),
    ("bp_bt", "BP-BT"),
    ("e_orientacion", "E"),
    ("o_orientacion", "O"),
    ("rbp", "RBP"),
    ("s_orientacion", "S"),
]

NOMINA_ALERGIA_CHOICES = [
    ("leche_vaca", "Leche de vaca"),
    ("tacc", "Trigo-Avena-Cebada-Centeno (TACC)"),
    ("huevo", "Huevo"),
    ("soja", "Soja"),
    ("pescado", "Pescado"),
    ("frutos_secos", "Frutos secos"),
]

NOMINA_DOSIS_VACUNA_CHOICES = [
    ("0_dosis", "0 dosis"),
    ("1_dosis", "1 dosis"),
    ("2_dosis", "2 dosis"),
    ("3_dosis", "3 dosis"),
    ("sin_dato", "Sin dato"),
]


NOMINA_VACUNAS = [
    ("bcg", "BCG"),
    ("neumococo", "Neumococo Conjugada"),
    ("quintuple", "Quíntuple o Pentavalente"),
    ("polio", "Polio (IPV o SALK)"),
    ("rotavirus", "Rotavirus"),
    ("meningococo", "Meningococo ACYW"),
    ("antigripal", "Antigripal"),
    ("hepatitis_a", "Hepatitis A"),
    ("triple_viral", "Triple Viral"),
    ("varicela", "Varicela"),
    ("triple_bacteriana_celular", "Triple Bacteriana Celular"),
    ("triple_bacteriana_acelular", "Triple Bacteriana Acelular"),
    ("sincicial_respiratorio", "Virus Sincicial Respiratorio"),
    ("fiebre_amarilla", "Fiebre Amarilla"),
]


def _trabajador_etiquetas(values, choices):
    """Traduce claves de un multiselect (JSONField) a sus etiquetas legibles."""
    etiquetas = dict(choices)
    return [etiquetas.get(valor, valor) for valor in (values or [])]


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
    rol = models.CharField(max_length=20, choices=Rol.choices, blank=True)

    # Sección Institución
    fecha_carga = models.DateField(blank=True, null=True, verbose_name="Fecha de carga")

    # Sección Fuerza de trabajo
    subcomponente = models.CharField(
        max_length=8,
        choices=TRABAJADOR_SUBCOMPONENTE_CHOICES,
        blank=True,
        null=True,
        verbose_name="Subcomponente",
    )
    funcion_egp = models.CharField(
        max_length=32,
        choices=TRABAJADOR_FUNCION_EGP_CHOICES,
        blank=True,
        null=True,
        verbose_name="Función (EGP)",
    )
    funcion_cdi = models.CharField(
        max_length=32,
        choices=TRABAJADOR_FUNCION_CDI_CHOICES,
        blank=True,
        null=True,
        verbose_name="Función (CDI)",
    )
    sala_cdi = models.CharField(
        max_length=16,
        choices=TRABAJADOR_SALA_CDI_CHOICES,
        blank=True,
        null=True,
        verbose_name="Sala (CDI)",
    )
    fecha_nacimiento = models.DateField(
        blank=True, null=True, verbose_name="Fecha de nacimiento"
    )
    dni = models.PositiveBigIntegerField(
        blank=True, null=True, verbose_name="Número de documento"
    )
    tipo_documentacion = models.CharField(
        max_length=40,
        choices=TRABAJADOR_TIPO_DOCUMENTACION_CHOICES,
        blank=True,
        null=True,
        verbose_name="¿Con qué tipo de documentación cuenta en Argentina?",
    )
    sexo_registral = models.CharField(
        max_length=16,
        choices=TRABAJADOR_SEXO_REGISTRAL_CHOICES,
        blank=True,
        null=True,
        verbose_name="Sexo registral",
    )
    cuit = models.CharField(
        max_length=11,
        blank=True,
        null=True,
        validators=[CUIT_VALIDATOR],
        verbose_name="CUIT",
    )
    pais_nacimiento = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        verbose_name="¿Cuál es su país de nacimiento?",
    )
    nacionalidad_trabajador = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        verbose_name="¿Cuál es su nacionalidad?",
    )

    # Sección Formación y experiencia
    nivel_educativo = models.CharField(
        max_length=32,
        choices=TRABAJADOR_NIVEL_EDUCATIVO_CHOICES,
        blank=True,
        null=True,
        verbose_name="Nivel educativo",
    )
    formacion_academica = models.CharField(
        max_length=32,
        choices=TRABAJADOR_FORMACION_ACADEMICA_CHOICES,
        blank=True,
        null=True,
        verbose_name="Formación académica",
    )
    capacitaciones_certificadas = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Capacitaciones certificadas (últimos tres años)",
    )
    anos_trabajo_primera_infancia = models.CharField(
        max_length=16,
        choices=TRABAJADOR_ANOS_TRABAJO_CHOICES,
        blank=True,
        null=True,
        verbose_name="Años de trabajo en primera infancia",
    )

    # Sección Contratación
    tipo_contratacion = models.CharField(
        max_length=32,
        choices=TRABAJADOR_TIPO_CONTRATACION_CHOICES,
        blank=True,
        null=True,
        verbose_name="Tipo de contratación",
    )
    carga_horaria_semanal = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(60)],
        verbose_name="Carga horaria semanal (CDI)",
    )

    # Sección Contacto
    email = models.EmailField(blank=True, null=True, verbose_name="Correo electrónico")
    calle_contacto = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Calle y numeración"
    )
    unidad_funcional = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        verbose_name="Unidad funcional (piso, departamento)",
    )
    tipo_barrio = models.CharField(
        max_length=24,
        choices=TRABAJADOR_TIPO_BARRIO_CHOICES,
        blank=True,
        null=True,
        verbose_name="Tipo de barrio",
    )
    provincia_contacto = models.ForeignKey(
        "core.Provincia",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="+",
        verbose_name="Jurisdicción",
    )
    municipio_contacto = models.ForeignKey(
        "core.Municipio",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="+",
        verbose_name="Municipio",
    )
    localidad_contacto = models.ForeignKey(
        "core.Localidad",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="+",
        verbose_name="Localidad",
    )

    # Sección Cultura e identidad
    grupo_pertenencia = models.JSONField(
        default=list,
        blank=True,
        verbose_name="¿Desciende, tiene antepasados o pertenece a alguno de los siguientes grupos?",
    )
    pueblo_originario = models.CharField(
        max_length=40,
        choices=TRABAJADOR_PUEBLO_ORIGINARIO_CHOICES,
        blank=True,
        null=True,
        verbose_name="Pueblo originario al que pertenece",
    )
    lenguajes = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Lenguajes que utiliza",
    )
    es_interprete = models.CharField(
        max_length=16,
        choices=[("si", "Sí"), ("no", "No"), ("no_corresponde", "No corresponde")],
        blank=True,
        null=True,
        verbose_name="¿Es intérprete?",
    )

    # Sección Discapacidad
    tiene_discapacidad = models.CharField(
        max_length=8,
        choices=[("si", "Sí"), ("no", "No"), ("no_sabe", "No sabe")],
        blank=True,
        null=True,
        verbose_name="¿Tiene alguna discapacidad y/o requiere apoyos específicos?",
    )
    tipo_discapacidad = models.JSONField(
        default=list,
        blank=True,
        verbose_name="¿Qué tipo de discapacidad presenta?",
    )
    recibe_apoyo_discapacidad = models.CharField(
        max_length=8,
        choices=[("si", "Sí"), ("no", "No"), ("no_sabe", "No sabe")],
        blank=True,
        null=True,
        verbose_name="¿Recibe actualmente algún tipo de apoyo, tratamiento o acompañamiento?",
    )
    tiene_cud = models.CharField(
        max_length=4,
        choices=[("si", "Sí"), ("no", "No")],
        blank=True,
        null=True,
        verbose_name="¿Tiene CUD?",
    )
    numero_cud = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name="Número de CUD (ANSES)",
    )

    class Meta:
        verbose_name = "Trabajador"
        verbose_name_plural = "Trabajadores"
        ordering = ["apellido", "nombre"]

    def __str__(self):
        return f"{self.apellido}, {self.nombre}"

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

    @property
    def capacitaciones_certificadas_display(self):
        return _trabajador_etiquetas(
            self.capacitaciones_certificadas, TRABAJADOR_CAPACITACIONES_CHOICES
        )

    @property
    def grupo_pertenencia_display(self):
        return _trabajador_etiquetas(
            self.grupo_pertenencia, TRABAJADOR_GRUPO_PERTENENCIA_CHOICES
        )

    @property
    def lenguajes_display(self):
        return _trabajador_etiquetas(self.lenguajes, TRABAJADOR_LENGUAJES_CHOICES)

    @property
    def tipo_discapacidad_display(self):
        return _trabajador_etiquetas(
            self.tipo_discapacidad, TRABAJADOR_TIPO_DISCAPACIDAD_CHOICES
        )

    @staticmethod
    def _validar_multiselect(field_name, value, choices):
        allowed = {item[0] for item in choices}
        if value in (None, ""):
            return
        if not isinstance(value, list):
            raise ValidationError({field_name: "Seleccione opciones válidas."})
        invalid = [v for v in value if v not in allowed]
        if invalid:
            raise ValidationError({field_name: "Seleccione opciones válidas."})

    def clean(self):
        super().clean()
        errors = {}

        # Limpiar función condicional por subcomponente
        if self.subcomponente != "egp":
            self.funcion_egp = None
        if self.subcomponente != "cdi":
            self.funcion_cdi = None

        # Limpiar formacion_academica si nivel no la habilita
        if self.nivel_educativo not in _TRABAJADOR_NIVELES_HABILITAN_FORMACION:
            self.formacion_academica = None

        # Limpiar pueblo_originario si no aplica
        if "indigena" not in (self.grupo_pertenencia or []):
            self.pueblo_originario = None

        # Limpiar campos condicionales de discapacidad
        if self.tiene_discapacidad != "si":
            self.tipo_discapacidad = []
            self.recibe_apoyo_discapacidad = None
        if self.tiene_cud != "si":
            self.numero_cud = None

        # Normalizar CUIT
        self.cuit = normalizar_cuit(self.cuit) or None

        # Validar multiselect JSONFields
        multiselect_fields = [
            ("capacitaciones_certificadas", TRABAJADOR_CAPACITACIONES_CHOICES),
            ("grupo_pertenencia", TRABAJADOR_GRUPO_PERTENENCIA_CHOICES),
            ("lenguajes", TRABAJADOR_LENGUAJES_CHOICES),
            ("tipo_discapacidad", TRABAJADOR_TIPO_DISCAPACIDAD_CHOICES),
        ]
        for fname, choices in multiselect_fields:
            try:
                self._validar_multiselect(fname, getattr(self, fname), choices)
            except ValidationError as exc:
                errors.update(exc.message_dict)

        # Validar geografía de contacto
        geo_rules = [
            (
                "municipio_contacto",
                "provincia_contacto",
                "provincia_id",
                "El municipio no pertenece a la provincia indicada.",
            ),
            (
                "localidad_contacto",
                "municipio_contacto",
                "municipio_id",
                "La localidad no pertenece al municipio indicado.",
            ),
        ]
        for child_field, parent_field, relation_attr, msg in geo_rules:
            child = getattr(self, child_field)
            parent_id = getattr(self, f"{parent_field}_id")
            if child and parent_id and getattr(child, relation_attr) != parent_id:
                errors[child_field] = msg

        if errors:
            raise ValidationError(errors)


class NominaPais(models.Model):
    nombre = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "País"
        verbose_name_plural = "Países"

    def __str__(self):
        return self.nombre


class NominaNacionalidad(models.Model):
    nombre = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Nacionalidad"
        verbose_name_plural = "Nacionalidades"

    def __str__(self):
        return self.nombre


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

    # ── Sección 3: Registro ──────────────────────────────────────────────────
    tipo_registro = models.CharField(
        max_length=16,
        choices=NOMINA_TIPO_REGISTRO_CHOICES,
        blank=True,
        null=True,
    )
    fecha_registro = models.DateField(blank=True, null=True)

    # ── Sección 4: Trabajador que registra ──────────────────────────────────
    trabajador_registra = models.ForeignKey(
        "Trabajador",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="nominas_registradas",
    )

    # ── Sección 5: Responsable 1 (campos extendidos) ─────────────────────────
    responsable_legal_1_relacion = models.CharField(
        max_length=32,
        choices=NOMINA_RELACION_RESPONSABLE_CHOICES,
        blank=True,
        null=True,
    )
    responsable_legal_1_fecha_nacimiento = models.DateField(blank=True, null=True)
    responsable_legal_1_tipo_documentacion = models.CharField(
        max_length=64,
        choices=TRABAJADOR_TIPO_DOCUMENTACION_CHOICES,
        blank=True,
        null=True,
    )
    responsable_legal_1_cuit = models.CharField(max_length=20, blank=True, null=True)
    responsable_legal_1_pais_nacimiento = models.CharField(
        max_length=100, blank=True, null=True
    )
    responsable_legal_1_nacionalidad = models.CharField(
        max_length=100, blank=True, null=True
    )
    responsable_legal_1_sexo_registral = models.CharField(
        max_length=16,
        choices=TRABAJADOR_SEXO_REGISTRAL_CHOICES,
        blank=True,
        null=True,
    )
    responsable_legal_1_nivel_educativo = models.CharField(
        max_length=32,
        choices=TRABAJADOR_NIVEL_EDUCATIVO_CHOICES,
        blank=True,
        null=True,
    )
    responsable_legal_1_consentimiento = models.CharField(
        max_length=4,
        choices=[("si", "Sí"), ("no", "No")],
        blank=True,
        null=True,
    )

    # ── Sección 6: Responsable 2 (campos extendidos) ─────────────────────────
    responsable_legal_2_relacion = models.CharField(
        max_length=32,
        choices=NOMINA_RELACION_RESPONSABLE_CHOICES,
        blank=True,
        null=True,
    )
    responsable_legal_2_fecha_nacimiento = models.DateField(blank=True, null=True)
    responsable_legal_2_tipo_documentacion = models.CharField(
        max_length=64,
        choices=TRABAJADOR_TIPO_DOCUMENTACION_CHOICES,
        blank=True,
        null=True,
    )
    responsable_legal_2_cuit = models.CharField(max_length=20, blank=True, null=True)
    responsable_legal_2_pais_nacimiento = models.CharField(
        max_length=100, blank=True, null=True
    )
    responsable_legal_2_nacionalidad = models.CharField(
        max_length=100, blank=True, null=True
    )
    responsable_legal_2_sexo_registral = models.CharField(
        max_length=16,
        choices=TRABAJADOR_SEXO_REGISTRAL_CHOICES,
        blank=True,
        null=True,
    )
    responsable_legal_2_nivel_educativo = models.CharField(
        max_length=32,
        choices=TRABAJADOR_NIVEL_EDUCATIVO_CHOICES,
        blank=True,
        null=True,
    )
    responsable_legal_2_consentimiento = models.CharField(
        max_length=4,
        choices=[("si", "Sí"), ("no", "No")],
        blank=True,
        null=True,
    )

    # ── Sección 7: Datos del niño/a (campos extendidos) ──────────────────────
    tipo_documentacion = models.CharField(
        max_length=64,
        choices=TRABAJADOR_TIPO_DOCUMENTACION_CHOICES,
        blank=True,
        null=True,
    )
    cuit_nino = models.CharField(max_length=20, blank=True, null=True)
    pais_nacimiento = models.CharField(max_length=100, blank=True, null=True)
    edad_unidad = models.CharField(
        max_length=8,
        choices=NOMINA_EDAD_UNIDAD_CHOICES,
        blank=True,
        null=True,
    )

    # ── Sección 8: Domicilio (campos extendidos) ──────────────────────────────
    tipo_barrio = models.CharField(
        max_length=32,
        choices=TRABAJADOR_TIPO_BARRIO_CHOICES,
        blank=True,
        null=True,
    )
    convivientes = models.PositiveSmallIntegerField(blank=True, null=True)

    # ── Sección 9: Cultura e identidad ────────────────────────────────────────
    grupo_pertenencia = models.JSONField(default=list, blank=True)
    lenguajes = models.JSONField(default=list, blank=True)
    necesito_interprete = models.CharField(
        max_length=4,
        choices=[("si", "Sí"), ("no", "No")],
        blank=True,
        null=True,
    )

    # ── Sección 10: Discapacidad (campos extendidos) ──────────────────────────
    tipo_discapacidad = models.JSONField(default=list, blank=True)
    numero_cud = models.CharField(max_length=20, blank=True, null=True)

    # ── Sección 11: Salud ─────────────────────────────────────────────────────
    cobertura_salud = models.CharField(
        max_length=32,
        choices=NOMINA_COBERTURA_SALUD_CHOICES,
        blank=True,
        null=True,
    )
    controles_sanitarios_ultimo_anio = models.CharField(
        max_length=4,
        choices=NOMINA_CONTROLES_SANITARIOS_CHOICES,
        blank=True,
        null=True,
    )

    # ── Sección 12: Antropometría ─────────────────────────────────────────────
    longitud_acostado = models.DecimalField(
        max_digits=5, decimal_places=1, blank=True, null=True
    )
    perimetro_cefalico = models.DecimalField(
        max_digits=5, decimal_places=1, blank=True, null=True
    )

    # ── Sección 13: Nutrición ─────────────────────────────────────────────────
    lactancia = models.CharField(
        max_length=16,
        choices=NOMINA_LACTANCIA_CHOICES,
        blank=True,
        null=True,
    )
    diagnostico_peso = models.CharField(
        max_length=16,
        choices=NOMINA_DX_PESO_CHOICES,
        blank=True,
        null=True,
    )
    diagnostico_talla = models.CharField(
        max_length=16,
        choices=NOMINA_DX_TALLA_CHOICES,
        blank=True,
        null=True,
    )
    orientacion_msal = models.CharField(
        max_length=16,
        choices=NOMINA_ORIENTACION_MSAL_CHOICES,
        blank=True,
        null=True,
    )
    alergias_alimentarias = models.JSONField(default=list, blank=True)

    # ── Sección 14: ANSES ─────────────────────────────────────────────────────
    anses_auh = models.CharField(
        max_length=4,
        choices=[("si", "Sí"), ("no", "No")],
        blank=True,
        null=True,
    )
    anses_aue = models.CharField(
        max_length=4,
        choices=[("si", "Sí"), ("no", "No")],
        blank=True,
        null=True,
    )
    anses_acsi = models.CharField(
        max_length=4,
        choices=[("si", "Sí"), ("no", "No")],
        blank=True,
        null=True,
    )
    anses_acn = models.CharField(
        max_length=4,
        choices=[("si", "Sí"), ("no", "No")],
        blank=True,
        null=True,
    )

    # ── Sección 15: Vacunación NOMIVAC ────────────────────────────────────────
    vacunacion_nomivac = models.JSONField(default=dict, blank=True)

    # ── Sección 16: Desarrollo Infantil Temprano ──────────────────────────────
    recibe_apoyo_desarrollo = models.CharField(
        max_length=4,
        choices=[("si", "Sí"), ("no", "No")],
        blank=True,
        null=True,
    )

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

    @staticmethod
    def _validar_multiselect(field_name, value, choices):
        allowed = {item[0] for item in choices}
        if value in (None, ""):
            return
        if not isinstance(value, list):
            raise ValidationError({field_name: "Seleccione opciones válidas."})
        invalid = [v for v in value if v not in allowed]
        if invalid:
            raise ValidationError({field_name: "Seleccione opciones válidas."})

    def clean(self):
        super().clean()
        errors = {}

        # ── Pueblo originario (campo legacy) ────────────────────────────────
        if self.pertenece_pueblo_originario != self.RespuestaSiNoNsNc.SI:
            self.pueblo_originario_cual = None

        # ── Pueblo originario via nuevo grupo_pertenencia ────────────────────
        if "indigena" not in (self.grupo_pertenencia or []):
            self.pueblo_originario_cual = None

        # ── Discapacidad ─────────────────────────────────────────────────────
        if self.tiene_discapacidad != self.RespuestaSiNoNsNc.SI:
            self.discapacidad_tipo = None
            self.recibe_apoyo_discapacidad = None
            self.tipo_discapacidad = []
            self.numero_cud = None
        if not self.posee_cud:
            self.numero_cud = None

        # ── Validar multiselect JSONFields ───────────────────────────────────
        multiselect_fields = [
            ("grupo_pertenencia", TRABAJADOR_GRUPO_PERTENENCIA_CHOICES),
            ("lenguajes", TRABAJADOR_LENGUAJES_CHOICES),
            ("tipo_discapacidad", TRABAJADOR_TIPO_DISCAPACIDAD_CHOICES),
            ("alergias_alimentarias", NOMINA_ALERGIA_CHOICES),
        ]
        for fname, choices in multiselect_fields:
            try:
                self._validar_multiselect(fname, getattr(self, fname), choices)
            except ValidationError as exc:
                errors.update(exc.message_dict)

        # ── Validar geografía domicilio ───────────────────────────────────────
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

    @property
    def grupo_pertenencia_display(self):
        return _trabajador_etiquetas(self.grupo_pertenencia, TRABAJADOR_GRUPO_PERTENENCIA_CHOICES)

    @property
    def lenguajes_display(self):
        return _trabajador_etiquetas(self.lenguajes, TRABAJADOR_LENGUAJES_CHOICES)

    @property
    def tipo_discapacidad_display(self):
        return _trabajador_etiquetas(self.tipo_discapacidad, TRABAJADOR_TIPO_DISCAPACIDAD_CHOICES)

    @property
    def alergias_alimentarias_display(self):
        return _trabajador_etiquetas(self.alergias_alimentarias, NOMINA_ALERGIA_CHOICES)


class NominaCentroInfanciaDerivacion(models.Model):
    nomina_origen = models.ForeignKey(
        NominaCentroInfancia,
        on_delete=models.PROTECT,
        related_name="derivaciones_origen",
    )
    nomina_destino = models.ForeignKey(
        NominaCentroInfancia,
        on_delete=models.PROTECT,
        related_name="derivaciones_destino",
    )
    centro_origen = models.ForeignKey(
        CentroDeInfancia,
        on_delete=models.PROTECT,
        related_name="+",
    )
    centro_destino = models.ForeignKey(
        CentroDeInfancia,
        on_delete=models.PROTECT,
        related_name="+",
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    fecha = models.DateTimeField(auto_now_add=True)
    motivo = models.TextField(blank=True)

    class Meta:
        verbose_name = "Derivación de nómina CDI"
        verbose_name_plural = "Derivaciones de nómina CDI"
        ordering = ["-fecha"]


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


class AccesoCDI(models.Model):
    """Vínculo entre un usuario y un CDI que gestiona.

    Replica el patrón de ``users.AccesoComedorPWA`` para el dominio CDI: un
    usuario provincial genera usuarios "CDI - Referente centro" asociados a un
    centro puntual (relación 1..N, máximo definido en la capa de servicio).
    El rol/permisos los aporta el grupo, no este modelo.
    """

    LIMITE_USUARIOS_POR_CENTRO = 10

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="accesos_cdi",
    )
    centro = models.ForeignKey(
        CentroDeInfancia,
        on_delete=models.CASCADE,
        related_name="accesos_usuarios",
    )
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accesos_cdi_creados",
    )
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_baja = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Acceso de usuario a CDI"
        verbose_name_plural = "Accesos de usuarios a CDI"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "centro"],
                name="uniq_acceso_cdi_user_centro",
            )
        ]
        indexes = [
            models.Index(fields=["centro", "activo"]),
            models.Index(fields=["user", "activo"]),
            models.Index(fields=["creado_por", "activo"]),
        ]

    def __str__(self):
        estado = "activo" if self.activo else "baja"
        return f"{self.user_id} - {self.centro_id} ({estado})"
