from django.contrib.auth import get_user_model
from django.db import models

from ciudadanos.models import Ciudadano
from core.models import Provincia
from core.soft_delete import SoftDeleteModelMixin

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
        indexes = [
            models.Index(
                fields=["expediente", "-fecha"], name="exp_hist_exp_fecha_idx"
            ),
        ]

    def __str__(self):
        return f"{self.expediente_id} {self.estado_anterior} -> {self.estado_nuevo}"


class ExpedienteCiudadano(SoftDeleteModelMixin, models.Model):
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
        max_length=50, choices=ROLE_CHOICES, default=ROLE_BENEFICIARIO, db_index=True
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
            models.Index(
                fields=["estado_cupo", "es_titular_activo", "rol"],
                name="leg_cupo_activo_rol_idx",
            ),
        ]

    def _recompute_archivos_ok(self):
        """Calcula archivos_ok basado en documentos requeridos."""
        # Usar nuevo sistema si está disponible
        if hasattr(self, "documentos"):
            try:
                tipos_requeridos = TipoDocumento.objects.filter(
                    requerido=True, activo=True
                ).count()
                documentos_cargados = self.documentos.filter(
                    tipo_documento__requerido=True, tipo_documento__activo=True
                ).count()
                self.archivos_ok = documentos_cargados >= tipos_requeridos
            except:
                # Fallback al sistema anterior
                self.archivos_ok = bool(self.archivo2 and self.archivo3)
        else:
            # Sistema anterior
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

    def agregar_comentario(
        self, tipo_comentario, comentario, usuario=None, archivo_adjunto=None
    ):
        """Helper para agregar comentarios al historial."""
        from .services.comentarios_service import ComentariosService

        return ComentariosService.agregar_comentario(
            legajo=self,
            tipo_comentario=tipo_comentario,
            comentario=comentario,
            usuario=usuario,
            archivo_adjunto=archivo_adjunto,
        )

    @property
    def ultimo_comentario(self):
        """Obtiene el último comentario del legajo."""
        return self.historial_comentarios.first()  # pylint: disable=no-member

    @property
    def comentarios_subsanacion(self):
        """Obtiene comentarios de subsanación."""
        return HistorialComentarios.objects.filter(
            legajo=self,
            tipo_comentario__in=[
                HistorialComentarios.TIPO_SUBSANACION_MOTIVO,
                HistorialComentarios.TIPO_SUBSANACION_RESPUESTA,
            ],
        )

    def tiene_documento(self, tipo_documento_nombre):
        """Verifica si tiene un documento específico."""
        return self.documentos.filter(
            tipo_documento__nombre=tipo_documento_nombre
        ).exists()

    def obtener_documento(self, tipo_documento_nombre):
        """Obtiene un documento específico."""
        try:
            return self.documentos.get(tipo_documento__nombre=tipo_documento_nombre)
        except DocumentoLegajo.DoesNotExist:
            return None

    @property
    def documentos_completos(self):
        """Verifica si tiene todos los documentos requeridos."""
        tipos_requeridos = TipoDocumento.objects.filter(
            requerido=True, activo=True
        ).count()
        documentos_cargados = self.documentos.filter(
            tipo_documento__requerido=True, tipo_documento__activo=True
        ).count()
        return tipos_requeridos == documentos_cargados

    def documentos_faltantes(self):
        """Lista los tipos de documentos faltantes."""
        tipos_requeridos = TipoDocumento.objects.filter(requerido=True, activo=True)
        tipos_cargados = self.documentos.values_list("tipo_documento_id", flat=True)
        return tipos_requeridos.exclude(id__in=tipos_cargados)


class AsignacionTecnico(SoftDeleteModelMixin, models.Model):
    expediente = models.ForeignKey(
        Expediente, on_delete=models.CASCADE, related_name="asignaciones_tecnicos"
    )
    tecnico = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="expedientes_asignados"
    )
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    activa = models.BooleanField(
        default=True, help_text="Indica si la asignación está activa"
    )

    class Meta:
        verbose_name = "Asignación de Técnico"
        verbose_name_plural = "Asignaciones de Técnico"
        unique_together = ("expediente", "tecnico")
        indexes = [
            models.Index(fields=["tecnico", "activa"], name="asig_tecnico_activa_idx"),
            models.Index(
                fields=["expediente", "activa"], name="asig_expediente_activa_idx"
            ),
        ]

    def __str__(self):
        return f"{self.tecnico.username} - {self.expediente.id} ({'Activa' if self.activa else 'Inactiva'})"


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


class RegistroErroneo(SoftDeleteModelMixin, models.Model):
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


class ValidacionTecnica(models.Model):
    legajo = models.OneToOneField(
        ExpedienteCiudadano, on_delete=models.CASCADE, related_name="validacion_tecnica"
    )
    revision_tecnico = models.CharField(
        max_length=24,
        choices=RevisionTecnico.choices,
        default=RevisionTecnico.PENDIENTE,
    )
    subsanacion_motivo = models.TextField(null=True, blank=True)
    subsanacion_solicitada_en = models.DateTimeField(null=True, blank=True)
    subsanacion_enviada_en = models.DateTimeField(null=True, blank=True)
    subsanacion_usuario = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="validaciones_tecnicas",
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    modificado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Validación Técnica"
        verbose_name_plural = "Validaciones Técnicas"

    def __str__(self):
        return f"{self.legajo} - {self.revision_tecnico}"


class CruceResultado(models.Model):
    legajo = models.OneToOneField(
        ExpedienteCiudadano, on_delete=models.CASCADE, related_name="cruce_resultado"
    )
    resultado_sintys = models.CharField(
        max_length=10,
        choices=ResultadoSintys.choices,
        default=ResultadoSintys.SIN_CRUCE,
    )
    cruce_ok = models.BooleanField(null=True, blank=True)
    observacion_cruce = models.CharField(max_length=255, null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    modificado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Resultado de Cruce"
        verbose_name_plural = "Resultados de Cruce"

    def __str__(self):
        return f"{self.legajo} - {self.resultado_sintys}"


class CupoTitular(models.Model):
    legajo = models.OneToOneField(
        ExpedienteCiudadano, on_delete=models.CASCADE, related_name="cupo_titular"
    )
    estado_cupo = models.CharField(
        max_length=8, choices=EstadoCupo.choices, default=EstadoCupo.NO_EVAL
    )
    es_titular_activo = models.BooleanField(default=False)
    creado_en = models.DateTimeField(auto_now_add=True)
    modificado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cupo Titular"
        verbose_name_plural = "Cupos Titulares"
        indexes = [
            models.Index(fields=["estado_cupo", "es_titular_activo"]),
        ]

    def __str__(self):
        return f"{self.legajo} - {self.estado_cupo}"


class ValidacionRenaper(models.Model):
    legajo = models.OneToOneField(
        ExpedienteCiudadano, on_delete=models.CASCADE, related_name="validacion_renaper"
    )
    estado_validacion = models.IntegerField(
        default=0,
        choices=[
            (0, "No validado"),
            (1, "Aceptado"),
            (2, "Rechazado"),
            (3, "Subsanar"),
        ],
    )
    comentario = models.TextField(null=True, blank=True)
    archivo = models.FileField(
        upload_to="legajos/subsanacion_renaper/", null=True, blank=True
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    modificado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Validación Renaper"
        verbose_name_plural = "Validaciones Renaper"

    def __str__(self):
        return f"{self.legajo} - Estado {self.estado_validacion}"


class HistorialValidacionTecnica(models.Model):
    legajo = models.ForeignKey(
        ExpedienteCiudadano,
        on_delete=models.CASCADE,
        related_name="historial_validacion_tecnica",
    )
    estado_anterior = models.CharField(
        max_length=24, choices=RevisionTecnico.choices, null=True, blank=True
    )
    estado_nuevo = models.CharField(max_length=24, choices=RevisionTecnico.choices)
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cambios_validacion_tecnica",
    )
    motivo = models.TextField(null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Historial Validación Técnica"
        verbose_name_plural = "Historiales Validación Técnica"
        ordering = ("-creado_en",)
        indexes = [
            models.Index(fields=["legajo", "-creado_en"]),
        ]

    def __str__(self):
        return f"{self.legajo} - {self.estado_anterior} → {self.estado_nuevo}"


class HistorialCupo(models.Model):
    legajo = models.ForeignKey(
        ExpedienteCiudadano, on_delete=models.CASCADE, related_name="historial_cupo"
    )
    estado_cupo_anterior = models.CharField(
        max_length=8, choices=EstadoCupo.choices, null=True, blank=True
    )
    estado_cupo_nuevo = models.CharField(max_length=8, choices=EstadoCupo.choices)
    es_titular_activo_anterior = models.BooleanField(null=True, blank=True)
    es_titular_activo_nuevo = models.BooleanField()
    tipo_movimiento = models.CharField(
        max_length=20, choices=TipoMovimientoCupo.choices
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cambios_cupo",
    )
    motivo = models.TextField(null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Historial Cupo"
        verbose_name_plural = "Historiales Cupo"
        ordering = ("-creado_en",)
        indexes = [
            models.Index(fields=["legajo", "-creado_en"]),
            models.Index(fields=["tipo_movimiento", "-creado_en"]),
        ]

    def __str__(self):
        return f"{self.legajo} - {self.tipo_movimiento}"


class SubsanacionRespuesta(models.Model):
    legajo = models.ForeignKey(
        ExpedienteCiudadano,
        on_delete=models.CASCADE,
        related_name="subsanaciones_respuestas",
    )
    validacion_tecnica = models.ForeignKey(
        ValidacionTecnica, on_delete=models.CASCADE, related_name="respuestas"
    )
    archivo1 = models.FileField(
        upload_to="legajos/subsanacion_respuesta/", null=True, blank=True
    )
    archivo2 = models.FileField(
        upload_to="legajos/subsanacion_respuesta/", null=True, blank=True
    )
    archivo3 = models.FileField(
        upload_to="legajos/subsanacion_respuesta/", null=True, blank=True
    )
    comentario = models.TextField(null=True, blank=True)
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subsanaciones_respondidas",
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Respuesta de Subsanación"
        verbose_name_plural = "Respuestas de Subsanación"
        ordering = ("-creado_en",)
        indexes = [
            models.Index(fields=["legajo", "-creado_en"]),
            models.Index(fields=["validacion_tecnica"]),
        ]

    def __str__(self):
        return f"{self.legajo} - Respuesta #{self.pk}"


class RegistroErroneoReprocesado(models.Model):
    RESULTADO_CHOICES = [
        ("EXITOSO", "Exitoso"),
        ("FALLIDO", "Fallido"),
    ]

    registro_erroneo = models.ForeignKey(
        RegistroErroneo, on_delete=models.CASCADE, related_name="reprocesados"
    )
    intento_numero = models.PositiveIntegerField()
    resultado = models.CharField(max_length=10, choices=RESULTADO_CHOICES)
    ciudadano_creado = models.ForeignKey(
        Ciudadano, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    legajo_creado = models.ForeignKey(
        ExpedienteCiudadano,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    error_mensaje = models.TextField(null=True, blank=True)
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reprocesados",
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Registro Erróneo Reprocesado"
        verbose_name_plural = "Registros Erróneos Reprocesados"
        ordering = ("-creado_en",)
        unique_together = ("registro_erroneo", "intento_numero")
        indexes = [
            models.Index(fields=["registro_erroneo", "-creado_en"]),
            models.Index(fields=["resultado"]),
        ]

    def __str__(self):
        return f"Fila {self.registro_erroneo.fila_excel} - Intento {self.intento_numero} - {self.resultado}"


class TipoDocumento(models.Model):
    """Tipos de documentos requeridos para los legajos."""

    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    requerido = models.BooleanField(default=True)
    orden = models.PositiveIntegerField(default=0, help_text="Orden de presentación")
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Tipo de Documento"
        verbose_name_plural = "Tipos de Documento"
        ordering = ["orden", "nombre"]

    def __str__(self):
        return self.nombre


class DocumentoLegajo(models.Model):
    """Documentos específicos asociados a un legajo."""

    legajo = models.ForeignKey(
        ExpedienteCiudadano, on_delete=models.CASCADE, related_name="documentos"
    )
    tipo_documento = models.ForeignKey(
        TipoDocumento, on_delete=models.PROTECT, related_name="documentos_legajo"
    )
    archivo = models.FileField(upload_to="legajos/documentos/")
    fecha_carga = models.DateTimeField(auto_now_add=True)
    usuario_carga = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documentos_cargados",
    )
    observaciones = models.TextField(blank=True)

    class Meta:
        verbose_name = "Documento de Legajo"
        verbose_name_plural = "Documentos de Legajo"
        unique_together = ("legajo", "tipo_documento")
        ordering = ["-fecha_carga"]
        indexes = [
            models.Index(fields=["legajo", "tipo_documento"]),
            models.Index(fields=["fecha_carga"]),
        ]

    def __str__(self):
        return f"{self.legajo} - {self.tipo_documento.nombre}"


class HistorialComentarios(models.Model):
    """Historial completo de comentarios y subsanaciones por legajo."""

    TIPO_VALIDACION_TECNICA = "VALIDACION_TECNICA"
    TIPO_SUBSANACION_MOTIVO = "SUBSANACION_MOTIVO"
    TIPO_SUBSANACION_RESPUESTA = "SUBSANACION_RESPUESTA"
    TIPO_RENAPER_VALIDACION = "RENAPER_VALIDACION"
    TIPO_OBSERVACION_GENERAL = "OBSERVACION_GENERAL"
    TIPO_CRUCE_SINTYS = "CRUCE_SINTYS"
    TIPO_PAGO_OBSERVACION = "PAGO_OBSERVACION"

    TIPO_COMENTARIO_CHOICES = [
        (TIPO_VALIDACION_TECNICA, "Validación Técnica"),
        (TIPO_SUBSANACION_MOTIVO, "Motivo de Subsanación"),
        (TIPO_SUBSANACION_RESPUESTA, "Respuesta de Subsanación"),
        (TIPO_RENAPER_VALIDACION, "Validación RENAPER"),
        (TIPO_OBSERVACION_GENERAL, "Observación General"),
        (TIPO_CRUCE_SINTYS, "Cruce SINTYS"),
        (TIPO_PAGO_OBSERVACION, "Observación de Pago"),
    ]

    legajo = models.ForeignKey(
        ExpedienteCiudadano,
        on_delete=models.CASCADE,
        related_name="historial_comentarios",
    )
    tipo_comentario = models.CharField(
        max_length=30, choices=TIPO_COMENTARIO_CHOICES, db_index=True
    )
    comentario = models.TextField()
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="comentarios_realizados",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    # Campos opcionales para contexto
    archivo_adjunto = models.FileField(upload_to="comentarios/", null=True, blank=True)
    estado_relacionado = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Estado del legajo al momento del comentario",
    )

    class Meta:
        verbose_name = "Historial de Comentarios"
        verbose_name_plural = "Historial de Comentarios"
        ordering = ("-fecha_creacion",)
        indexes = [
            models.Index(fields=["legajo", "-fecha_creacion"]),
            models.Index(fields=["tipo_comentario", "-fecha_creacion"]),
            models.Index(fields=["usuario", "-fecha_creacion"]),
        ]

    def __str__(self):
        return f"{self.legajo} - {self.get_tipo_comentario_display()} ({self.fecha_creacion:%Y-%m-%d %H:%M})"
