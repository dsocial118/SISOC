import logging
from typing import List, Tuple

from django.contrib.auth.models import User
from django.db.models import Case, CharField, F, Value, When
from django.db.models import Case, CharField, Count, F, Q, Value, When
from django.urls import reverse

from core.services.advanced_filters import AdvancedFilterEngine
from core.services.column_preferences import build_columns_context
from core.services.favorite_filters import SeccionesFiltrosFavoritos
from iam.services import user_has_any_permission_codes, user_has_permission_code
from users.models import Profile
from users.users_filter_config import (
    FIELD_MAP as BENEFICIARIO_FILTER_MAP,
    FIELD_TYPES as BENEFICIARIO_FIELD_TYPES,
    NUM_OPS as BENEFICIARIO_NUM_OPS,
    TEXT_OPS as BENEFICIARIO_TEXT_OPS,
    get_filters_ui_config,
)
from users.usuarios_column_config import USUARIOS_COLUMNS, USUARIOS_LIST_KEY

logger = logging.getLogger("django")
TECHNICAL_ROLE_PERMISSION_CODES = (
    "auth.role_tecnico_comedor",
    "auth.role_abogado_dupla",
)

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
    def get_pending_mobile_password_reset_count() -> int:
        """Cantidad de usuarios con solicitud pendiente de reset mobile."""
        return Profile.objects.filter(password_reset_requested_at__isnull=False).count()

    @staticmethod
    def has_pending_mobile_password_resets() -> bool:
        """Indica si existe al menos una solicitud pendiente de reset mobile."""
        return Profile.objects.filter(password_reset_requested_at__isnull=False).exists()

    @staticmethod
    def can_view_mobile_reset_notifications(user: User) -> bool:
        """Determina si el usuario puede ver alertas de reset mobile."""
        if not user or not user.is_authenticated:
            return False
        return bool(user.is_superuser or user.has_perm("auth.change_user"))

    @staticmethod
    def get_filtered_usuarios(request_or_get):
        """Aplica filtros combinables sobre el listado de usuarios."""
        base_qs = UsuariosService.get_usuarios_queryset()
        base_qs = UsuariosService._apply_actor_scope(base_qs, request_or_get)
        return BENEFICIARIO_ADVANCED_FILTER.filter_queryset(base_qs, request_or_get)

    @staticmethod
    def _apply_actor_scope(base_qs, request_or_get):
        """
        Restringe visibilidad de usuarios según el alcance delegable del actor.

        Regla: si el actor tiene configurado `grupos_asignables` y/o
        `roles_asignables` (auth.role_*), solo puede ver usuarios cuyos grupos
        y roles directos sean un subconjunto de ese alcance.
        """
        actor = getattr(request_or_get, "user", None)
        if not actor or not getattr(actor, "is_authenticated", False):
            return base_qs
        if actor.is_superuser:
            return base_qs

        profile = getattr(actor, "profile", None)
        if not profile:
            return base_qs

        allowed_groups = profile.grupos_asignables.all()
        allowed_roles = profile.roles_asignables.filter(
            content_type__app_label="auth",
            codename__startswith="role_",
        )

        has_group_scope = allowed_groups.exists()
        has_role_scope = allowed_roles.exists()
        if not has_group_scope and not has_role_scope:
            return base_qs

        scoped_qs = base_qs.annotate(
            total_groups=Count("groups", distinct=True),
            allowed_groups_count=Count(
                "groups",
                filter=Q(groups__in=allowed_groups),
                distinct=True,
            ),
            total_role_permissions=Count(
                "user_permissions",
                filter=Q(
                    user_permissions__content_type__app_label="auth",
                    user_permissions__codename__startswith="role_",
                ),
                distinct=True,
            ),
            allowed_role_permissions_count=Count(
                "user_permissions",
                filter=Q(user_permissions__in=allowed_roles),
                distinct=True,
            ),
        )

        scope_filter = Q()
        if has_group_scope:
            scope_filter &= Q(total_groups=F("allowed_groups_count"))
        if has_role_scope:
            scope_filter &= Q(
                total_role_permissions=F("allowed_role_permissions_count")
            )

        scoped_qs = scoped_qs.filter(Q(pk=actor.pk) | scope_filter)

        return scoped_qs.distinct().order_by("-id")

    @staticmethod
    def get_usuarios_queryset():
        """Query optimizada para usuarios."""
        return (
            User.objects.select_related("profile")
            .annotate(
                rol=F("profile__rol"),
                password_reset_requested_at=F("profile__password_reset_requested_at"),
                password_reset_requested_indicator=Case(
                    When(
                        profile__password_reset_requested_at__isnull=False,
                        then=Value("!"),
                    ),
                    default=Value("-"),
                is_active_display=Case(
                    When(is_active=True, then=Value("true")),
                    default=Value("false"),
                    output_field=CharField(),
                ),
            )
            .order_by("-id")
        )

    @staticmethod
    def get_usuarios_list_context(request):
        """Configuración para la lista de usuarios."""
        columns_catalog = list(USUARIOS_COLUMNS)
        if not UsuariosService.has_pending_mobile_password_resets():
            columns_catalog = [
                column
                for column in columns_catalog
                if column.key != "password_reset_requested_indicator"
            ]
        columns_context = build_columns_context(
            request,
            USUARIOS_LIST_KEY,
            columns_catalog,
        )
        return {
            **columns_context,
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

    @staticmethod
    def build_user_table_items(users, table_fields):
        """Construye filas para la tabla personalizada del listado de usuarios."""
        field_names = [field.get("name") for field in table_fields]
        items = []

        for user in users:
            cells = []
            for field_name in field_names:
                value = getattr(user, field_name, "")
                if value is None:
                    value = "-"
                cells.append({"content": value})

            actions = [
                {
                    "label": "Editar",
                    "url": reverse("usuario_editar", kwargs={"pk": user.pk}),
                    "type": "primary",
                    "icon": "edit",
                }
            ]
            if user.is_active:
                actions.append(
                    {
                        "label": "Desactivar",
                        "url": reverse("usuario_borrar", kwargs={"pk": user.pk}),
                        "type": "danger",
                        "icon": "trash-alt",
                    }
                )
            else:
                actions.append(
                    {
                        "label": "Activar",
                        "url": reverse("usuario_activar", kwargs={"pk": user.pk}),
                        "type": "success",
                        "icon": "check-circle",
                    }
                )

            items.append({"cells": cells, "actions": actions})

        return items


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
        """
        try:
            if not hasattr(user, "profile"):
                logger.debug(f"Usuario {user.pk} no tiene profile")
                return False, []

            profile = user.profile
            if not profile.es_coordinador:
                return False, []

            duplas_ids = list(profile.duplas_asignadas.values_list("id", flat=True))

            if not duplas_ids:
                logger.warning(
                    f"Usuario {user.pk} es coordinador pero no tiene duplas asignadas"
                )

            return True, duplas_ids

        except AttributeError as exc:
            logger.error(
                f"Error de atributo al obtener duplas de coordinador "
                f"para usuario {user.pk}: {exc}"
            )
            return False, []

        except Exception as exc:
            logger.exception(
                f"Error inesperado al obtener duplas de coordinador "
                f"para usuario {user.pk}: {exc}"
            )
            return False, []

    @staticmethod
    def tiene_grupo(user: User, permiso_codigo: str) -> bool:
        """Verifica si un usuario tiene un permiso específico."""
        if not user or not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        return user_has_permission_code(user, permiso_codigo)

    @staticmethod
    def tiene_alguno_de_los_grupos(user: User, permisos: List[str]) -> bool:
        """Verifica si un usuario tiene al menos uno de los permisos especificados."""
        if not user or not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        return user_has_any_permission_codes(user, permisos)

    @staticmethod
    def es_tecnico_o_abogado(user: User) -> bool:
        """Verifica si un usuario es técnico de comedor o abogado de dupla."""
        return UserPermissionService.tiene_alguno_de_los_grupos(
            user, list(TECHNICAL_ROLE_PERMISSION_CODES)
        )

    @staticmethod
    def es_coordinador(user: User) -> bool:
        """Verifica si un usuario es coordinador de gestión."""
        is_coord, _ = UserPermissionService.get_coordinador_duplas(user)
        return is_coord
