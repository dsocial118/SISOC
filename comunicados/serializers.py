"""
Serializers para la API REST de Comunicados.
"""

from rest_framework import serializers
from .models import Comunicado, ComunicadoAdjunto


class ComunicadoAdjuntoSerializer(serializers.ModelSerializer):
    """Serializer para archivos adjuntos de comunicados."""

    class Meta:
        model = ComunicadoAdjunto
        fields = ["id", "archivo", "nombre_original"]


class ComunicadoSerializer(serializers.ModelSerializer):
    """Serializer para comunicados (lectura para PWA)."""

    adjuntos = ComunicadoAdjuntoSerializer(many=True, read_only=True)

    class Meta:
        model = Comunicado
        fields = [
            "id",
            "titulo",
            "cuerpo",
            "estado",
            "subtipo",
            "fecha_publicacion",
            "fecha_vencimiento",
            "adjuntos",
        ]
