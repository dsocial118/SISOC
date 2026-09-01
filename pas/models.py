from django.conf import settings
from django.db import models

from core.models import Municipio, Provincia


class PasEstado(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Estado PAS"
        verbose_name_plural = "Estados PAS"

    def __str__(self):
        return self.nombre


class PasAviso(models.Model):
    codigo = models.PositiveIntegerField(unique=True)
    descripcion = models.CharField(max_length=255)
    observacion = models.CharField(max_length=255, blank=True)
    estados = models.ManyToManyField(PasEstado, related_name="avisos")

    class Meta:
        ordering = ["codigo"]
        verbose_name = "Aviso PAS"
        verbose_name_plural = "Avisos PAS"

    def __str__(self):
        return f"{self.codigo} - {self.descripcion}"


class PasPersona(models.Model):
    id_persona = models.PositiveIntegerField(unique=True, verbose_name="IdPersona")
    apellidos = models.CharField(max_length=150)
    nombres = models.CharField(max_length=150)
    dni = models.PositiveIntegerField(unique=True)
    cuit = models.CharField(max_length=20, blank=True)
    provincia = models.ForeignKey(Provincia, on_delete=models.PROTECT)
    municipio = models.ForeignKey(Municipio, on_delete=models.PROTECT)
    estado = models.ForeignKey(PasEstado, on_delete=models.PROTECT)
    avisos = models.ManyToManyField(PasAviso, related_name="personas")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["apellidos", "nombres", "id_persona"]
        verbose_name = "Persona PAS"
        verbose_name_plural = "Personas PAS"

    def __str__(self):
        return f"{self.apellidos}, {self.nombres} - {self.dni}"


class PasHistorialEstado(models.Model):
    persona = models.ForeignKey(
        PasPersona,
        on_delete=models.CASCADE,
        related_name="historial_estados",
    )
    estado_anterior = models.ForeignKey(
        PasEstado,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="historiales_como_anterior",
    )
    estado_nuevo = models.ForeignKey(
        PasEstado,
        on_delete=models.PROTECT,
        related_name="historiales_como_nuevo",
    )
    avisos_anteriores = models.ManyToManyField(
        PasAviso,
        blank=True,
        related_name="historiales_como_anterior",
    )
    avisos_nuevos = models.ManyToManyField(
        PasAviso,
        related_name="historiales_como_nuevo",
    )
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-fecha_cambio", "-id"]
        verbose_name = "Historial de estado PAS"
        verbose_name_plural = "Historiales de estado PAS"

    def __str__(self):
        return f"{self.persona_id} - {self.estado_nuevo} - {self.fecha_cambio:%d/%m/%Y}"
