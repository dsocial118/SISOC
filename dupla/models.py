from django.db import models
from django.contrib.auth.models import User


class Dupla(models.Model):
    nombre = models.CharField(max_length=255)
    tecnico = models.ManyToManyField(
        User,
        blank=False,
        related_name="dupla_tecnico",
    )
    estado = models.CharField(
        max_length=50,
        choices=[
            ("Activo", "Activo"),
            ("Inactivo", "Inactivo"),
        ],
    )
    fecha = models.DateTimeField(auto_now_add=True)
    abogado = models.ForeignKey(User, on_delete=models.PROTECT, blank=False)
