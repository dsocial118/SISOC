from rest_framework import viewsets
from anexos.models import AnexoSocioProductivo
from anexos.serializers import AnexoSocioProductivoSerializer


class AnexoSocioProductivoViewSet(viewsets.ModelViewSet):
    queryset = AnexoSocioProductivo.objects.all()
    serializer_class = AnexoSocioProductivoSerializer
