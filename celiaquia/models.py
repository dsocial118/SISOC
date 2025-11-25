from django.contrib.auth import get_user_model
from django.db import models

from ciudadanos.models import Ciudadano
from core.models import Provincia

User = get_user_model()


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


class RevisionTecnico(models.TextChoices):
    PENDIENTE = "PENDIENTE", "Pendiente"
    APROBADO = "APROBADO", "Aprobado por el tecnico"
    RECHAZADO = "RECHAZADO", "Rechazado por el tecnico"
    SUBSANAR = "SUBSANAR", "Subsanar"
    SUBSANADO = "SUBSANADO", "Subsanado"


class ResultadoSintys(models.TextChoices):
    SIN_CRUCE = "SIN_CRUCE", "Sin cruce"
    MATCH = "MATCH", "Matcheado"
    NO_MATCH = "NO_MATCH", "No matcheado"


class EstadoCupo(models.TextChoices):
    NO_EVAL = "NO_EVAL", "No evaluado"
    DENTRO = "DENTRO", "Dentro de cupo"
    FUERA = "FUERA", "Fuera de cupo"


class TipoMovimientoCupo(models.TextChoices):
    ALTA = "ALTA", "Alta"
    REACTIVACION = "REACTIVACION", "Reactivacion"
    BAJA = "BAJA", "Baja"
    AJUSTE = "AJUSTE", "Ajuste"
    SUSPENDIDO = "SUSPENDIDO", "Suspendido"


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
    numero_expediente = models.CharField(max_length=100, blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    excel_masivo = models.FileField(
        upload_to="expedientes/masivos/", null=True, blank=True
    )
    cruce_excel = models.FileField(
        upload_to="expedientes/cruces/", null=True, blank=True
    )
    documento = models.FileField(upload_to="expedientes/prd/", null=True, blank=True)

    class Meta:
        verbose_name = "Expediente"
        verbose_name_plural = "Expedientes"
        ordering = ("-fecha_creacion", "pk")
        indexes = [
            models.Index(
                fields=["usuario_provincia", "estado"], name="exp_prov_est_idx"
            ),
            models.Index(fields=["estado", "fecha_creacion"], name="exp_est_fecha_idx"),
            models.Index(
                fields=["usuario_provincia", "fecha_creacion"],
                name="exp_prov_fecha_idx",
            ),
            models.Index(fields=["fecha_creacion"], name="exp_fecha_idx"),
        ]

    def __str__(self):
        return f"{self.usuario_provincia.username}"

    @property
    def provincia(self):
        try:
            return self.usuario_provincia.profile.provincia
        except Exception:
            return None


class ExpedienteEstadoHistorial(models.Model):
    """Historial de cambios de estado para un expediente."""

    expediente = models.ForeignKey(
        "Expediente", on_delete=models.CASCADE, related_name="historial"
    )
    estado_anterior = models.ForeignKey(
        EstadoExpediente, on_delete=models.PROTECT, related_name="+"
    )
    estado_nuevo = models.ForeignKey(
        EstadoExpediente, on_delete=models.PROTECT, related_name="+"
    )
    usuario = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="cambios_estado",
    )
    fecha = models.DateTimeField(auto_now_add=True)
    observaciones = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "Historial de estado"
        verbose_name_plural = "Historial de estados"
        ordering = ("-fecha",)

    def __str__(self):
        return f"{self.expediente_id} {self.estado_anterior} -> {self.estado_nuevo}"


class ExpedienteCiudadano(models.Model):
    # Roles en minúsculas según requerimiento funcional.
    ROLE_BENEFICIARIO = "beneficiario"
    ROLE_RESPONSABLE = "responsable"
    ROLE_BENEFICIARIO_Y_RESPONSABLE = "beneficiario_y_responsable"
    
    ROLE_CHOICES = [
        (ROLE_BENEFICIARIO, "Solo Beneficiario"),
        (ROLE_RESPONSABLE, "Solo Responsable"),
        (ROLE_BENEFICIARIO_Y_RESPONSABLE, "Beneficiario y Responsable"),
    ]
    
    expediente = models.ForeignKey(
        Expediente, on_delete=models.CASCADE, related_name="expediente_ciudadanos"
    )
    ciudadano = models.ForeignKey(
        Ciudadano, on_delete=models.PROTECT, related_name="expedientes"
    )
    estado = models.ForeignKey(
        EstadoLegajo, on_delete=models.PROTECT, related_name="expediente_ciudadanos"
    )
    archivo1 = models.FileField(upload_to="legajos/archivos/", null=True, blank=True)
    archivo2 = models.FileField(upload_to="legajos/archivos/", null=True, blank=True)
    archivo3 = models.FileField(upload_to="legajos/archivos/", null=True, blank=True)
    archivos_ok = models.BooleanField(default=False, db_index=True)
    cruce_ok = models.BooleanField(null=True, blank=True)
    observacion_cruce = models.CharField(max_length=255, null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    modificado_en = models.DateTimeField(auto_now=True)
    revision_tecnico = models.CharField(
        max_length=24,
        choices=RevisionTecnico.choices,
        default=RevisionTecnico.PENDIENTE,
    )
    resultado_sintys = models.CharField(
        max_length=10,
        choices=ResultadoSintys.choices,
        default=ResultadoSintys.SIN_CRUCE,
    )
    estado_cupo = models.CharField(
        max_length=8, choices=EstadoCupo.choices, default=EstadoCupo.NO_EVAL
    )
    es_titular_activo = models.BooleanField(default=False)
    subsanacion_motivo = models.TextField(null=True, blank=True)
    subsanacion_solicitada_en = models.DateTimeField(null=True, blank=True)
    subsanacion_enviada_en = models.DateTimeField(null=True, blank=True)
    subsanacion_usuario = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="subsanaciones_realizadas",
    )
    estado_validacion_renaper = models.IntegerField(
        default=0,
        db_index=True,
        help_text="0=no validado, 1=aceptado, 2=rechazado, 3=subsanar",
    )
    subsanacion_renaper_comentario = models.TextField(
        null=True, blank=True, help_text="Comentario de respuesta a subsanación Renaper"
    )
    subsanacion_renaper_archivo = models.FileField(
        upload_to="legajos/subsanacion_renaper/",
        null=True,
        blank=True,
        help_text="Archivo de respuesta a subsanación Renaper",
    )
    rol = models.CharField(
        max_length=50,
        choices=ROLE_CHOICES,
        default=ROLE_BENEFICIARIO,
        db_index=True
    )

    class Meta:
        unique_together = ("expediente", "ciudadano")
        verbose_name = "Expediente Ciudadano"
        verbose_name_plural = "Expedientes Ciudadano"
        ordering = ("-creado_en", "pk")
        indexes = [
            models.Index(
                fields=["expediente", "revision_tecnico"], name="leg_exp_rev_idx"
            ),
            models.Index(fields=["expediente", "estado"], name="leg_exp_est_idx"),
            models.Index(fields=["expediente", "estado_cupo"], name="leg_exp_cupo_idx"),
            models.Index(
                fields=["expediente", "resultado_sintys"], name="leg_exp_sin_idx"
            ),
            models.Index(
                fields=["expediente", "es_titular_activo"], name="leg_exp_tit_idx"
            ),
            models.Index(fields=["creado_en"], name="leg_creado_idx"),
            models.Index(fields=["ciudadano"], name="leg_ciud_idx"),
            models.Index(
                fields=["estado_cupo", "es_titular_activo"], name="leg_cupo_activo_idx"
            ),
            models.Index(
                fields=["revision_tecnico", "resultado_sintys"],
                name="leg_rev_sintys_idx",
            ),
        ]

    def _recompute_archivos_ok(self):
        self.archivos_ok = bool(self.archivo2 and self.archivo3)

    def save(self, *args, **kwargs):
        self._recompute_archivos_ok()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ciudadano.documento} - {self.ciudadano.nombre} {self.ciudadano.apellido}"

    def tiene_dos_archivos(self) -> bool:
        return bool(self.archivo2 and self.archivo3)

    def faltantes_archivos(self):
        faltan = []
        if not self.archivo2:
            faltan.append("archivo2")
        if not self.archivo3:
            faltan.append("archivo3")
        return faltan


class AsignacionTecnico(models.Model):
    expediente = models.ForeignKey(
        Expediente, on_delete=models.CASCADE, related_name="asignaciones_tecnicos"
    )
    tecnico = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="expedientes_asignados"
    )
    fecha_asignacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Asignación de Técnico"
        verbose_name_plural = "Asignaciones de Técnico"
        unique_together = ("expediente", "tecnico")
        indexes = [
            models.Index(fields=["tecnico"], name="asig_tecnico_idx"),
            models.Index(fields=["expediente"], name="asig_expediente_idx"),
        ]

    def __str__(self):
        return f"{self.tecnico.username} - {self.expediente.id}"


class ProvinciaCupo(models.Model):
    provincia = models.OneToOneField(
        Provincia, on_delete=models.CASCADE, related_name="cupo"
    )
    total_asignado = models.PositiveIntegerField(default=0)
    usados = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Cupo por Provincia"
        verbose_name_plural = "Cupos por Provincia"

    def __str__(self):
        return f"{self.provincia} ({self.usados}/{self.total_asignado})"


class CupoMovimiento(models.Model):
    provincia = models.ForeignKey(
        Provincia, on_delete=models.CASCADE, related_name="movimientos_cupo"
    )
    expediente = models.ForeignKey(
        Expediente,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="movimientos_cupo",
    )
    legajo = models.ForeignKey(
        ExpedienteCiudadano,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="movimientos_cupo",
    )
    tipo = models.CharField(max_length=20, choices=TipoMovimientoCupo.choices)
    delta = models.IntegerField()
    motivo = models.CharField(max_length=255, blank=True)
    usuario = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="movimientos_cupo",
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Movimiento de Cupo"
        verbose_name_plural = "Movimientos de Cupo"
        ordering = ("-creado_en", "pk")
        indexes = [
            models.Index(
                fields=["provincia", "-creado_en"], name="cupo_prov_fecha_idx"
            ),
            models.Index(
                fields=["expediente", "-creado_en"], name="cupo_exp_fecha_idx"
            ),
            models.Index(fields=["legajo", "-creado_en"], name="cupo_leg_fecha_idx"),
            models.Index(
                fields=["tipo", "provincia", "-creado_en"], name="cupo_tipo_prov_idx"
            ),
        ]

    def __str__(self):
        return f"{self.provincia} {self.tipo} {self.delta} ({self.creado_en:%Y-%m-%d %H:%M})"


class PagoEstado(models.TextChoices):
    BORRADOR = "BORRADOR", "Borrador"
    ENVIADO = "ENVIADO", "Enviado a Sintys"
    PROCESADO = "PROCESADO", "Cruce procesado"
    CERRADO = "CERRADO", "Cerrado"


class PagoExpediente(models.Model):
    provincia = models.ForeignKey(
        Provincia, on_delete=models.PROTECT, related_name="pagos_expedientes"
    )
    periodo = models.CharField(max_length=7, help_text="YYYY-MM", db_index=True)
    estado = models.CharField(
        max_length=12, choices=PagoEstado.choices, default=PagoEstado.BORRADOR
    )

    archivo_envio = models.FileField(upload_to="pagos/envios/", null=True, blank=True)
    archivo_respuesta = models.FileField(
        upload_to="pagos/respuestas/", null=True, blank=True
    )

    total_candidatos = models.PositiveIntegerField(default=0)
    total_validados = models.PositiveIntegerField(default=0)
    total_excluidos = models.PositiveIntegerField(default=0)

    creado_por = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="pagos_creados"
    )
    modificado_por = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="pagos_modificados",
    )

    creado_en = models.DateTimeField(auto_now_add=True)
    modificado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Expediente de Pago"
        verbose_name_plural = "Expedientes de Pago"
        ordering = ("-creado_en", "pk")
        indexes = [
            models.Index(
                fields=["provincia", "periodo", "estado"],
                name="pago_prov_per_estado_idx",
            ),
        ]

    def __str__(self):
        return f"Pago {self.provincia} {self.periodo} ({self.estado})"


class PagoNominaEstado(models.TextChoices):
    VALIDADO = "VALIDADO", "Validado para pago"
    EXCLUIDO = "EXCLUIDO", "Excluido por cruce"


class PagoNomina(models.Model):
    pago = models.ForeignKey(
        PagoExpediente, on_delete=models.CASCADE, related_name="nomina"
    )
    legajo = models.ForeignKey(
        ExpedienteCiudadano, on_delete=models.PROTECT, related_name="pagos"
    )
    documento = models.CharField(max_length=16, db_index=True)
    nombre = models.CharField(max_length=80, blank=True)
    apellido = models.CharField(max_length=80, blank=True)
    estado = models.CharField(
        max_length=12,
        choices=PagoNominaEstado.choices,
        default=PagoNominaEstado.VALIDADO,
    )
    observacion = models.CharField(max_length=255, blank=True)

    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Fila nómina de pago"
        verbose_name_plural = "Nómina de pago"
        unique_together = ("pago", "legajo")
        indexes = [
            models.Index(fields=["pago", "estado"], name="pago_nomina_estado_idx"),
            models.Index(fields=["documento"], name="pago_nomina_doc_idx"),
        ]

    def __str__(self):
        return f"{self.documento} - {self.nombre} {self.apellido} ({self.estado})"


class RegistroErroneo(models.Model):
    expediente = models.ForeignKey(
        Expediente, on_delete=models.CASCADE, related_name="registros_erroneos"
    )
    fila_excel = models.PositiveIntegerField()
    datos_raw = models.JSONField()
    campo_error = models.CharField(max_length=100, blank=True)
    mensaje_error = models.TextField()
    procesado = models.BooleanField(default=False, db_index=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    procesado_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Registro Erróneo"
        verbose_name_plural = "Registros Erróneos"
        ordering = ("fila_excel",)
        indexes = [
            models.Index(
                fields=["expediente", "procesado"], name="reg_err_exp_proc_idx"
            ),
        ]

    def __str__(self):
        return f"Fila {self.fila_excel} - {self.mensaje_error[:50]}"
