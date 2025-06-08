from django.db import models
from django.core.exceptions import ValidationError

class Centro(models.Model):
    TIPO_CHOICES = (
        ('faro', 'Centro Faro'),
        ('adherido', 'Centro Adherido'),
    )

    nombre = models.CharField(max_length=255)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    direccion = models.TextField()
    contacto = models.CharField(max_length=255)
    activo = models.BooleanField(default=True)
    faro_asociado = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={'tipo': 'faro', 'activo': True},
        related_name='adheridos'
    )

    def clean(self):
        if self.tipo == 'adherido' and not self.faro_asociado:
            raise ValidationError("Un centro adherido debe tener un Centro Faro asociado.")
        if self.tipo == 'faro' and self.faro_asociado:
            raise ValidationError("Un Centro Faro no puede tener un centro faro asociado.")

    def __str__(self):
        return self.nombre


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre


class Actividad(models.Model):
    nombre = models.CharField(max_length=100)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('nombre', 'categoria')

    def __str__(self):
        return f"{self.nombre} ({self.categoria.nombre})"


class ActividadCentro(models.Model):
    centro = models.ForeignKey(Centro, on_delete=models.CASCADE)
    actividad = models.ForeignKey(Actividad, on_delete=models.CASCADE)
    cantidad_personas = models.PositiveIntegerField()
    dias = models.CharField(max_length=100)  # Ejemplo: "Lunes, Miércoles, Viernes"
    horarios = models.CharField(max_length=100)  # Ejemplo: "10:00 a 12:00"

    def __str__(self):
        return f"{self.actividad} en {self.centro}"


class ParticipanteActividad(models.Model):
    actividad_centro = models.ForeignKey(ActividadCentro, on_delete=models.CASCADE)
    cuit = models.CharField(max_length=20)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.cuit} - {self.actividad_centro}"
