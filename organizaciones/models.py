from django.db import models


class Organizacion(models.Model):
    nombre = models.CharField(max_length=255)
    cuit = models.CharField(max_length=13, blank=True, null=True, unique=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
