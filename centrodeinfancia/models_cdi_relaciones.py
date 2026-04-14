from django.db import models
from django.utils import timezone

from centrodeinfancia.formulario_cdi_schema import (
    OPCIONES_INSTITUCIONES_ARTICULACION,
    OPCIONES_GRUPO_ETARIO_DEMANDA,
    OPCIONES_GRUPO_ETARIO_SALAS,
)
from core.soft_delete import SoftDeleteModelMixin


class IntervencionCentroInfancia(SoftDeleteModelMixin, models.Model):
    centro = models.ForeignKey(
        "centrodeinfancia.CentroDeInfancia",
        on_delete=models.CASCADE,
        related_name="intervenciones",
    )
    tipo_intervencion = models.ForeignKey(
        "intervenciones.TipoIntervencion",
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Tipo de intervención",
    )
    subintervencion = models.ForeignKey(
        "intervenciones.SubIntervencion",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Sub-tipo de intervención",
    )
    destinatario = models.ForeignKey(
        "intervenciones.TipoDestinatario",
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Destinatario",
    )
    forma_contacto = models.ForeignKey(
        "intervenciones.TipoContacto",
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Forma de contacto",
    )
    fecha = models.DateTimeField(default=timezone.now)
    observaciones = models.TextField(blank=True, null=True)
    tiene_documentacion = models.BooleanField(default=False)
    documentacion = models.FileField(upload_to="documentacion/", blank=True, null=True)
    creado_por = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Creado por",
    )

    class Meta:
        verbose_name = "Intervención Centro de Desarrollo Infantil"
        verbose_name_plural = "Intervenciones Centro de Desarrollo Infantil"
        ordering = ["-fecha"]

    def __str__(self):
        fecha = self.fecha.strftime("%Y-%m-%d") if self.fecha else "sin fecha"
        return f"Intervención en {self.centro} - {fecha}"


class ObservacionCentroInfancia(SoftDeleteModelMixin, models.Model):
    observador = models.CharField(max_length=255, blank=True)
    centro = models.ForeignKey(
        to="centrodeinfancia.CentroDeInfancia",
        on_delete=models.CASCADE,
        related_name="observaciones",
    )
    fecha_visita = models.DateTimeField(default=timezone.now, blank=True)
    observacion = models.TextField()

    class Meta:
        indexes = [
            models.Index(fields=["centro"]),
        ]
        verbose_name = "Observación Centro de Desarrollo Infantil"
        verbose_name_plural = "Observaciones Centro de Desarrollo Infantil"

    def __str__(self):
        centro = self.centro.nombre if self.centro else "Centro sin nombre"
        fecha = self.fecha_visita.date() if self.fecha_visita else "sin fecha"
        return f"Observación {fecha} - {centro}"


class FormularioCDIRoomDistribution(SoftDeleteModelMixin, models.Model):
    formulario = models.ForeignKey(
        "centrodeinfancia.FormularioCDI",
        on_delete=models.CASCADE,
        related_name="filas_distribucion_salas",
    )
    grupo_etario = models.CharField(max_length=32, choices=OPCIONES_GRUPO_ETARIO_SALAS)
    cantidad_salas = models.PositiveIntegerField(blank=True, null=True)
    superficie_exclusiva_m2 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
    )
    cantidad_ninos = models.PositiveIntegerField(blank=True, null=True)
    cantidad_personal_sala = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        verbose_name = "Formulario CDI - Distribucion de salas"
        verbose_name_plural = "Formulario CDI - Distribucion de salas"
        constraints = [
            models.UniqueConstraint(
                fields=["formulario", "grupo_etario"],
                name="uniq_formulario_cdi_distribucion_salas_grupo_etario",
            )
        ]

    @property
    def personal_por_sala(self):
        if not self.cantidad_salas:
            return None
        if self.cantidad_personal_sala is None:
            return None
        return self.cantidad_personal_sala / self.cantidad_salas


class FormularioCDIWaitlistByAgeGroup(SoftDeleteModelMixin, models.Model):
    formulario = models.ForeignKey(
        "centrodeinfancia.FormularioCDI",
        on_delete=models.CASCADE,
        related_name="filas_demanda_insatisfecha",
    )
    grupo_etario = models.CharField(
        max_length=32, choices=OPCIONES_GRUPO_ETARIO_DEMANDA
    )
    cantidad_demanda_insatisfecha = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        verbose_name = "Formulario CDI - Lista de espera"
        verbose_name_plural = "Formulario CDI - Lista de espera"
        constraints = [
            models.UniqueConstraint(
                fields=["formulario", "grupo_etario"],
                name="uniq_formulario_cdi_waitlist_grupo_etario",
            )
        ]


class FormularioCDIArticulationFrequency(SoftDeleteModelMixin, models.Model):
    formulario = models.ForeignKey(
        "centrodeinfancia.FormularioCDI",
        on_delete=models.CASCADE,
        related_name="filas_articulacion",
    )
    tipo_institucion = models.CharField(
        max_length=64,
        choices=OPCIONES_INSTITUCIONES_ARTICULACION,
    )
    frecuencia = models.CharField(
        max_length=32,
        choices=[
            ("trimestral", "Trimestral"),
            ("semestral", "Semestral"),
            ("anual", "Anual"),
            ("no_se_articula", "No se articula"),
        ],
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "Formulario CDI - Articulacion institucional"
        verbose_name_plural = "Formulario CDI - Articulacion institucional"
        constraints = [
            models.UniqueConstraint(
                fields=["formulario", "tipo_institucion"],
                name="uniq_formulario_cdi_articulacion_tipo_institucion",
            )
        ]
