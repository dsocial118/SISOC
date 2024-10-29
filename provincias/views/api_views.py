from rest_framework import viewsets
from provincias.models import AnexoSocioProductivo
from provincias.serializers import AnexoSocioProductivoSerializer


class AnexoSocioProductivoViewSet(viewsets.ModelViewSet):
    queryset = AnexoSocioProductivo.objects.all()
    serializer_class = AnexoSocioProductivoSerializer
