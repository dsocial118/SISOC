from django.db import models
from django.contrib.auth.models import User
from django.db.models import Count


class DuplaManager(models.Manager):
    """Manager personalizado para el modelo Dupla."""

    def activas_con_comedores(self):
        """
        Retorna duplas activas que tienen al menos un comedor asignado.

        Esta query se usa comúnmente en forms de asignación de coordinadores
        para evitar mostrar duplas sin comedores.

        Returns:
            QuerySet de Duplas activas con comedores, ordenadas por nombre
        """
        return (
            self.filter(estado="Activo")
            .annotate(comedores_count=Count('comedor'))
            .filter(comedores_count__gt=0)
            .order_by('nombre')
        )


class Dupla(models.Model):
    """Relación entre técnicos y abogados que trabajan como dupla.

    Coordinador:
    -----------
    Las duplas pueden tener un coordinador asignado. Esta relación es bidireccional:
    - Desde el ABM de Duplas: se puede asignar/cambiar el coordinador
    - Desde el ABM de Usuarios: se pueden asignar duplas al coordinador

    Cuando se elimina un coordinador, la dupla queda sin coordinador (coordinador=NULL).
    La sincronización entre Dupla.coordinador y Profile.duplas_asignadas se maneja
    automáticamente mediante signals.
    """

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
    coordinador = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="duplas_coordinadas",
        limit_choices_to={"groups__name": "Coordinador Equipo Tecnico"},
        verbose_name="Coordinador de Equipo Técnico",
        help_text="Coordinador asignado a esta dupla. Si se elimina el coordinador, este campo quedará vacío.",
    )

    # Manager personalizado
    objects = DuplaManager()

    def __str__(self):
        return self.nombre

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

    @property
    def coordinador_nombre(self) -> str:
        """Devuelve el nombre del coordinador o un indicador si no hay coordinador asignado."""
        if self.coordinador:
            return (
                self.coordinador.get_full_name()
                or self.coordinador.username
            )
        return "Sin asignar"
