from django.db import models
from django.contrib.auth.models import User
from comedores.models.comedor import Comedor


class DocumentacionAdjunta(models.Model):
    nombre = models.CharField(max_length=255, verbose_name="Nombre del Documento")
    archivo = models.FileField(upload_to="documentos_adjuntos/", verbose_name="Archivo")
    fecha_creacion = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de Creación"
    )
    ultima_modificacion = models.DateTimeField(
        auto_now=True, verbose_name="Última Modificación"
    )

    class Meta:
        verbose_name = "Documento Adjunto"
        verbose_name_plural = "Documentos Adjuntos"

class RendicionCuentaMensual(models.Model):
    comedor = models.ForeignKey(
        Comedor, on_delete=models.SET_NULL, 
        related_name="rendiciones_cuentas_mensuales",
        null=True,
        blank=True,
    )
    mes = models.IntegerField(verbose_name="Mes")
    anio = models.IntegerField(verbose_name="Año")
    documento_adjunto = models.BooleanField(
        default=False, verbose_name="Documento Adjunto"
    )
    observaciones = models.TextField(
        verbose_name="Observaciones", blank=True, null=True
    )
    ultima_modificacion = models.DateTimeField(
        auto_now=True, verbose_name="Última Modificación"
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de Creación"
    )
    arvhios_adjuntos = models.ManyToManyField(
        DocumentacionAdjunta,
        related_name="rendiciones_cuentas_mensuales",
        blank=True,
    )

    class Meta:
        verbose_name = "Rendición de Cuenta Mensual"
        verbose_name_plural = "Rendiciones de Cuenta Mensuales"