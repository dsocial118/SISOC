from django.db import models
from django.contrib.auth.models import User


class Dupla(models.Model):
    """Relación entre técnicos y abogados que trabajan como dupla."""

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

    @property
    def tecnicos_nombres(self) -> str:
        """Devuelve los nombres de técnicos separados por coma para mostrar en tablas."""
        try:
            nombres = ", ".join(
                getattr(u, "get_full_name", lambda: "")()
                or getattr(u, "username", str(u))
                for u in self.tecnico.all()
            )
            return nombres or "—"
        except Exception:
            return "—"
