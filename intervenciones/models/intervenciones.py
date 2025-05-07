# intervenciones/models.py
from django.db import models
from django.utils import timezone


class EstadosIntervencion(models.Model):
    """
    Guardado de los estados de las intervenciones realizadas.
    """

    nombre = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.nombre}"

    class Meta:
        verbose_name = "Estado de Intervención"
        verbose_name_plural = "Estados de Intervención"
        ordering = ["id"]


class TipoIntervencion(models.Model):
    """
    Guardado de los tipos de intervenciones realizadas.
    """

    nombre = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.nombre}"

    class Meta:
        verbose_name = "Tipo de Intervención"
        verbose_name_plural = "Tipos de Intervención"
        ordering = ["id"]


class SubIntervencion(models.Model):
    """
    Guardado de las sub-intervenciones realizadas.
    """

    nombre = models.CharField(max_length=255)
    tipo_intervencion = models.ForeignKey(
        TipoIntervencion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subintervenciones",
        verbose_name="Tipo de Intervención asociada",
    )

    def __str__(self):
        return f"{self.nombre}"

    class Meta:
        verbose_name = "Sub-Intervención"
        verbose_name_plural = "Sub-Intervenciones"
        ordering = ["tipo_intervencion", "nombre"]


class TipoDestinatario(models.Model):
    """
    Guardado de los destinatarios de las intervenciones realizadas.
    """

    nombre = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.nombre}"

    class Meta:
        verbose_name = "Destinatario"
        verbose_name_plural = "Destinatarios"
        ordering = ["id"]


class TipoContacto(models.Model):
    """
    Guardado de los tipos de contacto de las intervenciones realizadas.
    """

    nombre = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.nombre}"

    class Meta:
        verbose_name = "Tipo de Contacto"
        verbose_name_plural = "Tipos de Contacto"
        ordering = ["id"]


class Intervencion(models.Model):
    """
    Registro de intervenciones realizadas a comedores.
    """

    comedor = models.ForeignKey(
        "comedores.Comedor",
        on_delete=models.SET_NULL,
        null=True,
        related_name="intervenciones",
        verbose_name="Comedor intervenido",
    )
    subintervencion = models.ForeignKey(
        SubIntervencion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Sub-tipo de intervención",
    )
    tipo_intervencion = models.ForeignKey(
        TipoIntervencion,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Tipo de intervención",
    )
    fecha = models.DateTimeField(
        default=timezone.now, verbose_name="Fecha y hora de intervención"
    )
    estado = models.ForeignKey(
        EstadosIntervencion,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Estado actual",
    )
    observaciones = models.TextField(
        blank=True, null=True, verbose_name="Observaciones"
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
    tiene_documentacion = models.BooleanField(
        default=False, verbose_name="Documentación adjunta"
    )
    documentacion = models.FileField(
        upload_to="documentacion/",
        blank=True,
        null=True,
        verbose_name="Documentación Adjunta",
    )

    class Meta:
        verbose_name = "Intervención"
        verbose_name_plural = "Intervenciones"
        ordering = ["-fecha"]
        indexes = [
            models.Index(fields=["comedor"]),
            models.Index(fields=["fecha"]),
            models.Index(fields=["tipo_intervencion"]),
        ]

    def __str__(self):
        return f"Intervención en {self.comedor} - {self.fecha.strftime('%Y-%m-%d')}"
