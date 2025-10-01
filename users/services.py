import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count
from django.shortcuts import get_object_or_404
from users.models import Profile
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
        base_qs = UsuariosService.get_beneficiarios_queryset()
        return BENEFICIARIO_ADVANCED_FILTER.filter_queryset(base_qs, request_or_get)

    @staticmethod
    def get_beneficiarios_queryset():
        """Query optimizada para usuarios"""
        return Profile.objects.select_related(
            "responsable", "provincia", "municipio"
        ).order_by("-id", "apellido", "nombre")
    
    @staticmethod
    def get_usuarios_list_context():
        """Configuración para la lista de usuarios"""
        return {
            "table_headers": [
                {"title": "CUIL", "width": "12%"},
                {"title": "Apellido y Nombre", "width": "20%"},
                {"title": "DNI", "width": "10%"},
                {"title": "Género", "width": "8%"},
                {"title": "Responsable", "width": "20%"},
                {"title": "Provincia", "width": "15%"},
                {"title": "Municipio", "width": "15%"},
            ],
            "table_fields": [
                {"name": "cuil"},
                {"name": "apellido_nombre"},
                {"name": "dni"},
                {"name": "genero_display"},
                {"name": "responsable_nombre"},
                {"name": "provincia"},
                {"name": "municipio"},
            ],
            "table_actions": [
                {
                    "url_name": "beneficiarios_detail",
                    "type": "info",
                    "label": "Ver",
                    "class": "btn-sm",
                },
            ],
        }