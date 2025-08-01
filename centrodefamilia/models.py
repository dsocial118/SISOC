from django.db import models
from django.contrib.auth.models import User
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
    codigo = models.CharField(max_length=10, unique=True)
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
    dias = models.ManyToManyField(
        to=Dia,
        related_name="DiaActividad",
        blank=True,
    )
    sexoact = models.ManyToManyField(
        to=Sexo,
        related_name="sexoactividad",
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

    def __str__(self):
        return f"{self.actividad.nombre} en {self.centro.nombre}"

    class Meta:
        verbose_name = "Actividad del Centro"
        verbose_name_plural = "Actividades por Centro"


class ParticipanteActividad(models.Model):
    actividad_centro = models.ForeignKey(
        "ActividadCentro", on_delete=models.CASCADE, verbose_name="Actividad del Centro"
    )
    ciudadano = models.ForeignKey(
        Ciudadano, on_delete=models.CASCADE, verbose_name="Ciudadano"
    )
    fecha_registro = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de Registro"
    )

    def __str__(self):
        return f"{self.ciudadano.apellido}, {self.ciudadano.nombre} - {self.actividad_centro}"

    class Meta:
        verbose_name = "Participante"
        verbose_name_plural = "Participantes"
        unique_together = ("actividad_centro", "ciudadano")
        indexes = [
            models.Index(fields=["actividad_centro"]),
        ]

class Expediente(models.Model):
    centro = models.ForeignKey(
        'centrodefamilia.Centro',
        on_delete=models.CASCADE,
        related_name="expedientes_cabal",
        db_index=True,
        null=True,
        blank=True,
    )
    archivo = models.FileField(upload_to="informes_cabal/")
    periodo = models.DateField(help_text="Fecha del informe Cabal", db_index=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, db_index=True)
    procesado = models.BooleanField(default=False, db_index=True)
    errores = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['centro']),
            models.Index(fields=['periodo']),
            models.Index(fields=['procesado']),
        ]
        ordering = ['-fecha_subida']
        verbose_name = "Expediente Cabal"
        verbose_name_plural = "Expedientes Cabal"

    def __str__(self):
        centro_codigo = self.centro.codigo if self.centro else 'Global'
        return f"Informe Cabal {centro_codigo} - {self.periodo}"


class MovimientoCabal(models.Model):
    expediente = models.ForeignKey(
        Expediente,
        on_delete=models.CASCADE,
        related_name="movimientos",
        db_index=True
    )
    centro = models.ForeignKey(
        'centrodefamilia.Centro',
        on_delete=models.PROTECT,
        db_index=True
    )
    ciudadano = models.ForeignKey(
        'ciudadanos.Ciudadano',
        on_delete=models.PROTECT,
        db_index=True
    )
    monto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Monto registrado en el movimiento Cabal"
    )
    fecha = models.DateField(
        help_text="Fecha del movimiento registrado en el Excel",
        db_index=True
    )
    fila_origen = models.PositiveIntegerField(
        help_text="Número de fila en el Excel de origen",
        db_index=True
    )

    class Meta:
        indexes = [
            models.Index(fields=['expediente']),
            models.Index(fields=['centro']),
            models.Index(fields=['ciudadano']),
            models.Index(fields=['fecha']),
            models.Index(fields=['fila_origen']),
        ]
        ordering = ['expediente', 'fila_origen']
        verbose_name = "Movimiento Cabal"
        verbose_name_plural = "Movimientos Cabal"

    def __str__(self):
        return f"Movimiento {self.centro.codigo} - {self.ciudadano.documento} - {self.monto}"
