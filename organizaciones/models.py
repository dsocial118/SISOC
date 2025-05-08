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


class FirmanteHecho(models.Model):
    firmante1 = models.CharField(max_length=255, blank=True, null=True)
    firmante2 = models.CharField(max_length=255, blank=True, null=True)
    aval1 = models.CharField(max_length=255, blank=True, null=True)
    cuitaval1 = models.IntegerField(blank=True, null=True)
    aval2 = models.CharField(max_length=255, blank=True, null=True)
    cuitaval2 = models.IntegerField(blank=True, null=True)


class FirmanteEclesiastica(models.Model):
    obispo = models.CharField(max_length=255, blank=True, null=True)
    apoderado1 = models.CharField(max_length=255, blank=True, null=True)
    apoderado2 = models.CharField(max_length=255, blank=True, null=True)


class FirmanteJuridica(models.Model):
    presidente = models.CharField(max_length=255, blank=True, null=True)
    tesorero = models.CharField(max_length=255, blank=True, null=True)
    secretario = models.CharField(max_length=255, blank=True, null=True)


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
    firmante_juridica = models.OneToOneField(
        "FirmanteJuridica", on_delete=models.SET_NULL, null=True, blank=True
    )
    firmante_eclesiastica = models.OneToOneField(
        "FirmanteEclesiastica", on_delete=models.SET_NULL, null=True, blank=True
    )
    firmante_hecho = models.OneToOneField(
        "FirmanteHecho", on_delete=models.SET_NULL, null=True, blank=True
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
