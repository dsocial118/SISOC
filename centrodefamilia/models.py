from django.db import models
from django.contrib.auth.models import User
from ciudadanos.models import Ciudadano
from configuraciones.models import Dia, Localidad, Municipio, Provincia
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
    calle = models.CharField(
        max_length=255, blank=True, null=True
    )
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
    horarios = models.TimeField()
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
        ActividadCentro, on_delete=models.CASCADE, verbose_name="Actividad del Centro"
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


class Orientador(models.Model):
    centro = models.ForeignKey(Centro, on_delete=models.CASCADE, verbose_name="Centro")
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    apellido = models.CharField(max_length=100, verbose_name="Apellido")
    dni = models.CharField(max_length=15, verbose_name="DNI")
    genero = models.CharField(
        max_length=20,
        choices=[
            ("masculino", "Masculino"),
            ("femenino", "Femenino"),
            ("otro", "Otro"),
        ],
        verbose_name="Género",
    )
    foto = models.ImageField(upload_to="centros/orientador/", blank=True, null=True)
    cargo = models.CharField(
        max_length=20,
        choices=[
            ("profesor", "profesor"),
            ("administrativo", "administrativo"),
            ("otro", "Otro"),
        ],
        verbose_name="Cargo",
    )

    def __str__(self):
        return f"{self.apellido}, {self.nombre} - {self.dni}"

    class Meta:
        verbose_name = "Orientador"
        verbose_name_plural = "Orientadores"
