from django.conf import settings
from django.contrib.auth.models import Group, Permission, User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from core.models import Localidad, Municipio, Provincia


def bulk_credentials_job_upload_to(instance, filename):
    return f"users/bulk_credentials_jobs/{instance.requested_by_id}/{filename}"


class Profile(models.Model):
    """Perfil extendido de usuario del sistema SISOC.

    Este modelo extiende el modelo User de Django con información adicional
    específica del sistema de gestión de comedores comunitarios.

    Roles principales:
    ----------------

    1. Usuario Provincial:
       - Tiene acceso limitado por ProfileTerritorialScope
       - Profile.provincia se conserva solo como compatibilidad legacy

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
        Provincia legacy; la autorización territorial usa ProfileTerritorialScope
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
    source = models.CharField(
        max_length=50,
        blank=True,
        default="sisoc",
        verbose_name="Origen del usuario",
        help_text=(
            "Sistema que originó el usuario (sisoc, ticketera, ...). "
            "Permite reconciliar altas provenientes de integraciones externas."
        ),
    )
    es_coordinador = models.BooleanField(
        default=False,
        verbose_name="Es Coordinador de Gestión",
        help_text="Marca si este usuario es coordinador de gestión",
    )
    es_territorial_comedor = models.BooleanField(
        default=False,
        verbose_name="Acceso SISOC - Mobile Territorial comedor",
        help_text=(
            "Marca al usuario como territorial (relevador) de comedores en "
            "SISOC - Mobile. El alcance se define por provincia en "
            "TerritorialComedorProvincia."
        ),
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


class ProfileTerritorialScope(models.Model):
    """Alcance territorial explícito para usuarios provinciales."""

    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="territorial_scopes",
    )
    provincia = models.ForeignKey(
        Provincia,
        on_delete=models.PROTECT,
        related_name="+",
    )
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
    scope_key = models.CharField(max_length=64, editable=False, db_index=True)

    class Meta:
        verbose_name = "Alcance territorial de perfil"
        verbose_name_plural = "Alcances territoriales de perfil"
        constraints = [
            models.CheckConstraint(
                check=Q(localidad__isnull=True) | Q(municipio__isnull=False),
                name="profile_scope_localidad_requires_municipio",
            ),
            models.UniqueConstraint(
                fields=["profile", "scope_key"],
                name="uniq_profile_scope_key",
            ),
        ]
        indexes = [
            models.Index(
                fields=["profile", "provincia"],
                name="users_profi_profile_4be6f7_idx",
            ),
            models.Index(
                fields=["profile", "provincia", "municipio"],
                name="users_profi_profile_26d7f4_idx",
            ),
        ]

    @staticmethod
    def build_scope_key(provincia_id, municipio_id=None, localidad_id=None):
        return f"p{provincia_id}:m{municipio_id or 0}:l{localidad_id or 0}"

    def clean(self):
        super().clean()
        if not self.provincia_id:
            raise ValidationError({"provincia": "Seleccione una provincia."})
        if self.localidad_id and not self.municipio_id:
            raise ValidationError(
                {"localidad": "Para asignar localidad debe seleccionar municipio."}
            )
        if self.municipio_id and self.municipio.provincia_id != self.provincia_id:
            raise ValidationError(
                {"municipio": "El municipio no pertenece a la provincia seleccionada."}
            )
        if self.localidad_id and self.localidad.municipio_id != self.municipio_id:
            raise ValidationError(
                {"localidad": "La localidad no pertenece al municipio seleccionado."}
            )

    def save(self, *args, **kwargs):
        self.scope_key = self.build_scope_key(
            self.provincia_id,
            self.municipio_id,
            self.localidad_id,
        )
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        parts = [str(self.provincia)]
        if self.municipio_id:
            parts.append(str(self.municipio))
        if self.localidad_id:
            parts.append(str(self.localidad))
        return " / ".join(parts)


class TerritorialComedorProvincia(models.Model):
    """Provincia de alcance de un usuario territorial de comedores (SISOC - Mobile).

    Estructura dedicada al rol territorial: mantiene el alcance desacoplado de
    ``ProfileTerritorialScope`` (usuarios provinciales) y de ``AccesoComedorPWA``
    (representantes PWA). Solo modela provincia, que es el eje con el que el pull
    de territoriales desde GESTIONAR/AppSheet cachea los relevadores.
    """

    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="territorial_comedor_provincias",
    )
    provincia = models.ForeignKey(
        Provincia,
        on_delete=models.PROTECT,
        related_name="+",
    )

    class Meta:
        verbose_name = "Provincia de territorial de comedor"
        verbose_name_plural = "Provincias de territorial de comedor"
        constraints = [
            models.UniqueConstraint(
                fields=["profile", "provincia"],
                name="uniq_territorial_comedor_provincia",
            ),
        ]
        indexes = [
            models.Index(fields=["provincia"]),
        ]

    def __str__(self):
        return f"{self.profile.user.username} / {self.provincia}"


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
    ACCION_UPDATE_PERMISSIONS = "update_permissions"

    ACCION_CHOICES = (
        (ACCION_CREATE, "Alta"),
        (ACCION_REACTIVATE, "Reactivación"),
        (ACCION_DEACTIVATE, "Baja"),
        (ACCION_UPDATE_PERMISSIONS, "Edicion de permisos"),
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


def user_import_job_upload_to(instance, filename):
    return f"users/import_jobs/{instance.requested_by_id}/{filename}"


class UserImportJob(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        PROCESSING = "processing", "Procesando"
        COMPLETED = "completed", "Completado"
        COMPLETED_WITH_ERRORS = "completed_with_errors", "Completado con errores"
        FAILED = "failed", "Fallido"

    requested_by = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        related_name="user_import_jobs",
    )
    archivo = models.FileField(upload_to=user_import_job_upload_to)
    original_filename = models.CharField(max_length=255)
    send_credentials = models.BooleanField(default=True)
    is_pwa_import = models.BooleanField(default=False)
    status = models.CharField(
        max_length=25,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    total_rows = models.PositiveIntegerField(default=0)
    processed_rows = models.PositiveIntegerField(default=0)
    created_rows = models.PositiveIntegerField(default=0)
    skipped_rows = models.PositiveIntegerField(default=0)
    failed_rows = models.PositiveIntegerField(default=0)
    next_row_index = models.PositiveIntegerField(default=0)
    last_successful_row = models.PositiveIntegerField(null=True, blank=True)
    last_successful_email = models.EmailField(max_length=254, blank=True)
    last_attempted_row = models.PositiveIntegerField(null=True, blank=True)
    last_attempted_email = models.EmailField(max_length=254, blank=True)
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
        verbose_name = "Lote de importacion masiva de usuarios"
        verbose_name_plural = "Lotes de importacion masiva de usuarios"

    def __str__(self):
        return f"Importacion {self.id} ({self.get_status_display()})"


class UserImportJobRow(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        CREATED = "created", "Creado"
        SKIPPED = "skipped", "Omitido"
        FAILED = "failed", "Fallido"

    job = models.ForeignKey(
        UserImportJob,
        on_delete=models.CASCADE,
        related_name="rows",
    )
    created_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    fila = models.PositiveIntegerField()
    nombre = models.CharField(max_length=150, blank=True)
    apellido = models.CharField(max_length=150, blank=True)
    email = models.EmailField(max_length=254, blank=True)
    rol = models.CharField(max_length=100, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    mensaje = models.TextField(blank=True)
    attempts = models.PositiveIntegerField(default=0)
    processed_at = models.DateTimeField(null=True, blank=True, db_index=True)
    credentials_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["fila", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["job", "fila"],
                name="users_user_import_job_row_unique",
            )
        ]
        indexes = [
            models.Index(fields=["job", "status"]),
            models.Index(fields=["job", "processed_at"]),
        ]
        verbose_name = "Fila de importacion masiva de usuarios"
        verbose_name_plural = "Filas de importacion masiva de usuarios"

    def __str__(self):
        return (
            f"Importacion {self.job_id} fila {self.fila} ({self.get_status_display()})"
        )
