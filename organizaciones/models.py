from django.db import models
from django.forms import ValidationError


class Organizacion(models.Model):
    nombre = models.CharField(max_length=255)
    cuit = models.BigIntegerField(blank=True, null=True, unique=True)
    telefono = models.BigIntegerField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    def delete(self, *args, **kwargs):
        from comedores.models.comedor import (  # pylint: disable=import-outside-toplevel
            Comedor,
        )

        comedor_relacionado = Comedor.objects.filter(organizacion=self).first()

        if comedor_relacionado:
            raise ValidationError(
                f"No puedes eliminar {self.nombre} porque está relacionado con el comedor: {comedor_relacionado.nombre}."
            )
        super().delete(*args, **kwargs)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        ordering = ["id"]
        verbose_name = "Organizacion"
        verbose_name_plural = "Organizaciones"
