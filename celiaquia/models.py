from django.db import models
from django.contrib.auth import get_user_model
from ciudadanos.models import Ciudadano, Provincia

User = get_user_model()


# =========================
# Enumeraciones (TextChoices)
# =========================

class RevisionTecnico(models.TextChoices):
    PENDIENTE = "PENDIENTE", "Pendiente"
    APROBADO  = "APROBADO", "Aprobado por técnico"
    RECHAZADO = "RECHAZADO", "Rechazado por técnico"


class ResultadoSintys(models.TextChoices):
    SIN_CRUCE = "SIN_CRUCE", "Sin cruce"
    MATCH     = "MATCH", "Matcheado"
    NO_MATCH  = "NO_MATCH", "No matcheado"


class EstadoCupo(models.TextChoices):
    NO_EVAL = "NO_EVAL", "No evaluado"
    DENTRO  = "DENTRO", "Dentro de cupo"
    FUERA   = "FUERA", "Fuera de cupo"


class TipoMovimientoCupo(models.TextChoices):
    ALTA   = "ALTA", "Alta (consumo de cupo)"
    BAJA   = "BAJA", "Baja (liberación de cupo)"
    AJUSTE = "AJUSTE", "Ajuste manual"


# =========================
# Catálogos básicos
# =========================

class EstadoExpediente(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = "Estado del Expediente"
        verbose_name_plural = "Estados del Expediente"

    def __str__(self):
        return self.nombre

    def display_name(self):
        return self.nombre.replace("_", " ").capitalize()


class EstadoLegajo(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = "Estado del Legajo"
        verbose_name_plural = "Estados del Legajo"

    def __str__(self):
        return self.nombre


class Organismo(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Organismo de Cruce"
        verbose_name_plural = "Organismos de Cruce"

    def __str__(self):
        return self.nombre


class TipoCruce(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = "Tipo de Cruce"
        verbose_name_plural = "Tipos de Cruce"

    def __str__(self):
        return self.nombre


# =========================
# Expediente
# =========================

class Expediente(models.Model):
    usuario_provincia = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="expedientes_creados"
    )
    usuario_modificador = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="expedientes_modificados",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    estado = models.ForeignKey(
        EstadoExpediente, on_delete=models.PROTECT, related_name="expedientes"
    )
    observaciones = models.TextField(blank=True, null=True)

    excel_masivo = models.FileField(
        upload_to="expedientes/masivos/", null=True, blank=True
    )
    cruce_excel = models.FileField(
        upload_to="expedientes/cruces/", null=True, blank=True
    )
    documento = models.FileField(
        upload_to="expedientes/prd/", null=True, blank=True
    )

    class Meta:
        verbose_name = "Expediente"
        verbose_name_plural = "Expedientes"

    def __str__(self):
        return f"{self.codigo} - {self.usuario_provincia.username}"

    # Helpers (compatibilidad con templates)
    @property
    def codigo(self) -> str:
        return f"EXP-{self.pk:06d}" if self.pk else "EXP--"

    @property
    def provincia(self):
        try:
            return self.usuario_provincia.profile.provincia
        except Exception:
            return None


class ExpedienteCiudadano(models.Model):
    expediente = models.ForeignKey(
        Expediente, on_delete=models.CASCADE, related_name="expediente_ciudadanos"
    )
    ciudadano = models.ForeignKey(
        Ciudadano, on_delete=models.PROTECT, related_name="expedientes"
    )
    estado = models.ForeignKey(
        EstadoLegajo, on_delete=models.PROTECT, related_name="expediente_ciudadanos"
    )
    archivo = models.FileField(upload_to="legajos/archivos/", null=True, blank=True)

    cruce_ok = models.BooleanField(null=True, blank=True)
    observacion_cruce = models.CharField(max_length=255, null=True, blank=True)

    creado_en = models.DateTimeField(auto_now_add=True)
    modificado_en = models.DateTimeField(auto_now=True)

    revision_tecnico = models.CharField(
        max_length=10, choices=RevisionTecnico.choices, default=RevisionTecnico.PENDIENTE
    )
    resultado_sintys = models.CharField(
        max_length=10, choices=ResultadoSintys.choices, default=ResultadoSintys.SIN_CRUCE
    )

    # Cupo por provincia
    estado_cupo = models.CharField(
        max_length=8, choices=EstadoCupo.choices, default=EstadoCupo.NO_EVAL
    )
    es_titular_activo = models.BooleanField(default=True)

    class Meta:
        unique_together = ("expediente", "ciudadano")
        verbose_name = "Expediente Ciudadano"
        verbose_name_plural = "Expedientes Ciudadano"
        indexes = [
            models.Index(fields=["expediente", "estado_cupo"]),
            models.Index(fields=["revision_tecnico", "resultado_sintys"]),
        ]

    def __str__(self):
        return f"{self.ciudadano.documento} - {self.ciudadano.nombre} {self.ciudadano.apellido}"


class AsignacionTecnico(models.Model):
    expediente = models.OneToOneField(
        Expediente, on_delete=models.CASCADE, related_name="asignacion_tecnico"
    )
    tecnico = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="expedientes_asignados"
    )
    fecha_asignacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Asignación de Técnico"
        verbose_name_plural = "Asignaciones de Técnico"

    def __str__(self):
        return f"{self.expediente.codigo} -> {self.tecnico.username}"


# =========================
# Cupo por provincia
# =========================

class ProvinciaCupo(models.Model):
    provincia = models.OneToOneField(
        Provincia, on_delete=models.PROTECT, related_name="cupo_provincia"
    )
    total_asignado = models.PositiveIntegerField(default=0)
    usados = models.PositiveIntegerField(default=0)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cupo de Provincia"
        verbose_name_plural = "Cupos de Provincia"

    def __str__(self):
        return f"Cupo {self.provincia} ({self.usados}/{self.total_asignado})"

    @property
    def disponibles(self) -> int:
        val = int(self.total_asignado) - int(self.usados)
        return val if val > 0 else 0


class CupoMovimiento(models.Model):
    provincia = models.ForeignKey(
        Provincia, on_delete=models.PROTECT, related_name="movimientos_cupo"
    )
    expediente = models.ForeignKey(
        Expediente, on_delete=models.SET_NULL, null=True, blank=True, related_name="movimientos_cupo"
    )
    legajo = models.ForeignKey(
        ExpedienteCiudadano, on_delete=models.SET_NULL, null=True, blank=True, related_name="movimientos_cupo"
    )
    tipo = models.CharField(max_length=10, choices=TipoMovimientoCupo.choices)
    delta = models.SmallIntegerField(default=0)
    motivo = models.CharField(max_length=255, blank=True)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, related_name="movimientos_cupo_creados")
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Movimiento de Cupo"
        verbose_name_plural = "Movimientos de Cupo"
        ordering = ["-creado_en"]
        indexes = [
            models.Index(fields=["provincia", "creado_en"]),
            models.Index(fields=["tipo"]),
        ]

    def __str__(self):
        who = f"legajo #{self.legajo_id}" if self.legajo_id else f"expediente #{self.expediente_id}"
        return f"[{self.creado_en:%Y-%m-%d %H:%M}] {self.provincia} {self.tipo} {self.delta:+d} ({who})"
