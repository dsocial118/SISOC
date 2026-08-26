from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
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
    admision = models.ForeignKey(
        "admisiones.Admision",
        on_delete=models.SET_NULL,
        related_name="expedientes_pagos",
        null=True,
        blank=True,
        verbose_name="Admisión",
        help_text=(
            "Si se deja vacío, se intenta resolver automáticamente a partir del "
            "expediente del convenio."
        ),
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
    total_prestaciones = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Total Prestaciones",
        blank=True,
        null=True,
    )
    gastos_accesorios = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Gastos Accesorios 6%",
        blank=True,
        null=True,
    )
    mes_pago = models.CharField(
        max_length=20, verbose_name="Mes de Pago", blank=True, null=True
    )
    mes_convenio = models.PositiveSmallIntegerField(
        verbose_name="Mes de Convenio",
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(6)],
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

    def save(self, *args, **kwargs):
        """Resuelve la admisión antes de guardar, si quedó sin asignar.

        La resolución vive acá y no en el servicio porque los expedientes de pago
        entran por varias puertas: el formulario de alta, la importación por CSV
        (``importarexpediente``, que instancia el modelo y guarda directo) y la
        consola. Todas terminan en ``save()``, así que es el único lugar donde la
        vinculación corre siempre.

        Nunca pisa una admisión ya asignada: dejar el campo vacío es justamente
        lo que significa "resolver automáticamente".
        """
        if self.admision_id is None:
            from expedientespagos.vinculacion import (  # pylint: disable=import-outside-toplevel
                resolver_admision,
            )

            admision = resolver_admision(self.comedor, self.expediente_convenio)
            if admision is not None:
                self.admision = admision
                update_fields = kwargs.get("update_fields")
                if update_fields is not None:
                    kwargs["update_fields"] = set(update_fields) | {"admision"}

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Expediente de Pago"
        verbose_name_plural = "Expedientes de Pago"
