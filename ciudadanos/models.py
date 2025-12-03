from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone

from core.models import Localidad, Municipio, Programa, Provincia, Sexo

User = get_user_model()


class Ciudadano(models.Model):
    """Datos básicos del ciudadano/a."""

    DOCUMENTO_DNI = "DNI"
    DOCUMENTO_CUIT = "CUIT"
    DOCUMENTO_PASAPORTE = "PASAPORTE"
    DOCUMENTO_LE = "LE"
    DOCUMENTO_CHOICES = [
        (DOCUMENTO_DNI, "DNI"),
        (DOCUMENTO_CUIT, "CUIT"),
        (DOCUMENTO_PASAPORTE, "Pasaporte"),
        (DOCUMENTO_LE, "Libreta de enrolamiento"),
    ]

    apellido = models.CharField(max_length=255)
    nombre = models.CharField(max_length=255)
    fecha_nacimiento = models.DateField()
    tipo_documento = models.CharField(
        max_length=20, choices=DOCUMENTO_CHOICES, default=DOCUMENTO_DNI
    )
    documento = models.PositiveBigIntegerField(
        validators=[MinValueValidator(1)], null=True
    )
    sexo = models.ForeignKey(Sexo, on_delete=models.SET_NULL, null=True, blank=True)
    nacionalidad = models.CharField(max_length=100, null=True, blank=True)

    calle = models.CharField(max_length=255, null=True, blank=True)
    altura = models.CharField(max_length=10, null=True, blank=True)
    piso_departamento = models.CharField(max_length=50, null=True, blank=True)
    barrio = models.CharField(max_length=100, null=True, blank=True)
    provincia = models.ForeignKey(
        Provincia, on_delete=models.SET_NULL, null=True, blank=True
    )
    municipio = models.ForeignKey(
        Municipio, on_delete=models.SET_NULL, null=True, blank=True
    )
    localidad = models.ForeignKey(
        Localidad, on_delete=models.SET_NULL, null=True, blank=True
    )
    codigo_postal = models.CharField(max_length=12, null=True, blank=True)

    telefono = models.CharField(max_length=30, null=True, blank=True)
    telefono_alternativo = models.CharField(max_length=30, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)

    observaciones = models.TextField(null=True, blank=True)
    foto = models.ImageField(upload_to="ciudadanos", blank=True, null=True)

    familiares = models.ManyToManyField(
        "self", through="GrupoFamiliar", symmetrical=True, blank=True
    )

    creado_por = models.ForeignKey(
        User,
        related_name="ciudadano_creado_por",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    modificado_por = models.ForeignKey(
        User,
        related_name="ciudadano_modificado_por",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    creado = models.DateTimeField(default=timezone.now, editable=False)
    modificado = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["apellido", "nombre"]
        unique_together = ("tipo_documento", "documento")
        indexes = [
            models.Index(fields=["apellido", "nombre"]),
            models.Index(fields=["documento"]),
        ]

    def __str__(self) -> str:
        return f"{self.apellido}, {self.nombre}".strip(", ")

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido}".strip()

    def get_absolute_url(self):
        return reverse("ciudadanos_ver", kwargs={"pk": self.pk})


class GrupoFamiliar(models.Model):
    """Relación básica entre dos ciudadanos."""

    RELACION_PADRE = "PADRE/MADRE"
    RELACION_HIJO = "HIJO/A"
    RELACION_PAREJA = "PAREJA"
    RELACION_HERMANO = "HERMANO/A"
    RELACION_TUTOR = "TUTOR/A"
    RELACION_OTRO = "OTRO"

    VINCULO_CHOICES = [
        (RELACION_PADRE, "Padre/Madre"),
        (RELACION_HIJO, "Hijo/a"),
        (RELACION_PAREJA, "Pareja"),
        (RELACION_HERMANO, "Hermano/a"),
        (RELACION_TUTOR, "Tutor/a"),
        (RELACION_OTRO, "Otro"),
    ]

    ESTADO_BUENO = "bueno"
    ESTADO_REGULAR = "regular"
    ESTADO_CONFLICTIVO = "conflictivo"
    ESTADO_CHOICES = [
        (ESTADO_BUENO, "Bueno"),
        (ESTADO_REGULAR, "Regular"),
        (ESTADO_CONFLICTIVO, "Conflictivo"),
    ]

    ciudadano_1 = models.ForeignKey(
        Ciudadano, related_name="relaciones_salientes", on_delete=models.CASCADE
    )
    ciudadano_2 = models.ForeignKey(
        Ciudadano, related_name="relaciones_entrantes", on_delete=models.CASCADE
    )
    vinculo = models.CharField(
        max_length=20, choices=VINCULO_CHOICES, null=True, blank=True
    )
    estado_relacion = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, null=True, blank=True
    )
    conviven = models.BooleanField(default=False)
    cuidador_principal = models.BooleanField(default=False)
    observaciones = models.TextField(null=True, blank=True)

    creado = models.DateTimeField(default=timezone.now, editable=False)
    modificado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["ciudadano_1", "ciudadano_2"]
        unique_together = ("ciudadano_1", "ciudadano_2")
        indexes = [
            models.Index(fields=["ciudadano_1"]),
            models.Index(fields=["ciudadano_2"]),
        ]

    def __str__(self) -> str:
        return f"{self.ciudadano_1} - {self.ciudadano_2} ({self.vinculo})"

    def get_absolute_url(self):
        return reverse("ciudadanos_ver", kwargs={"pk": self.ciudadano_1_id})


class CiudadanoPrograma(models.Model):
    programas = models.ForeignKey(
        Programa, related_name="programa_ciudadano", on_delete=models.CASCADE
    )
    ciudadano = models.ForeignKey(
        Ciudadano, related_name="ciudadano_programa", on_delete=models.CASCADE
    )
    fecha_creado = models.DateField(auto_now=True)
    creado_por = models.ForeignKey(
        User,
        related_name="prog_creado_por",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["-fecha_creado"]
        verbose_name = "CiudadanoProgramas"
        verbose_name_plural = "CiudadanosProgramas"
        unique_together = (("ciudadano", "programas"),)


class HistorialCiudadanoProgramas(models.Model):
    fecha = models.DateTimeField(auto_now_add=True)
    accion = models.CharField(
        max_length=10, choices=[("agregado", "Agregado"), ("eliminado", "Eliminado")]
    )
    programa = models.ForeignKey(
        Programa, related_name="hist_prog_ciudadano", on_delete=models.CASCADE
    )
    ciudadano = models.ForeignKey(
        Ciudadano, related_name="hist_ciudadano_programa", on_delete=models.CASCADE
    )
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ["-fecha"]
        verbose_name = "Historial CiudadanoPrograma"
        verbose_name_plural = "Historial CiudadanosProgramas"

    def __str__(self):
        return f"{self.fecha} - {self.accion} - {self.programa} - {self.ciudadano}"
