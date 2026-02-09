from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()

class Prestacion(models.Model):
    programa = models.CharField(
        max_length=255, verbose_name="Programa", blank=True, null=True
    )
    desayuno_valor = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Valor desayuno", blank=True, null=True
    )
    almuerzo_valor = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Valor almuerzo", blank=True, null=True
    )
    merienda_valor = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Valor merienda", blank=True, null=True
    )
    cena_valor = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Valor cena", blank=True, null=True
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    fecha_modificacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")
    usuario_creador = models.ForeignKey(User, on_delete=models.DO_NOTHING)
        
    def __str__(self):
        return str(self.programa)

    class Meta:
        ordering = ["id"]
        verbose_name = "Prestación"
        verbose_name_plural = "Prestaciones"
