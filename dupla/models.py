from django.db import models
from django.contrib.auth.models import User
from django.forms import ValidationError


class Dupla(models.Model):
    nombre = models.CharField(max_length=255)
    tecnico = models.ManyToManyField(
        User,
        blank=False,
        null=False,
        related_name="dupla_tecnico",
    )
    fecha = models.DateField()
    abogado = models.ForeignKey(
        User, on_delete=models.PROTECT, blank=False, null=False
    )