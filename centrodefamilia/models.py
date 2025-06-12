from django.db import models
from django.core.exceptions import ValidationError

from django.contrib.auth.models import User


class Centro(models.Model):
    TIPO_CHOICES = [
        ("faro", "FARO"),
        ("adherido", "Adherido"),
    ]
    nombre = models.CharField(max_length=200)
    direccion = models.CharField(max_length=255)
    contacto = models.CharField(max_length=100)
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
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class ParticipanteActividad(models.Model):
    actividad_centro = models.ForeignKey(
        "ActividadCentro", on_delete=models.CASCADE, verbose_name="Actividad del Centro"
    )
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
    edad = models.PositiveIntegerField(verbose_name="Edad")
    cuit = models.CharField(max_length=20, verbose_name="CUIT del Participante")
    fecha_registro = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de Registro"
    )

    def __str__(self):
        return f"{self.apellido}, {self.nombre} - {self.actividad_centro}"

    class Meta:
        verbose_name = "Participante"
        verbose_name_plural = "Participantes"
        unique_together = ("actividad_centro", "cuit")


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre de la Categoría")

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"


class Actividad(models.Model):
    nombre = models.CharField(max_length=200, verbose_name="Nombre de la Actividad")
    categoria = models.ForeignKey(
        Categoria, on_delete=models.CASCADE, verbose_name="Categoría"
    )

    def __str__(self):
        return self.nombre


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
    dias = models.CharField(max_length=100, verbose_name="Días")
    horarios = models.CharField(max_length=100, verbose_name="Horarios")
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
