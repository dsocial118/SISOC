import uuid

from django.contrib.auth.models import User
from django.db import models

from comedores.models import Comedor
from comedores.models import Nomina
from core.models import Dia


class AuditoriaSesionPWA(models.Model):
    """Auditoría de eventos de autenticación/uso de API PWA."""

    EVENTO_LOGIN_OK = "login_ok"
    EVENTO_LOGIN_ERROR = "login_error"
    EVENTO_LOGOUT = "logout"
    EVENTO_TOKEN_INVALIDO = "token_invalido"
    EVENTO_ME_OK = "me_ok"

    RESULTADO_OK = "ok"
    RESULTADO_ERROR = "error"

    EVENTO_CHOICES = (
        (EVENTO_LOGIN_OK, "Login exitoso"),
        (EVENTO_LOGIN_ERROR, "Login fallido"),
        (EVENTO_LOGOUT, "Logout"),
        (EVENTO_TOKEN_INVALIDO, "Token inválido"),
        (EVENTO_ME_OK, "Consulta de contexto"),
    )
    RESULTADO_CHOICES = (
        (RESULTADO_OK, "OK"),
        (RESULTADO_ERROR, "Error"),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="auditorias_pwa",
    )
    username_intentado = models.CharField(max_length=150, null=True, blank=True)
    evento = models.CharField(max_length=30, choices=EVENTO_CHOICES)
    resultado = models.CharField(max_length=10, choices=RESULTADO_CHOICES)
    fecha_evento = models.DateTimeField(auto_now_add=True, db_index=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, null=True, blank=True)
    path = models.CharField(max_length=255)
    metodo_http = models.CharField(max_length=10)
    codigo_respuesta = models.PositiveSmallIntegerField(null=True, blank=True)
    motivo_error = models.CharField(max_length=255, null=True, blank=True)
    session_id = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)
    rol_pwa_snapshot = models.JSONField(default=list, blank=True)
    comedor_ids_snapshot = models.JSONField(default=list, blank=True)
    app_version = models.CharField(max_length=50, null=True, blank=True)
    platform = models.CharField(max_length=30, null=True, blank=True)
    is_standalone = models.BooleanField(null=True, blank=True)

    class Meta:
        verbose_name = "Auditoría sesión PWA"
        verbose_name_plural = "Auditorías sesiones PWA"
        indexes = [
            models.Index(fields=["user", "fecha_evento"]),
            models.Index(fields=["evento", "fecha_evento"]),
            models.Index(fields=["resultado", "fecha_evento"]),
        ]

    def __str__(self):
        username = (
            self.user.username if self.user_id else self.username_intentado or "-"
        )
        return f"{self.evento} - {username} - {self.fecha_evento:%Y-%m-%d %H:%M:%S}"


class AuditoriaOperacionPWA(models.Model):
    """Auditoria de operaciones de negocio en PWA."""

    ACCION_CREATE = "create"
    ACCION_UPDATE = "update"
    ACCION_DELETE = "delete"
    ACCION_ACTIVATE = "activate"
    ACCION_DEACTIVATE = "deactivate"

    ACCION_CHOICES = (
        (ACCION_CREATE, "Alta"),
        (ACCION_UPDATE, "Edicion"),
        (ACCION_DELETE, "Baja"),
        (ACCION_ACTIVATE, "Reactivacion"),
        (ACCION_DEACTIVATE, "Desactivacion"),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="auditorias_operacion_pwa",
    )
    comedor = models.ForeignKey(
        Comedor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="auditorias_operacion_pwa",
    )
    entidad = models.CharField(max_length=50, db_index=True)
    entidad_id = models.PositiveIntegerField(db_index=True)
    accion = models.CharField(max_length=20, choices=ACCION_CHOICES, db_index=True)
    fecha_evento = models.DateTimeField(auto_now_add=True, db_index=True)
    snapshot_antes = models.JSONField(null=True, blank=True)
    snapshot_despues = models.JSONField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Auditoria operacion PWA"
        verbose_name_plural = "Auditorias operaciones PWA"
        indexes = [
            models.Index(fields=["comedor", "fecha_evento"]),
            models.Index(fields=["entidad", "entidad_id", "fecha_evento"]),
            models.Index(fields=["accion", "fecha_evento"]),
        ]

    def __str__(self):
        return f"{self.entidad}#{self.entidad_id} {self.accion} {self.fecha_evento:%Y-%m-%d %H:%M:%S}"


class LecturaMensajePWA(models.Model):
    """Estado de lectura de mensajes PWA originados en comunicados."""

    comunicado = models.ForeignKey(
        "comunicados.Comunicado",
        on_delete=models.CASCADE,
        related_name="lecturas_pwa",
    )
    comedor = models.ForeignKey(
        Comedor,
        on_delete=models.CASCADE,
        related_name="lecturas_mensajes_pwa",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="lecturas_mensajes_pwa",
    )
    visto = models.BooleanField(default=False)
    fecha_visto = models.DateTimeField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Lectura mensaje PWA"
        verbose_name_plural = "Lecturas mensajes PWA"
        ordering = ("-fecha_visto", "-fecha_creacion", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=("comunicado", "comedor", "user"),
                name="uniq_lectura_mensaje_pwa_por_usuario_espacio",
            )
        ]
        indexes = [
            models.Index(
                fields=["comedor", "user", "visto"],
                name="pwa_msg_read_com_user_seen_idx",
            ),
            models.Index(
                fields=["comunicado", "user"],
                name="pwa_msg_read_msg_user_idx",
            ),
            models.Index(fields=["fecha_visto"], name="pwa_msg_read_seen_at_idx"),
        ]

    def __str__(self):
        return (
            f"Mensaje {self.comunicado_id} - user {self.user_id} - "
            f"comedor {self.comedor_id} - visto={self.visto}"
        )


class PushSubscriptionPWA(models.Model):
    """Suscripción web push asociada a un usuario/dispositivo PWA."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="push_subscriptions_pwa",
    )
    endpoint = models.URLField(max_length=500, unique=True)
    p256dh = models.CharField(max_length=255)
    auth = models.CharField(max_length=255)
    content_encoding = models.CharField(max_length=30, default="aes128gcm")
    user_agent = models.CharField(max_length=512, null=True, blank=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_baja = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Suscripción push PWA"
        verbose_name_plural = "Suscripciones push PWA"
        ordering = ("-fecha_actualizacion", "-id")
        indexes = [
            models.Index(fields=["user", "activo"], name="pwa_push_user_activo_idx"),
            models.Index(
                fields=["fecha_actualizacion"],
                name="pwa_push_updated_at_idx",
            ),
        ]

    def __str__(self):
        return f"Push user {self.user_id} activo={self.activo}"


class ColaboradorEspacioPWA(models.Model):
    """Colaborador asociado a un espacio (comedor) para la app PWA."""

    comedor = models.ForeignKey(
        Comedor,
        on_delete=models.CASCADE,
        related_name="colaboradores_pwa",
    )
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    dni = models.CharField(max_length=8)
    telefono = models.CharField(max_length=30)
    email = models.EmailField(max_length=255)
    rol_funcion = models.CharField(max_length=150)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_baja = models.DateTimeField(null=True, blank=True)
    creado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="colaboradores_pwa_creados",
    )
    actualizado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="colaboradores_pwa_actualizados",
    )

    class Meta:
        verbose_name = "Colaborador PWA"
        verbose_name_plural = "Colaboradores PWA"
        ordering = ("apellido", "nombre", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=("comedor", "dni"),
                name="uniq_colaborador_pwa_dni_por_comedor",
            )
        ]
        indexes = [
            models.Index(
                fields=["comedor", "activo"], name="pwa_colab_comedor_activo_idx"
            ),
            models.Index(fields=["comedor", "dni"], name="pwa_colab_comedor_dni_idx"),
        ]

    def __str__(self):
        return f"{self.apellido}, {self.nombre} ({self.dni})"


class CatalogoActividadPWA(models.Model):
    """Catalogo cerrado de actividades habilitadas para PWA."""

    categoria = models.CharField(max_length=120)
    actividad = models.CharField(max_length=180)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Catalogo Actividad PWA"
        verbose_name_plural = "Catalogo Actividades PWA"
        ordering = ("categoria", "actividad", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("categoria", "actividad"),
                name="uniq_catalogo_actividad_pwa_categoria_actividad",
            )
        ]
        indexes = [
            models.Index(fields=["categoria"], name="pwa_cat_act_categoria_idx"),
            models.Index(fields=["activo"], name="pwa_cat_act_activo_idx"),
        ]

    def __str__(self):
        return f"{self.categoria} - {self.actividad}"


class ActividadEspacioPWA(models.Model):
    """Actividad dada de alta en un espacio (comedor)."""

    comedor = models.ForeignKey(
        Comedor,
        on_delete=models.CASCADE,
        related_name="actividades_pwa",
    )
    catalogo_actividad = models.ForeignKey(
        CatalogoActividadPWA,
        on_delete=models.PROTECT,
        related_name="actividades_espacio",
    )
    dia_actividad = models.ForeignKey(
        Dia,
        on_delete=models.PROTECT,
        related_name="actividades_pwa",
    )
    horario_actividad = models.CharField(max_length=60)
    hora_inicio = models.TimeField(null=True, blank=True)
    hora_fin = models.TimeField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    fecha_alta = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_baja = models.DateTimeField(null=True, blank=True)
    creado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="actividades_pwa_creadas",
    )
    actualizado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="actividades_pwa_actualizadas",
    )

    class Meta:
        verbose_name = "Actividad Espacio PWA"
        verbose_name_plural = "Actividades Espacio PWA"
        ordering = ("-fecha_alta", "-id")
        indexes = [
            models.Index(
                fields=["comedor", "activo"], name="pwa_act_esp_com_activo_idx"
            ),
            models.Index(
                fields=["catalogo_actividad"], name="pwa_act_esp_catalogo_idx"
            ),
        ]

    def __str__(self):
        return f"{self.comedor} - {self.catalogo_actividad}"


class InscriptoActividadEspacioPWA(models.Model):
    """Vinculacion de nomina del espacio con una actividad PWA."""

    actividad_espacio = models.ForeignKey(
        ActividadEspacioPWA,
        on_delete=models.CASCADE,
        related_name="inscriptos",
    )
    nomina = models.ForeignKey(
        Nomina,
        on_delete=models.PROTECT,
        related_name="inscripciones_actividad_pwa",
    )
    activo = models.BooleanField(default=True)
    fecha_alta = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_baja = models.DateTimeField(null=True, blank=True)
    creado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inscriptos_actividad_pwa_creados",
    )
    actualizado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inscriptos_actividad_pwa_actualizados",
    )

    class Meta:
        verbose_name = "Inscripto Actividad Espacio PWA"
        verbose_name_plural = "Inscriptos Actividad Espacio PWA"
        ordering = ("-fecha_alta", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=("actividad_espacio", "nomina", "activo"),
                name="uniq_inscripto_actividad_nomina_estado_pwa",
            )
        ]
        indexes = [
            models.Index(
                fields=["actividad_espacio", "activo"], name="pwa_insc_act_activo_idx"
            ),
            models.Index(
                fields=["nomina", "activo"], name="pwa_insc_nomina_activo_idx"
            ),
        ]

    def __str__(self):
        return f"{self.actividad_espacio_id} - nomina {self.nomina_id}"


class NominaEspacioPWA(models.Model):
    """Perfil PWA para una persona de nómina del espacio."""

    nomina = models.OneToOneField(
        Nomina,
        on_delete=models.CASCADE,
        related_name="perfil_pwa",
    )
    asistencia_alimentaria = models.BooleanField(default=True)
    asistencia_actividades = models.BooleanField(default=False)
    es_indocumentado = models.BooleanField(default=False)
    identificador_interno = models.CharField(max_length=40, null=True, blank=True)
    activo = models.BooleanField(default=True)
    fecha_alta = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_baja = models.DateTimeField(null=True, blank=True)
    creado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="nominas_pwa_creadas",
    )
    actualizado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="nominas_pwa_actualizadas",
    )

    class Meta:
        verbose_name = "Nomina Espacio PWA"
        verbose_name_plural = "Nominas Espacio PWA"
        indexes = [
            models.Index(fields=["activo"], name="pwa_nomina_activo_idx"),
            models.Index(
                fields=["asistencia_alimentaria", "asistencia_actividades"],
                name="pwa_nomina_asistencia_idx",
            ),
            models.Index(fields=["es_indocumentado"], name="pwa_nomina_indoc_idx"),
        ]

    def __str__(self):
        return f"Nomina {self.nomina_id} - indocumentado={self.es_indocumentado}"


class RegistroAsistenciaNominaPWA(models.Model):
    """Historial de toma de asistencia por período para una persona de nómina."""

    PERIODICIDAD_MENSUAL = "mensual"

    PERIODICIDAD_CHOICES = ((PERIODICIDAD_MENSUAL, "Mensual"),)

    nomina = models.ForeignKey(
        Nomina,
        on_delete=models.CASCADE,
        related_name="registros_asistencia_pwa",
    )
    periodicidad = models.CharField(
        max_length=20,
        choices=PERIODICIDAD_CHOICES,
        default=PERIODICIDAD_MENSUAL,
    )
    periodo_referencia = models.DateField(
        help_text="Fecha ancla del período. Para mensual se usa el primer día del mes."
    )
    fecha_toma_asistencia = models.DateTimeField(auto_now_add=True, db_index=True)
    tomado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="asistencias_nomina_pwa_registradas",
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Registro Asistencia Nómina PWA"
        verbose_name_plural = "Registros Asistencia Nómina PWA"
        ordering = ("-periodo_referencia", "-fecha_toma_asistencia", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=("nomina", "periodicidad", "periodo_referencia"),
                name="uniq_pwa_asistencia_nomina_periodo",
            )
        ]
        indexes = [
            models.Index(
                fields=["nomina", "periodicidad", "periodo_referencia"],
                name="pwa_nom_asis_nom_per_idx",
            ),
            models.Index(
                fields=["periodicidad", "periodo_referencia"],
                name="pwa_nom_asis_periodo_idx",
            ),
        ]

    def __str__(self):
        return (
            f"Asistencia nomina {self.nomina_id} {self.periodicidad} "
            f"{self.periodo_referencia:%Y-%m}"
        )
