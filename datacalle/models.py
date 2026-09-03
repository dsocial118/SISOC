import uuid

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models

from core.models import Localidad, Municipio, Provincia
from core.soft_delete.base import SoftDeleteModelMixin


class Relevamiento(SoftDeleteModelMixin, models.Model):
    """Operativo de relevamiento de personas en situación de calle.

    Lo planifica un coordinador desde el backoffice y le baja al entrevistador
    como tarea en SISOC - Mobile DataCalle (ver D2 del canal de coordinación).
    Puede durar uno o varios días y agrupa N casos (encuestas).

    El id es UUID porque viaja a la app como identificador opaco y convive con
    los UUID que el dispositivo genera para los casos.
    """

    class Fase(models.TextChoices):
        ESPACIO_PUBLICO = "espacio_publico", "Espacio público"
        DISPOSITIVO_ALOJAMIENTO = (
            "dispositivo_alojamiento",
            "Dispositivo de alojamiento",
        )

    class Estado(models.TextChoices):
        PLANIFICADO = "planificado", "Planificado"
        EN_CURSO = "en_curso", "En curso"
        FINALIZADO = "finalizado", "Finalizado"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    denominacion = models.CharField(
        max_length=255,
        verbose_name="Denominación",
        help_text="Nombre con el que el equipo identifica el operativo.",
    )
    provincia = models.ForeignKey(Provincia, on_delete=models.PROTECT, related_name="+")
    municipio = models.ForeignKey(
        Municipio,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    localidad = models.ForeignKey(
        Localidad,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    fase = models.CharField(max_length=32, choices=Fase.choices)
    area_operativa = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Área operativa",
        help_text="Lugar del operativo cuando la fase es espacio público.",
    )
    dispositivo = models.ForeignKey(
        "dispositivos.Dispositivo",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="relevamientos_datacalle",
        help_text="Dispositivo de alojamiento donde se releva.",
    )
    fecha_inicio = models.DateField(verbose_name="Fecha de inicio")
    fecha_fin = models.DateField(verbose_name="Fecha de fin")
    modalidad_papel = models.BooleanField(
        default=False,
        verbose_name="Formato en papel",
        help_text="El operativo se releva en papel y se carga después en SISOC.",
    )
    estado = models.CharField(
        max_length=16,
        choices=Estado.choices,
        default=Estado.PLANIFICADO,
    )
    equipo = models.ManyToManyField(
        User,
        blank=True,
        related_name="relevamientos_datacalle",
        verbose_name="Equipo",
        help_text="Entrevistadores que ven este operativo como tarea en la app.",
    )
    observaciones = models.TextField(blank=True)

    # Datos que sólo se conocen al terminar: los manda la app en el cierre (D2.5).
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    cerrado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="relevamientos_datacalle_cerrados",
    )
    lat = models.FloatField(null=True, blank=True)
    lon = models.FloatField(null=True, blank=True)
    observacion_asentamiento = models.JSONField(default=list, blank=True)
    otra_observacion = models.TextField(blank=True)

    creado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="relevamientos_datacalle_creados",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Relevamiento DataCalle"
        verbose_name_plural = "Relevamientos DataCalle"
        ordering = ["-fecha_inicio", "denominacion"]
        indexes = [
            models.Index(fields=["provincia", "estado"]),
            models.Index(fields=["fecha_inicio"]),
        ]

    def __str__(self):
        return self.denominacion

    @property
    def esta_abierto(self) -> bool:
        return self.estado != self.Estado.FINALIZADO

    @property
    def lugar(self) -> str:
        if self.fase == self.Fase.DISPOSITIVO_ALOJAMIENTO and self.dispositivo_id:
            return self.dispositivo.nombre_institucion
        return self.area_operativa

    def clean(self):
        super().clean()
        errores = {}

        if self.fecha_inicio and self.fecha_fin and self.fecha_fin < self.fecha_inicio:
            errores["fecha_fin"] = (
                "La fecha de fin no puede ser anterior a la de inicio."
            )

        if self.municipio_id and self.municipio.provincia_id != self.provincia_id:
            errores["municipio"] = (
                "El municipio no pertenece a la provincia seleccionada."
            )
        if self.localidad_id:
            if not self.municipio_id:
                errores["localidad"] = (
                    "Para elegir localidad primero elegí el municipio."
                )
            elif self.localidad.municipio_id != self.municipio_id:
                errores["localidad"] = (
                    "La localidad no pertenece al municipio seleccionado."
                )

        if self.fase == self.Fase.ESPACIO_PUBLICO:
            if not (self.area_operativa or "").strip():
                errores["area_operativa"] = (
                    "Indicá el área operativa del espacio público."
                )
            if self.dispositivo_id:
                errores["dispositivo"] = (
                    "En espacio público no corresponde un dispositivo."
                )
        elif self.fase == self.Fase.DISPOSITIVO_ALOJAMIENTO:
            if not self.dispositivo_id:
                errores["dispositivo"] = "Elegí el dispositivo de alojamiento."
            elif self.dispositivo.provincia_id != self.provincia_id:
                errores["dispositivo"] = (
                    "El dispositivo no pertenece a la provincia seleccionada."
                )

        if errores:
            raise ValidationError(errores)
