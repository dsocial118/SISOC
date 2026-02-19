"""
ViewSets para la API REST de Comunicados (PWA).
"""
from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from core.api_auth import HasAPIKey
from .models import Comunicado, TipoComunicado, SubtipoComunicado, EstadoComunicado
from .serializers import ComunicadoSerializer


class ComunicadoInstitucionalViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint para comunicados institucionales (broadcast).
    PWA - Módulo Institucional.

    GET /api/comunicados/institucional/
    """

    serializer_class = ComunicadoSerializer
    permission_classes = [HasAPIKey | IsAuthenticated]

    def get_queryset(self):
        return Comunicado.objects.filter(
            tipo=TipoComunicado.EXTERNO,
            subtipo=SubtipoComunicado.INSTITUCIONAL,
            estado=EstadoComunicado.PUBLICADO,
        ).filter(
            Q(fecha_vencimiento__isnull=True) |
            Q(fecha_vencimiento__gt=timezone.now())
        ).prefetch_related('adjuntos').order_by('-fecha_publicacion')


class ComunicadoComedorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint para comunicados dirigidos a un comedor.
    PWA - Módulo Notificaciones.

    GET /api/comunicados/comedor/{comedor_id}/
    """

    serializer_class = ComunicadoSerializer
    permission_classes = [HasAPIKey | IsAuthenticated]

    def get_queryset(self):
        comedor_id = self.kwargs.get('comedor_id')
        return Comunicado.objects.filter(
            tipo=TipoComunicado.EXTERNO,
            subtipo=SubtipoComunicado.COMEDORES,
            estado=EstadoComunicado.PUBLICADO,
            comedores__id=comedor_id
        ).filter(
            Q(fecha_vencimiento__isnull=True) |
            Q(fecha_vencimiento__gt=timezone.now())
        ).prefetch_related('adjuntos').distinct().order_by('-fecha_publicacion')
