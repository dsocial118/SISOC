from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q, UniqueConstraint
from ciudadanos.models import Ciudadano
from core.models import Dia, Localidad, Municipio, Provincia, Sexo
from organizaciones.models import Organizacion


class Centro(models.Model):
    TIPO_CHOICES = [
        ("faro", "faro"),
        ("adherido", "Adherido"),
    ]
    nombre = models.CharField(max_length=200)
    referente = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        limit_choices_to={"groups__name": "ReferenteCentro"},
        related_name="centros",
        null=True,
        blank=False,
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    faro_asociado = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={"tipo": "faro", "activo": True},
    )
    codigo = models.CharField(max_length=20, unique=True)
    foto = models.ImageField(upload_to="centros/", blank=True, null=True)
    activo = models.BooleanField(default=True)
    organizacion_asociada = models.ForeignKey(
        Organizacion,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    # datos sede
    provincia = models.ForeignKey(to=Provincia, on_delete=models.PROTECT, null=True)
    municipio = models.ForeignKey(
        to=Municipio, on_delete=models.SET_NULL, null=True, blank=True
    )
    localidad = models.ForeignKey(
        to=Localidad, on_delete=models.SET_NULL, null=True, blank=True
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
    # referente
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
        return str(self.nombre)


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre de la Categoría")

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"


class Actividad(models.Model):
    nombre = models.CharField(max_length=200, verbose_name="Nombre de la Actividad")
    categoria = models.ForeignKey(
        Categoria, on_delete=models.CASCADE, verbose_name="Categoría"
    )

    def __str__(self):
        return str(self.nombre)


class ActividadCentro(models.Model):
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
    # Campos heredados (temporales):
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

    def __str__(self):
        return f"{self.actividad.nombre} en {self.centro.nombre}"


class HorarioActividadCentro(models.Model):
    """
    Franjas horarias para cada día de una ActividadCentro.
    """
    actividad_centro = models.ForeignKey(
        ActividadCentro,
        on_delete=models.CASCADE,
        related_name="horarios",
        verbose_name="Actividad Centro"
    )
    dia = models.ForeignKey(
        Dia,
        on_delete=models.CASCADE,
        verbose_name="Día"
    )
    hora_inicio = models.TimeField(verbose_name="Hora Inicio")
    hora_fin = models.TimeField(verbose_name="Hora Fin")

    class Meta:
        ordering = ["actividad_centro", "dia", "hora_inicio"]
        unique_together = ("actividad_centro", "dia", "hora_inicio", "hora_fin")

    def __str__(self):
        return f"{self.actividad_centro} - {self.dia.nombre}: {self.hora_inicio}-{self.hora_fin}"




class ParticipanteActividad(models.Model):

    ESTADO_INSCRIPCION = [
        ("inscrito", "Inscrito"),
        ("lista_espera", "Lista de Espera"),
        ("dado_baja", "Dado de Baja"),
    ]

    actividad_centro = models.ForeignKey(
        ActividadCentro, on_delete=models.CASCADE, verbose_name="Actividad del Centro"
    )
    ciudadano = models.ForeignKey(
        Ciudadano, on_delete=models.CASCADE, verbose_name="Ciudadano"
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
        constraints = [
            UniqueConstraint(
                fields=["actividad_centro", "ciudadano"],
                condition=Q(estado__in=["inscrito", "lista_espera"]),
                name="unique_activo_inscripcion",
            )
        ]
        indexes = [
            models.Index(fields=["actividad_centro"]),
            models.Index(fields=["estado"]),
        ]


class ParticipanteActividadHistorial(models.Model):
    """
    Historial inmutable de cambios de estado de las inscripciones.
    Registra quién y cuándo realizó cada transición.
    """

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
        User, on_delete=models.PROTECT, verbose_name="Usuario que realizó el cambio"
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


class Expediente(models.Model):
    centro = models.ForeignKey(
        Centro, on_delete=models.CASCADE, related_name="expedientes_cabal"
    )
    archivo = models.FileField(upload_to="informes_cabal/")
    periodo = models.DateField(help_text="Fecha del informe")
    fecha_subida = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    procesado = models.BooleanField(default=False)
    errores = models.TextField(blank=True)
