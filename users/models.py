from django.contrib.auth.models import User
from django.db import models

from core.models import Provincia


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    dark_mode = models.BooleanField(default=True)
    es_usuario_provincial = models.BooleanField(default=False)
    provincia = models.ForeignKey(
        Provincia, on_delete=models.SET_NULL, null=True, blank=True
    )
    rol = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"Perfil de {self.user.username}"
