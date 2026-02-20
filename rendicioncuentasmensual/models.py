from django.db import models
from comedores.models import Comedor
from core.soft_delete import SoftDeleteModelMixin


class DocumentacionAdjunta(SoftDeleteModelMixin, models.Model):
    nombre = models.CharField(max_length=255, verbose_name="Nombre del Documento")
    archivo = models.FileField(
        upload_to="rendicioncuentasmensualdocumentos_adjuntos/", verbose_name="Archivo"
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de Creación"
    )
    ultima_modificacion = models.DateTimeField(
        auto_now=True, verbose_name="Última Modificación"
    )
    rendicion_cuenta_mensual = models.ForeignKey(
        "RendicionCuentaMensual",
        on_delete=models.CASCADE,
        related_name="arvhios_adjuntos",  # FIXME: Arreglar typo
        verbose_name="Rendición de Cuenta Mensual",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Documento Adjunto"
        verbose_name_plural = "Documentos Adjuntos"


class RendicionCuentaMensual(SoftDeleteModelMixin, models.Model):
    MESES = [
        (1, "Enero"),
        (2, "Febrero"),
        (3, "Marzo"),
        (4, "Abril"),
        (5, "Mayo"),
        (6, "Junio"),
        (7, "Julio"),
        (8, "Agosto"),
        (9, "Septiembre"),
        (10, "Octubre"),
        (11, "Noviembre"),
        (12, "Diciembre"),
    ]
    comedor = models.ForeignKey(
        Comedor,
        on_delete=models.SET_NULL,
        related_name="rendiciones_cuentas_mensuales",
        null=True,
        blank=True,
    )
    mes = models.IntegerField(verbose_name="Mes", choices=MESES)
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

    class Meta:
        verbose_name = "Rendición de Cuenta Mensual"
        verbose_name_plural = "Rendiciones de Cuenta Mensuales"
