import re
from urllib.parse import urlparse, urlunparse

from django.db import models
from django.urls import reverse

from core.permissions.registry import build_legacy_permission_code

ADMIN_DASHBOARD_PERMISSION_CODES = (
    "auth.role_admin",
    "auth.role_administrador",
    "auth.role_superadmin",
)
LOOKER_STUDIO_HOSTS = {
    "datastudio.google.com",
    "lookerstudio.google.com",
}


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
        help_text=(
            "Listado de permisos con acceso al tablero (app_label.codename). "
            "Se aceptan nombres de grupo legacy por compatibilidad."
        ),
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
    def _strip_looker_user_prefix(path):
        return re.sub(r"^/u/\d+/", "/", path or "")

    def usa_url_compartible_looker_studio(self):
        if not self.url:
            return False

        parsed_url = urlparse(self.url)
        hostname = (parsed_url.hostname or "").lower()
        if hostname not in LOOKER_STUDIO_HOSTS:
            return False

        normalized_path = self._strip_looker_user_prefix(parsed_url.path)
        return normalized_path.startswith("/reporting/")

    def get_embed_url(self):
        if not self.url:
            return ""

        parsed_url = urlparse(self.url)
        hostname = (parsed_url.hostname or "").lower()
        if hostname not in LOOKER_STUDIO_HOSTS:
            return self.url

        normalized_path = self._strip_looker_user_prefix(parsed_url.path)
        if normalized_path.startswith("/embed/reporting/"):
            if normalized_path == parsed_url.path:
                return self.url
            return urlunparse(parsed_url._replace(path=normalized_path))

        if not normalized_path.startswith("/reporting/"):
            return self.url

        return urlunparse(parsed_url._replace(path=f"/embed{normalized_path}"))

    @staticmethod
    def permission_codes_de_usuario(user):
        if not user or not user.is_authenticated:
            return []
        if hasattr(user, "cached_permission_codes"):
            return list(user.cached_permission_codes)
        permission_codes = list(user.get_all_permissions())
        user.cached_permission_codes = set(permission_codes)
        return permission_codes

    def _normalized_required_permissions(self):
        if not self.permisos:
            return []

        normalized = []
        for raw_value in self.permisos:
            raw_text = str(raw_value or "").strip()
            if not raw_text:
                continue
            if "." in raw_text:
                normalized.append(raw_text)
            else:
                normalized.append(build_legacy_permission_code(raw_text))
        return normalized

    def tiene_acceso_para_permisos(self, permission_codes):
        required = self._normalized_required_permissions()
        if not required:
            return False
        return any(permission in permission_codes for permission in required)

    def usuario_puede_ver(self, user):
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True

        permission_codes = self.permission_codes_de_usuario(user)
        if any(code in permission_codes for code in ADMIN_DASHBOARD_PERMISSION_CODES):
            return True
        return self.tiene_acceso_para_permisos(permission_codes)

    def get_mensaje_construccion(self):
        if self.mensaje_construccion:
            return self.mensaje_construccion
        return f"El tablero de {self.nombre} estará disponible próximamente."
