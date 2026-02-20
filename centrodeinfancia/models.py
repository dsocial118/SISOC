from django.db import models
from django.utils import timezone

from ciudadanos.models import Ciudadano
from core.soft_delete import SoftDeleteModelMixin
from intervenciones.models.intervenciones import (
    SubIntervencion,
    TipoContacto,
    TipoDestinatario,
    TipoIntervencion,
)
from organizaciones.models import Organizacion


class CentroDeInfancia(SoftDeleteModelMixin, models.Model):
    nombre = models.CharField(max_length=255)
    organizacion = models.ForeignKey(
        Organizacion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Centro de Infancia"
        verbose_name_plural = "Centros de Infancia"
        ordering = ["nombre"]

    def __str__(self):
        return str(self.nombre)


class NominaCentroInfancia(SoftDeleteModelMixin, models.Model):
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
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Nómina Centro de Infancia"
        verbose_name_plural = "Nóminas Centro de Infancia"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.ciudadano} en {self.centro} ({self.get_estado_display()})"


class IntervencionCentroInfancia(SoftDeleteModelMixin, models.Model):
    centro = models.ForeignKey(
        CentroDeInfancia,
        on_delete=models.CASCADE,
        related_name="intervenciones",
    )
    tipo_intervencion = models.ForeignKey(
        TipoIntervencion,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Tipo de intervención",
    )
    subintervencion = models.ForeignKey(
        SubIntervencion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Sub-tipo de intervención",
    )
    destinatario = models.ForeignKey(
        TipoDestinatario,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Destinatario",
    )
    forma_contacto = models.ForeignKey(
        TipoContacto,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Forma de contacto",
    )
    fecha = models.DateTimeField(default=timezone.now)
    observaciones = models.TextField(blank=True, null=True)
    tiene_documentacion = models.BooleanField(default=False)
    documentacion = models.FileField(upload_to="documentacion/", blank=True, null=True)

    class Meta:
        verbose_name = "Intervención Centro de Infancia"
        verbose_name_plural = "Intervenciones Centro de Infancia"
        ordering = ["-fecha"]

    def __str__(self):
        fecha = self.fecha.strftime("%Y-%m-%d") if self.fecha else "sin fecha"
        return f"Intervención en {self.centro} - {fecha}"
