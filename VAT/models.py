from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.indexes import GinIndex
from django.utils import timezone
from ciudadanos.models import Ciudadano
from core.models import Dia, Localidad, Municipio, Provincia, Sexo
from core.soft_delete import SoftDeleteModelMixin
from organizaciones.models import Organizacion


class Centro(SoftDeleteModelMixin, models.Model):
    nombre = models.CharField(max_length=200)
    referente = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        limit_choices_to={"groups__name": "ReferenteCentroVAT"},
        related_name="vat_centros",
        null=True,
        blank=False,
    )
    codigo = models.CharField(max_length=20, unique=True)
    foto = models.ImageField(upload_to="vat_centros/", blank=True, null=True)
    activo = models.BooleanField(default=True)
    organizacion_asociada = models.ForeignKey(
        Organizacion,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="vat_centros",
    )
    provincia = models.ForeignKey(
        to=Provincia,
        on_delete=models.PROTECT,
        null=True,
        related_name="vat_centros",
    )
    municipio = models.ForeignKey(
        to=Municipio,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vat_centros",
    )
    localidad = models.ForeignKey(
        to=Localidad,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vat_centros",
    )
    calle = models.CharField(max_length=255, blank=True, null=True)
    numero = models.PositiveIntegerField(blank=True, null=True)
    domicilio_actividad = models.CharField(
        max_length=255, verbose_name="Domicilio de actividades"
    )
    telefono = models.CharField(max_length=50, verbose_name="Teléfono")
    celular = models.CharField(max_length=50, verbose_name="Celular")
    correo = models.EmailField(max_length=100, verbose_name="Correo electrónico")
    sitio_web = models.URLField(
        max_length=200, blank=True, null=True, verbose_name="Sitio web"
    )
    link_redes = models.URLField(
        max_length=200, blank=True, null=True, verbose_name="Redes sociales"
    )
    nombre_referente = models.CharField(
        max_length=100, verbose_name="Nombre del responsable"
    )
    apellido_referente = models.CharField(
        max_length=100, verbose_name="Apellido del responsable"
    )
    telefono_referente = models.CharField(
        max_length=50, verbose_name="Teléfono del responsable"
    )
    correo_referente = models.EmailField(
        max_length=100, verbose_name="Correo del responsable"
    )

    def __str__(self):
        return self.nombre

    class Meta:
        indexes = [
            GinIndex(
                fields=["nombre"],
                name="vat_centro_nombre_trgm",
                opclasses=["gin_trgm_ops"],
            ),
        ]


class Categoria(SoftDeleteModelMixin, models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre de la Categoría")

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        indexes = [
            GinIndex(
                fields=["nombre"],
                name="vat_categoria_nombre_trgm",
                opclasses=["gin_trgm_ops"],
            ),
        ]


class Actividad(SoftDeleteModelMixin, models.Model):
    nombre = models.CharField(max_length=200, verbose_name="Nombre de la Actividad")
    categoria = models.ForeignKey(
        Categoria, on_delete=models.CASCADE, verbose_name="Categoría"
    )

    def __str__(self):
        return self.nombre

    class Meta:
        indexes = [
            GinIndex(
                fields=["nombre"],
                name="vat_actividad_nombre_trgm",
                opclasses=["gin_trgm_ops"],
            ),
        ]


class ActividadCentro(SoftDeleteModelMixin, models.Model):
    ESTADO_CHOICES = [
        ("planificada", "Planificada"),
        ("en_curso", "En curso"),
        ("finalizada", "Finalizada"),
    ]
    centro = models.ForeignKey(Centro, on_delete=models.CASCADE, verbose_name="Centro")
    actividad = models.ForeignKey(
        Actividad, on_delete=models.CASCADE, verbose_name="Actividad"
    )
    cantidad_personas = models.PositiveIntegerField(
        verbose_name="Cantidad Estimada de Participantes"
    )
    dias = models.ManyToManyField(
        to=Dia,
        related_name="vat_DiaActividad",
        blank=True,
    )
    sexoact = models.ManyToManyField(
        to=Sexo,
        related_name="vat_sexoactividad",
        verbose_name="Actividad Dirigida a ",
        blank=True,
    )
    horariosdesde = models.TimeField()
    horarioshasta = models.TimeField(null=True, blank=True)
    precio = models.PositiveIntegerField(
        verbose_name="PrecioActividad", null=True, blank=True
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default="planificada",
        verbose_name="Estado",
    )
    fecha_inicio = models.DateField(
        null=True, blank=True, verbose_name="Fecha de inicio"
    )
    fecha_fin = models.DateField(null=True, blank=True, verbose_name="Fecha de fin")

    def __str__(self):
        return f"{self.actividad.nombre} en {self.centro.nombre}"

    class Meta:
        verbose_name = "Actividad del Centro"
        verbose_name_plural = "Actividades por Centro"
        indexes = [
            models.Index(fields=["centro", "estado"], name="vat_actcentro_ce_idx"),
            GinIndex(
                fields=["estado"],
                name="vat_actcentro_estado_trgm",
                opclasses=["gin_trgm_ops"],
            ),
        ]


class ParticipanteActividad(SoftDeleteModelMixin, models.Model):
    ESTADO_INSCRIPCION = [
        ("inscrito", "Inscrito"),
        ("lista_espera", "Lista de Espera"),
        ("dado_baja", "Dado de Baja"),
    ]

    actividad_centro = models.ForeignKey(
        ActividadCentro, on_delete=models.CASCADE, verbose_name="Actividad del Centro"
    )
    ciudadano = models.ForeignKey(
        Ciudadano,
        on_delete=models.CASCADE,
        verbose_name="Ciudadano",
        related_name="vat_participaciones",
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_INSCRIPCION,
        default="inscrito",
        verbose_name="Estado de Inscripción",
    )
    fecha_registro = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de Registro"
    )
    fecha_modificacion = models.DateTimeField(
        auto_now=True, verbose_name="Fecha de Última Modificación"
    )

    def __str__(self):
        return (
            f"{self.ciudadano.apellido}, {self.ciudadano.nombre} - "
            f"{self.actividad_centro} [{self.estado}]"
        )

    class Meta:
        verbose_name = "Participante"
        verbose_name_plural = "Participantes"
        indexes = [
            models.Index(fields=["actividad_centro"], name="vat_part_actcentro_idx"),
            GinIndex(
                fields=["estado"],
                name="vat_part_estado_trgm",
                opclasses=["gin_trgm_ops"],
            ),
        ]
        unique_together = ("actividad_centro", "ciudadano")


class ParticipanteActividadHistorial(models.Model):
    participante = models.ForeignKey(
        ParticipanteActividad, on_delete=models.CASCADE, related_name="historial"
    )
    estado_anterior = models.CharField(
        max_length=20,
        choices=ParticipanteActividad.ESTADO_INSCRIPCION,
        verbose_name="Estado Anterior",
        null=True,
        blank=True,
    )
    estado_nuevo = models.CharField(
        max_length=20,
        choices=ParticipanteActividad.ESTADO_INSCRIPCION,
        verbose_name="Estado Nuevo",
    )
    fecha_cambio = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de Cambio"
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name="Usuario que realizó el cambio",
        related_name="vat_historial_participantes",
    )

    def __str__(self):
        return (
            f"{self.participante}: {self.estado_anterior or '—'} -> {self.estado_nuevo} "
            f"en {self.fecha_cambio.strftime('%Y-%m-%d %H:%M')}"
        )

    class Meta:
        verbose_name = "Historial de Inscripción"
        verbose_name_plural = "Historial de Inscripciones"
        ordering = ["-fecha_cambio"]


class Encuentro(models.Model):
    ESTADO_CHOICES = [
        ("programado", "Programado"),
        ("realizado", "Realizado"),
        ("cancelado", "Cancelado"),
    ]

    actividad_centro = models.ForeignKey(
        ActividadCentro,
        on_delete=models.CASCADE,
        related_name="encuentros",
        verbose_name="Actividad del Centro",
    )
    numero_encuentro = models.PositiveIntegerField(verbose_name="Número de encuentro")
    fecha = models.DateField(verbose_name="Fecha")
    hora_inicio = models.TimeField(verbose_name="Hora de inicio")
    hora_fin = models.TimeField(null=True, blank=True, verbose_name="Hora de fin")
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default="programado",
        verbose_name="Estado",
    )
    observaciones = models.TextField(
        blank=True, null=True, verbose_name="Observaciones"
    )

    def __str__(self):
        return (
            f"Encuentro #{self.numero_encuentro} — "
            f"{self.actividad_centro} ({self.fecha})"
        )

    class Meta:
        verbose_name = "Encuentro"
        verbose_name_plural = "Encuentros"
        ordering = ["fecha", "hora_inicio"]
        unique_together = ("actividad_centro", "fecha")


class Asistencia(models.Model):
    ESTADO_CHOICES = [
        ("presente", "Presente"),
        ("ausente", "Ausente"),
        ("justificado", "Justificado"),
    ]

    encuentro = models.ForeignKey(
        Encuentro,
        on_delete=models.CASCADE,
        related_name="asistencias",
        verbose_name="Encuentro",
    )
    participante = models.ForeignKey(
        ParticipanteActividad,
        on_delete=models.CASCADE,
        related_name="asistencias",
        verbose_name="Participante",
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default="ausente",
        verbose_name="Estado de asistencia",
    )
    hora_registro = models.DateTimeField(
        auto_now_add=True, verbose_name="Hora de registro"
    )
    registrado_por = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="vat_asistencias_registradas",
        verbose_name="Registrado por",
    )
    observaciones = models.TextField(
        blank=True, null=True, verbose_name="Observaciones"
    )

    def __str__(self):
        return (
            f"{self.participante.ciudadano} — "
            f"Encuentro #{self.encuentro.numero_encuentro}: {self.estado}"
        )

    class Meta:
        verbose_name = "Asistencia"
        verbose_name_plural = "Asistencias"
        constraints = [
            models.UniqueConstraint(
                fields=["encuentro", "participante"],
                name="vat_unique_asistencia_encuentro_participante",
            )
        ]


class ModalidadInstitucional(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre de la modalidad")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Modalidad Institucional"
        verbose_name_plural = "Modalidades Institucionales"
        ordering = ["nombre"]


