from django.db import models
from comedores.models.comedor import Comedor


class ExpedientePago(models.Model):
    expediente_pago = models.CharField(
        max_length=255, verbose_name="Expediente de Pago"
    )
    resolucion_pago = models.CharField(
        max_length=255, verbose_name="Resolución de Pago"
    )
    anexo = models.CharField(max_length=255, verbose_name="Anexo")
    if_cantidad_de_prestaciones = models.CharField(
        max_length=255, verbose_name="IF Cantidad de Prestaciones"
    )
    if_pagado = models.CharField(
        max_length=255, verbose_name="IF Pagado"
    )
    monto = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monto",blank=True, null=True)
    numero_orden_pago = models.CharField(
        max_length=255, verbose_name="Número de Orden de Pago"
    )
    fecha_pago_al_banco = models.DateField(verbose_name="Fecha de pago al banco", blank=True, null=True)
    fecha_acreditacion = models.DateField(verbose_name="Fecha de acreditación", blank=True, null=True)
    observaciones = models.TextField(verbose_name="Observaciones", blank=True, null=True)
    comedor = models.ForeignKey(
        Comedor, on_delete=models.SET_NULL, related_name="expedientes_pagos", null=True
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de creación"
    )

    class Meta:
        verbose_name = "Expediente de Pago"
        verbose_name_plural = "Expedientes de Pago"
