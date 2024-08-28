from django.db import models
from django.urls import *
from django.contrib.auth.models import User, Permission
from django.db.models import Q

from .choices import *


# region------- EXTENSION DEL MODELO USER---------------------------------------------------------------------


# Agrego extrafields telefono y programa
class Usuarios(models.Model):
    """
    Extensión del modelo USER
    """

    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    imagen = models.ImageField(upload_to="usuarios/", null=True, blank=True)
    dni = models.PositiveIntegerField(null=True, blank=True, unique=True)
    telefono = models.CharField(
        max_length=30,
        null=True,
        blank=True,
    )
    darkmode = models.BooleanField(default=True, null=True, blank=True)

    def __str__(self):
        if self.usuario.first_name or self.usuario.last_name:
            nombre = self.usuario.first_name + " " + self.usuario.last_name
        else:
            nombre = self.usuario.username

        return nombre

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        permissions = [
            ("rol_directivo", "Directivo"),
            ("rol_operativo", "Equipo operativo"),
            ("rol_consultante", "Consultante"),
            ("rol_observador", "Observador"),
            ("rol_tecnico", "Equipo técnico"),
            ("rol_admin", "Administrador"),
            ("programa_externo", "Externo"),
            ("programa_CDIF", "CDIF"),
            ("programa_CDLE", "CDLE"),
            ("programa_PDV", "PDV"),
            ("programa_1000D", "1000D"),
            ("programa_SL", "SL"),
            ("programa_MA", "MA"),
            ("programa_Reporte", "Reporte"),
            ("programa_Administracion", "Administración"),
            ("programa_Legajo", "Legajo"),
            ("programa_Configuracion", "Configuración"),
            ("programa_Dashboard", "Dashboard"),
        ]

    def users_con_perm(perm_name):
        return User.objects.filter(
            Q(user_permissions__codename=perm_name)
            | Q(groups__permissions__codename=perm_name)
        ).distinct()

    def get_absolute_url(self):
        return reverse("usuarios_ver", kwargs={"pk": self.pk})


def users_con_permiso(perm_name):
    return User.objects.filter(
        Q(user_permissions__codename=perm_name)
        | Q(groups__permissions__codename=perm_name)
    ).distinct()


# endregion ------------------FIN EXTENSION USER MODEL--------------+---------------------------------------------
