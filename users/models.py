from django.contrib.auth.models import User
from django.db import models

from core.models import Provincia


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
       - Pertenecer al grupo "Coordinador Gestion" (en User.groups)
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

    3. Técnico con Coordinador:
       - Técnicos y abogados de duplas pueden tener un coordinador asignado
       - El campo 'coordinador' apunta a un usuario con rol Coordinador de Gestión

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
    coordinador : ForeignKey
        Coordinador de gestión asignado (para técnicos/abogados)
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
    coordinador = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tecnicos_coordinados",
        limit_choices_to={"groups__name": "Coordinador Gestion"},
        verbose_name="Coordinador de Gestión",
        help_text="Coordinador asignado a este técnico",
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

    def __str__(self):
        return f"Perfil de {self.user.username}"
