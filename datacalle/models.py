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
    localidades = models.ManyToManyField(
        Localidad,
        blank=True,
        related_name="relevamientos_datacalle",
        verbose_name="Localidades / comunas",
        help_text="Un operativo puede abarcar varias zonas del mismo municipio.",
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
            # Soporta el orden por defecto del listado sin filesort.
            models.Index(fields=["-fecha_inicio", "denominacion"]),
        ]

    def __str__(self):
        return self.denominacion

    @property
    def esta_abierto(self) -> bool:
        return self.estado != self.Estado.FINALIZADO

    @property
    def dias(self) -> int:
        """Duración planificada en días, contando el primero y el último."""
        if not self.fecha_inicio or not self.fecha_fin:
            return 0
        return (self.fecha_fin - self.fecha_inicio).days + 1

    @property
    def zonas(self) -> str:
        """Localidades del operativo en una línea, o el municipio si no hay."""
        nombres = [localidad.nombre for localidad in self.localidades.all()]
        if nombres:
            return ", ".join(nombres)
        return str(self.municipio) if self.municipio_id else ""

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


class Encuesta(SoftDeleteModelMixin, models.Model):
    """Caso relevado: una persona observada dentro de un relevamiento.

    La app la crea en campo con su propio UUID y la sube con upsert idempotente
    (D2.5). El instrumento vive en ``respuestas`` como JSON, con las claves del
    cuestionario; algunas se copian a columnas indexadas para tableros y
    filtros, sin que eso condicione el contrato.
    """

    class Estado(models.TextChoices):
        COMPLETA = "completa", "Completa"
        RECHAZADA = "rechazada", "Rechazada"

    class Origen(models.TextChoices):
        APP = "app", "App"
        BACKOFFICE = "backoffice", "Backoffice"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    relevamiento = models.ForeignKey(
        Relevamiento,
        on_delete=models.CASCADE,
        related_name="encuestas",
    )
    relevador = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="encuestas_datacalle",
    )
    origen = models.CharField(max_length=16, choices=Origen.choices, default=Origen.APP)
    variante = models.CharField(max_length=32, blank=True, default="completo")
    estado = models.CharField(max_length=16, choices=Estado.choices)
    fecha_inicio = models.DateTimeField(null=True, blank=True)
    fecha_hora_fin = models.DateTimeField(null=True, blank=True)
    respuestas = models.JSONField(default=dict, blank=True)

    # Columnas indexadas: copia de `respuestas` al guardar. Ver D2.9.
    grupo_id = models.CharField(max_length=64, blank=True, db_index=True)
    es_cabecera_grupo = models.BooleanField(default=False, db_index=True)
    persona_entrevistada = models.CharField(max_length=64, blank=True)
    personas_observadas = models.PositiveIntegerField(null=True, blank=True)
    realiza_entrevista = models.CharField(max_length=32, blank=True, db_index=True)
    codigo_entrevistado = models.CharField(max_length=64, blank=True, db_index=True)
    lugar_hallazgo = models.CharField(max_length=32, blank=True, db_index=True)
    es_menor_de_edad = models.BooleanField(null=True, blank=True, db_index=True)
    lat = models.FloatField(null=True, blank=True)
    lon = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Caso DataCalle"
        verbose_name_plural = "Casos DataCalle"
        ordering = ["-fecha_inicio", "-created_at"]
        indexes = [
            models.Index(fields=["relevamiento", "estado"]),
            models.Index(fields=["relevamiento", "grupo_id"]),
            # Los listados ordenan por fecha dentro de un operativo. Sin estos
            # índices MySQL hace filesort de filas que arrastran el JSON del
            # instrumento y se queda sin sort buffer (error 1038).
            models.Index(fields=["relevamiento", "-fecha_inicio"]),
            models.Index(fields=["relevamiento", "-updated_at"]),
        ]

    def __str__(self):
        return self.codigo_entrevistado or str(self.id)

    @property
    def sin_entrevista_por_menor(self) -> bool:
        """Separa al menor de edad de quien se negó o no pudo responder (D2.9)."""
        return bool(self.es_menor_de_edad) and not self.realiza_entrevista
