import logging
from typing import Tuple, List

from django.contrib.auth.models import User
from django.db.models import F
from django.urls import reverse

from core.constants import UserGroups
from core.services.advanced_filters import AdvancedFilterEngine
from core.services.favorite_filters import SeccionesFiltrosFavoritos
from users.users_filter_config import (
    FIELD_MAP as BENEFICIARIO_FILTER_MAP,
    FIELD_TYPES as BENEFICIARIO_FIELD_TYPES,
    TEXT_OPS as BENEFICIARIO_TEXT_OPS,
    NUM_OPS as BENEFICIARIO_NUM_OPS,
    get_filters_ui_config,
)

logger = logging.getLogger("django")

BENEFICIARIO_ADVANCED_FILTER = AdvancedFilterEngine(
    field_map=BENEFICIARIO_FILTER_MAP,
    field_types=BENEFICIARIO_FIELD_TYPES,
    allowed_ops={
        "text": BENEFICIARIO_TEXT_OPS,
        "number": BENEFICIARIO_NUM_OPS,
    },
)


class UsuariosService:
    @staticmethod
    def get_filtered_usuarios(request_or_get):
        """Aplica filtros combinables sobre el listado de usuarios."""
        base_qs = UsuariosService.get_usuarios_queryset()
        return BENEFICIARIO_ADVANCED_FILTER.filter_queryset(base_qs, request_or_get)

    @staticmethod
    def get_usuarios_queryset():
        """Query optimizada para usuarios"""
        # Profile tiene FK a User y a Provincia; seleccionar esas relaciones evita consultas N+1
        return (
            User.objects.select_related("profile")
            .annotate(rol=F("profile__rol"))
            .order_by("-id")
        )

    @staticmethod
    def get_usuarios_list_context():
        """Configuración para la lista de usuarios"""
        return {
            "table_headers": [
                {
                    "title": "Nombre",
                    "width": "12%",
                    "sortable": True,
                    "sort_key": "first_name",
                },
                {
                    "title": "Apellido",
                    "width": "20%",
                    "sortable": True,
                    "sort_key": "last_name",
                },
                {
                    "title": "Username",
                    "width": "10%",
                    "sortable": True,
                    "sort_key": "username",
                },
                {
                    "title": "Email",
                    "width": "8%",
                    "sortable": True,
                    "sort_key": "email",
                },
                {"title": "Rol", "width": "20%", "sortable": True, "sort_key": "rol"},
            ],
            "table_fields": [
                {"name": "first_name"},
                {"name": "last_name"},
                {"name": "username"},
                {"name": "email"},
                {"name": "rol"},
            ],
            "table_actions": [
                {
                    "label": "Editar",
                    "url_name": "usuario_editar",
                    "type": "editar",
                    "icon": "edit",
                },
                {
                    "label": "Eliminar",
                    "url_name": "usuario_borrar",
                    "type": "eliminar",
                    "icon": "trash-alt",
                },
            ],
            "breadcrumb_items": [
                {"text": "Usuarios", "url": reverse("usuarios")},
                {"text": "Listar", "active": True},
            ],
            "reset_url": reverse("usuarios"),
            "add_url": reverse("usuario_crear"),
            "filters_mode": True,
            "filters_config": get_filters_ui_config(),
            "filters_action": reverse("usuarios"),
            "seccion_filtros_favoritos": SeccionesFiltrosFavoritos.USUARIOS,
            "show_add_button": True,
        }


class UserPermissionService:
    """Servicio para verificación y gestión de permisos de usuarios."""

    @staticmethod
    def get_coordinador_duplas(user: User) -> Tuple[bool, List[int]]:
        """
        Obtiene información de coordinador de un usuario.

        Args:
            user: Usuario a verificar

        Returns:
            Tuple de (es_coordinador: bool, duplas_ids: List[int])
            - Si es coordinador: (True, [lista de IDs de duplas])
            - Si no es coordinador: (False, [])
            - Si hay error: (False, [])

        Examples:
            >>> is_coord, duplas = UserPermissionService.get_coordinador_duplas(user)
            >>> if is_coord:
            ...     comedores = Comedor.objects.filter(dupla_id__in=duplas)
        """
        try:
            # Verificar que el usuario tenga profile
            if not hasattr(user, "profile"):
                logger.debug(f"Usuario {user.pk} no tiene profile")
                return False, []

            profile = user.profile

            # Verificar si es coordinador
            if not profile.es_coordinador:
                return False, []

            # Obtener IDs de duplas asignadas
            duplas_ids = list(profile.duplas_asignadas.values_list("id", flat=True))

            if not duplas_ids:
                logger.warning(
                    f"Usuario {user.pk} es coordinador pero no tiene duplas asignadas"
                )

            return True, duplas_ids

        except AttributeError as e:
            # Error en estructura del modelo - no debería ocurrir
            logger.error(
                f"Error de atributo al obtener duplas de coordinador "
                f"para usuario {user.pk}: {e}"
            )
            return False, []

        except Exception as e:
            # Error inesperado
            logger.exception(
                f"Error inesperado al obtener duplas de coordinador "
                f"para usuario {user.pk}: {e}"
            )
            return False, []

    @staticmethod
    def tiene_grupo(user: User, grupo_nombre: str) -> bool:
        """
        Verifica si un usuario pertenece a un grupo específico.

        Args:
            user: Usuario a verificar
            grupo_nombre: Nombre del grupo

        Returns:
            True si el usuario pertenece al grupo, False en caso contrario
        """
        if not user or not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        return user.groups.filter(name=grupo_nombre).exists()

    @staticmethod
    def tiene_alguno_de_los_grupos(user: User, grupos: List[str]) -> bool:
        """
        Verifica si un usuario pertenece a al menos uno de los grupos especificados.

        Args:
            user: Usuario a verificar
            grupos: Lista de nombres de grupos

        Returns:
            True si el usuario pertenece a al menos un grupo, False en caso contrario
        """
        if not user or not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        return user.groups.filter(name__in=grupos).exists()

    @staticmethod
    def es_tecnico_o_abogado(user: User) -> bool:
        """
        Verifica si un usuario es técnico de comedor o abogado de dupla.

        Args:
            user: Usuario a verificar

        Returns:
            True si es técnico o abogado, False en caso contrario
        """
        return UserPermissionService.tiene_alguno_de_los_grupos(
            user, UserGroups.DUPLA_ROLES
        )

    @staticmethod
    def es_coordinador(user: User) -> bool:
        """
        Verifica si un usuario es coordinador de gestión.

        Args:
            user: Usuario a verificar

        Returns:
            True si es coordinador, False en caso contrario
        """
        is_coord, _ = UserPermissionService.get_coordinador_duplas(user)
        return is_coord
