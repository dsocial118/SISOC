"""
ViewSets para la API REST de Comunicados (PWA).
"""
from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from core.api_auth import HasAPIKey
from .models import Comunicado, TipoComunicado, EstadoComunicado
from .serializers import ComunicadoSerializer


class ComunicadoComedorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint para que la PWA obtenga comunicados de un comedor.

    GET /api/comunicados/comedor/{comedor_id}/
    """

    serializer_class = ComunicadoSerializer
    permission_classes = [HasAPIKey | IsAuthenticated]

    def get_queryset(self):
        comedor_id = self.kwargs.get('comedor_id')
        return Comunicado.objects.filter(
            tipo=TipoComunicado.EXTERNO,
            estado=EstadoComunicado.PUBLICADO,
            comedores__id=comedor_id
        ).filter(
            Q(fecha_vencimiento__isnull=True) |
            Q(fecha_vencimiento__gt=timezone.now())
        ).prefetch_related('adjuntos').distinct().order_by('-fecha_publicacion')
