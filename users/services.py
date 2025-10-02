import logging
from django.contrib.auth.models import User, Group
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count
from django.shortcuts import get_object_or_404
from users.models import Profile
from django.urls import reverse, reverse_lazy
from core.services.advanced_filters import AdvancedFilterEngine
from users.users_filter_config import (
    FIELD_MAP as BENEFICIARIO_FILTER_MAP,
    FIELD_TYPES as BENEFICIARIO_FIELD_TYPES,
    TEXT_OPS as BENEFICIARIO_TEXT_OPS,
    NUM_OPS as BENEFICIARIO_NUM_OPS,
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
        return User.objects.select_related("profile").order_by("-id")

    @staticmethod
    def get_usuarios_list_context():
        """Configuración para la lista de usuarios"""
        return {
            "table_headers": [
                {"title": "Nombre", "width": "12%"},
                {"title": "Apellido y Nombre", "width": "20%"},
                {"title": "Username", "width": "10%"},
                {"title": "Email", "width": "8%"},
                {"title": "Rol", "width": "20%"},
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
                    "type": "primary",
                    "class": "editar",
                },
                {
                    "label": "Eliminar",
                    "url_name": "usuario_borrar",
                    "type": "danger",
                    "class": "eliminar",
                },
            ],
            "breadcrumb_items": [
                {"text": "Usuarios", "url": reverse("usuarios")},
                {"text": "Listar", "active": True},
            ],
            "reset_url": reverse("usuarios"),
            "add_url": reverse("usuario_crear"),
            "filters_mode": True,
            "filters_js": "custom/js/usuarios_search_bar.js",
            "filters_action": reverse("usuarios"),
            "show_add_button": True,
        }
