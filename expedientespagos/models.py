from django.db import models
from comedores.models import Comedor
from core.soft_delete import SoftDeleteModelMixin


class ExpedientePago(SoftDeleteModelMixin, models.Model):
    expediente_convenio = models.CharField(
        max_length=255,
        verbose_name="Expediente del Convenio",
    )
    expediente_pago = models.CharField(
        max_length=255, verbose_name="Expediente de Pago", blank=True, null=True
    )
    anexo = models.CharField(
        max_length=255, verbose_name="Anexo", blank=True, null=True
    )
    if_cantidad_de_prestaciones = models.CharField(
        max_length=255,
        verbose_name="IF Cantidad de Prestaciones",
        blank=True,
        null=True,
    )
    if_pagado = models.CharField(
        max_length=255, verbose_name="IF Pagado", blank=True, null=True
    )
    numero_orden_pago = models.CharField(
        max_length=255, verbose_name="Número de Orden de Pago", blank=True, null=True
    )
    fecha_pago_al_banco = models.DateField(
        verbose_name="Fecha de pago al banco", blank=True, null=True
    )
    fecha_acreditacion = models.DateField(
        verbose_name="Fecha de acreditación", blank=True, null=True
    )
    observaciones = models.TextField(
        verbose_name="Observaciones", blank=True, null=True
    )
    comedor = models.ForeignKey(
        Comedor,
        on_delete=models.SET_NULL,
        related_name="expedientes_pagos",
        null=True,
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de creación"
    )
    organizacion_creacion = models.CharField(
        max_length=255, verbose_name="Organización de creación", blank=True, null=True
    )
    total = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Total", blank=True, null=True
    )
    mes_pago = models.CharField(
        max_length=20, verbose_name="Mes de Pago", blank=True, null=True
    )
    ano = models.CharField(
        max_length=4,
        verbose_name="Año",
        blank=True,
        null=True,
    )
    prestaciones_mensuales_desayuno = models.IntegerField(
        verbose_name="Prestaciones mensuales desayuno",
    )
    prestaciones_mensuales_almuerzo = models.IntegerField(
        verbose_name="Prestaciones mensuales almuerzo",
    )
    prestaciones_mensuales_merienda = models.IntegerField(
        verbose_name="Prestaciones mensuales merienda",
    )
    prestaciones_mensuales_cena = models.IntegerField(
        verbose_name="Prestaciones mensuales cena",
    )
    monto_mensual_desayuno = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Monto mensual desayuno",
    )
    monto_mensual_almuerzo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Monto mensual almuerzo",
    )
    monto_mensual_merienda = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Monto mensual merienda",
    )
    monto_mensual_cena = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Monto mensual cena",
    )

    class Meta:
        verbose_name = "Expediente de Pago"
        verbose_name_plural = "Expedientes de Pago"
