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


class RolFirmante(models.Model):
    nombre = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        ordering = ["id"]
        verbose_name = "Rol de Firmante"
        verbose_name_plural = "Roles de Firmante"


class Firmante(models.Model):
    organizacion = models.ForeignKey(
        "Organizacion", on_delete=models.CASCADE, related_name="firmantes"
    )
    nombre = models.CharField(max_length=255)
    rol = models.ForeignKey(
        RolFirmante,
        on_delete=models.PROTECT,
        related_name="firmantes",
        blank=True,
        null=True,
    )
    cuit = models.BigIntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.nombre} ({self.get_rol_display()})"


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
