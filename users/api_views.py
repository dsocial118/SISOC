from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.response import Response

from core.api_auth import HasAPIKey
from users.api_serializers import UserContextSerializer


@extend_schema(tags=["Auth"])
class UserContextViewSet(viewsets.ViewSet):
    permission_classes = [HasAPIKey]

    @extend_schema(responses=UserContextSerializer)
    def list(self, request):
        if not getattr(request.user, "is_authenticated", False):
            return Response(
                {"detail": "User authentication required."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        serializer = UserContextSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
