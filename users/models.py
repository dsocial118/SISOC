from django.contrib.auth.models import Group, Permission, User
from django.db import models

from core.models import Provincia


def bulk_credentials_job_upload_to(instance, filename):
    return f"users/bulk_credentials_jobs/{instance.requested_by_id}/{filename}"


class Profile(models.Model):
    """Perfil extendido de usuario del sistema SISOC.

    Este modelo extiende el modelo User de Django con información adicional
    específica del sistema de gestión de comedores comunitarios.

    Roles principales:
    ----------------

    1. Usuario Provincial:
       - Tiene acceso limitado a comedores de su provincia específica
       - Requiere: es_usuario_provincial=True y provincia asignada

    2. Coordinador de Gestión:
       - Rol de supervisión con acceso de solo lectura a comedores/admisiones/acompañamientos
       - Supervisa el trabajo de equipos técnicos (duplas) asignados

       Requisitos para ser Coordinador:
       - es_coordinador=True
       - Pertenecer al grupo "Coordinador Equipo Tecnico" (en User.groups)
       - is_staff=True (requerido para acceso al backoffice)
       - Tener al menos una dupla asignada en duplas_asignadas

       Permisos y alcance:
       - Acceso de SOLO LECTURA a:
         * Comedores de las duplas asignadas
         * Admisiones de esos comedores
         * Acompañamientos de esos comedores
       - NO puede editar, crear ni eliminar registros
       - NO puede ver comedores de duplas no asignadas

       Restricciones:
       - Un coordinador NO debe coordinar duplas donde participa como técnico/abogado
       - Solo puede asignarse duplas activas que tengan comedores
       - La asignación es many-to-many (un coordinador puede tener múltiples duplas)

       Ejemplo de uso:
       >>> coord = User.objects.create(username='coord1', is_staff=True)
       >>> coord.groups.add(Group.objects.get(name='Coordinador Gestion'))
       >>> profile = coord.profile
       >>> profile.es_coordinador = True
       >>> dupla1 = Dupla.objects.get(id=1)
       >>> profile.duplas_asignadas.add(dupla1)
       >>> # Ahora coord1 puede ver comedores de dupla1 en modo solo lectura

    Campos:
    -------
    user : OneToOneField
        Usuario de Django asociado (relación 1:1)
    dark_mode : BooleanField
        Preferencia de tema oscuro en la UI
    es_usuario_provincial : BooleanField
        Indica si el usuario tiene restricción por provincia
    provincia : ForeignKey
        Provincia específica si es_usuario_provincial=True
    rol : CharField
        Descripción textual del rol (complementa groups)
    es_coordinador : BooleanField
        Marca si este usuario es coordinador de gestión
    duplas_asignadas : ManyToManyField
        Duplas (equipos técnicos) que este coordinador supervisa
    fecha_creacion : DateTimeField
        Fecha de creación del perfil

    Ver también:
    ------------
    - users.services.UserPermissionService: Lógica centralizada de permisos
    - core.constants.UserGroups: Nombres de grupos del sistema
    - duplas.models.Dupla: Modelo de equipos técnicos
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    dark_mode = models.BooleanField(default=True)
    es_usuario_provincial = models.BooleanField(default=False)
    provincia = models.ForeignKey(
        Provincia, on_delete=models.SET_NULL, null=True, blank=True
    )
    rol = models.CharField(max_length=100, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    must_change_password = models.BooleanField(
        default=False,
        verbose_name="Debe cambiar contraseña",
        help_text="Obliga al usuario a actualizar la contraseña en su próximo login web.",
    )
    password_changed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Contraseña actualizada en",
    )
    initial_password_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Expira contraseña inicial en",
    )
    password_reset_requested_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Reset de contraseña solicitado en",
        help_text=(
            "Se completa cuando un usuario mobile solicita desde la app "
            "que un administrador genere una nueva contraseña temporal."
        ),
    )
    temporary_password_plaintext = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        verbose_name="Contraseña temporal visible",
    )
    es_coordinador = models.BooleanField(
        default=False,
        verbose_name="Es Coordinador de Gestión",
        help_text="Marca si este usuario es coordinador de gestión",
    )
    duplas_asignadas = models.ManyToManyField(
        "duplas.Dupla",
        blank=True,
        related_name="coordinadores",
        verbose_name="Duplas asignadas",
        help_text="Duplas (equipos técnicos) asignadas a este coordinador",
    )
    grupos_asignables = models.ManyToManyField(
        Group,
        blank=True,
        related_name="perfiles_delegadores",
        verbose_name="Grupos que puede asignar",
        help_text="Define qué grupos puede asignar este usuario al crear/editar otros usuarios.",
    )
    roles_asignables = models.ManyToManyField(
        Permission,
        blank=True,
        related_name="perfiles_roles_delegables",
        verbose_name="Roles que puede asignar",
        help_text="Permisos auth.role_* que este usuario puede asignar a terceros.",
    )

    def __str__(self):
        return f"Perfil de {self.user.username}"


class AccesoComedorPWA(models.Model):
    """Relación de alcance PWA entre usuario y comedor."""

    ROL_REPRESENTANTE = "representante"
    ROL_OPERADOR = "operador"
    TIPO_ASOCIACION_ORGANIZACION = "organizacion"
    TIPO_ASOCIACION_ESPACIO = "espacio"
    ROL_CHOICES = (
        (ROL_REPRESENTANTE, "Representante"),
        (ROL_OPERADOR, "Operador"),
    )
    TIPO_ASOCIACION_CHOICES = (
        (TIPO_ASOCIACION_ORGANIZACION, "Organización"),
        (TIPO_ASOCIACION_ESPACIO, "Espacio"),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="accesos_pwa",
    )
    comedor = models.ForeignKey(
        "comedores.Comedor",
        on_delete=models.CASCADE,
        related_name="accesos_pwa",
    )
    organizacion = models.ForeignKey(
        "organizaciones.Organizacion",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="accesos_pwa",
    )
    rol = models.CharField(max_length=20, choices=ROL_CHOICES)
    tipo_asociacion = models.CharField(
        max_length=20,
        choices=TIPO_ASOCIACION_CHOICES,
        default=TIPO_ASOCIACION_ESPACIO,
    )
    creado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accesos_pwa_creados",
    )
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_baja = models.DateTimeField(null=True, blank=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Acceso PWA a comedor"
        verbose_name_plural = "Accesos PWA a comedor"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "comedor"],
                name="unique_pwa_user_comedor",
            )
        ]
        indexes = [
            models.Index(fields=["user", "activo"]),
            models.Index(fields=["comedor", "rol", "activo"]),
            models.Index(fields=["organizacion", "activo"]),
            models.Index(fields=["creado_por", "activo"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.comedor_id} - {self.rol}"


class AuditAccesoComedorPWA(models.Model):
    ACCION_CREATE = "create"
    ACCION_REACTIVATE = "reactivate"
    ACCION_DEACTIVATE = "deactivate"

    ACCION_CHOICES = (
        (ACCION_CREATE, "Alta"),
        (ACCION_REACTIVATE, "Reactivación"),
        (ACCION_DEACTIVATE, "Baja"),
    )

    acceso = models.ForeignKey(
        AccesoComedorPWA,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accesos_pwa_audit_logs",
    )
    comedor = models.ForeignKey(
        "comedores.Comedor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accesos_pwa_audit_logs",
    )
    organizacion = models.ForeignKey(
        "organizaciones.Organizacion",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accesos_pwa_audit_logs",
    )
    accion = models.CharField(max_length=20, choices=ACCION_CHOICES, db_index=True)
    fecha_evento = models.DateTimeField(auto_now_add=True, db_index=True)
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accesos_pwa_audit_eventos",
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-fecha_evento", "-id"]
        verbose_name = "Auditoría de acceso PWA"
        verbose_name_plural = "Auditorías de accesos PWA"
        indexes = [
            models.Index(fields=["user", "fecha_evento"]),
            models.Index(fields=["comedor", "fecha_evento"]),
            models.Index(fields=["accion", "fecha_evento"]),
        ]

    def __str__(self):
        return (
            f"{self.user_id or '-'} {self.accion} {self.fecha_evento:%Y-%m-%d %H:%M:%S}"
        )


class BulkCredentialsJob(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        PROCESSING = "processing", "Procesando"
        COMPLETED = "completed", "Completado"
        FAILED = "failed", "Fallido"

    requested_by = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        related_name="bulk_credentials_jobs",
    )
    archivo = models.FileField(upload_to=bulk_credentials_job_upload_to)
    original_filename = models.CharField(max_length=255)
    send_type = models.CharField(max_length=32, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    total_rows = models.PositiveIntegerField(default=0)
    processed_rows = models.PositiveIntegerField(default=0)
    sent_rows = models.PositiveIntegerField(default=0)
    updated_password_rows = models.PositiveIntegerField(default=0)
    unchanged_password_rows = models.PositiveIntegerField(default=0)
    rejected_rows = models.PositiveIntegerField(default=0)
    next_row_index = models.PositiveIntegerField(default=0)
    last_successful_row = models.PositiveIntegerField(null=True, blank=True)
    last_successful_username = models.CharField(max_length=150, blank=True)
    last_attempted_row = models.PositiveIntegerField(null=True, blank=True)
    last_attempted_username = models.CharField(max_length=150, blank=True)
    last_error_message = models.TextField(blank=True)
    last_error_at = models.DateTimeField(null=True, blank=True)
    resume_count = models.PositiveIntegerField(default=0)
    requested_at = models.DateTimeField(auto_now_add=True, db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    last_activity_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        ordering = ["-requested_at", "-id"]
        indexes = [
            models.Index(fields=["status", "requested_at"]),
            models.Index(fields=["requested_by", "requested_at"]),
        ]
        verbose_name = "Lote de credenciales masivas"
        verbose_name_plural = "Lotes de credenciales masivas"

    def __str__(self):
        return f"Lote {self.id} ({self.get_status_display()})"


class BulkCredentialsJobRow(models.Model):
    class Status(models.TextChoices):
        SENT = "sent", "Enviada"
        FAILED = "failed", "Fallida"

    job = models.ForeignKey(
        BulkCredentialsJob,
        on_delete=models.CASCADE,
        related_name="rows",
    )
    fila = models.PositiveIntegerField()
    usuario = models.CharField(max_length=150, blank=True)
    mail_destino = models.EmailField(max_length=254, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, db_index=True)
    mensaje = models.TextField(blank=True)
    password_actualizada = models.BooleanField(default=False)
    attempts = models.PositiveIntegerField(default=0)
    processed_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        ordering = ["fila", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["job", "fila"],
                name="users_bulk_credentials_job_row_unique",
            )
        ]
        indexes = [
            models.Index(fields=["job", "status"]),
            models.Index(fields=["job", "processed_at"]),
        ]
        verbose_name = "Resultado de fila de credenciales masivas"
        verbose_name_plural = "Resultados de filas de credenciales masivas"

    def __str__(self):
        return f"Lote {self.job_id} fila {self.fila} ({self.get_status_display()})"
