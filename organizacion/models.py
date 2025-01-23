from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.forms import ValidationError


class Organizacion(models.Model):
    nombre = models.CharField(max_length=255, verbose_name="Nombre de la organizacion",blank=False, null=False)
    cuit = models.CharField(max_length=13,blank=True, null=True,unique=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(verbose_name="Mail de la organizacion", blank=True, null=True)

    def __str__(self):
        return f"{self.nombre}"
    
    class meta:
        verbose_name = "Organización"
        verbose_name_plural = "Organizaciones"
