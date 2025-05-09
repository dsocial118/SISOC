from django.db import models
from django.forms import ValidationError


class TipoOrganizacion(models.Model):
    nombre = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        ordering = ["id"]
        verbose_name = "Tipo de Organización"
        verbose_name_plural = "Tipos de Organización"


class Firmante(models.Model):
    organizacion = models.ForeignKey(
        "Organizacion",
        on_delete=models.CASCADE,
        related_name="firmantes"
    )
    nombre = models.CharField(max_length=255)
    rol = models.CharField(
        max_length=50,
        choices=[
                ("firmante1", "Firmante 1"), 
                ("firmante2", "Firmante 2"), 
                ("firmante3", "Firmante 3"), 
                ("obispo", "Obispo"),
                ("apoderado1", "Apoderado 1"),
                ("apoderado2", "Apoderado 2"),
                ("presidente", "Presidente"),
                ("secretario"," Secretario"),
                ("tesorero", "Tesorero"),
                ("aval", "Aval 1"),
                ("aval2", "Aval 2"),
                ("cuit_aval1", "CUIT Aval 1"),
                ("cuit_aval2", "CUIT Aval 2"),
                ]
    )

class Organizacion(models.Model):
    nombre = models.CharField(max_length=255)
    cuit = models.BigIntegerField(blank=True, null=True, unique=True)
    telefono = models.BigIntegerField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    tipo_organizacion = models.ForeignKey(
        TipoOrganizacion,
        on_delete=models.CASCADE,
        related_name="organizaciones",
        blank=True,
        null=True,
    )

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
