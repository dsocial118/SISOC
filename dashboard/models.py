from django.db import models
from django.urls import reverse

from core.constants import UserGroups


class Dashboard(models.Model):
    """
    Modelo para almacenar información de dashboard.
    """

    llave = models.CharField(
        max_length=255,
        unique=True,
        primary_key=True,
        help_text="Llave única para identificar el registro en el dashboard.",
    )
    cantidad = models.BigIntegerField(
        default=0, help_text="Cantidad asociada al registro en el dashboard."
    )

    def aumentar_cantidad(self, cantidad: int = 1):
        self.cantidad += cantidad
        self.save()


class Tablero(models.Model):
    """
    Modelo para administrar tableros embebidos y sus permisos.
    """

    nombre = models.CharField(
        max_length=255,
        help_text="Nombre visible en el menú y el encabezado del tablero.",
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        help_text="Identificador único para la URL del tablero.",
    )
    url = models.URLField(
        blank=True,
        help_text="URL embebida del tablero (Power BI u otra herramienta).",
    )
    mensaje_construccion = models.TextField(
        blank=True,
        help_text="Mensaje a mostrar cuando el tablero no tiene URL.",
    )
    orden = models.PositiveIntegerField(
        default=0,
        help_text="Orden de aparición en el menú de tableros.",
    )
    activo = models.BooleanField(
        default=True,
        help_text="Define si el tablero aparece en el menú.",
    )
    permisos = models.JSONField(
        default=list,
        blank=True,
        help_text="Listado de grupos con acceso al tablero.",
    )

    class Meta:
        ordering = ["orden", "nombre"]
        verbose_name = "tablero"
        verbose_name_plural = "tableros"

    def __str__(self):
        return self.nombre

    @property
    def titulo(self):
        return f"Tablero {self.nombre}"

    def get_absolute_url(self):
        return reverse("dashboard_tablero", kwargs={"slug": self.slug})

    @staticmethod
    def grupos_de_usuario(user):
        if not user or not user.is_authenticated:
            return []
        if hasattr(user, "cached_groups"):
            return list(user.cached_groups)
        grupos = list(user.groups.values_list("name", flat=True))
        user.cached_groups = grupos
        return grupos

    def tiene_acceso_para_grupos(self, grupos):
        if not self.permisos:
            return False
        return any(grupo in self.permisos for grupo in grupos)

    def usuario_puede_ver(self, user):
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        grupos = self.grupos_de_usuario(user)
        if UserGroups.ADMINISTRADOR in grupos:
            return True
        return self.tiene_acceso_para_grupos(grupos)

    def get_mensaje_construccion(self):
        if self.mensaje_construccion:
            return self.mensaje_construccion
        return f"El tablero de {self.nombre} estará disponible próximamente."
