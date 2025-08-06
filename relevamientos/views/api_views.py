from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_api_key.permissions import HasAPIKey
from relevamientos.models import Relevamiento
from relevamientos.serializer import RelevamientoSerializer
from core.utils import format_serializer_errors


class RelevamientoApiView(APIView):
    permission_classes = [HasAPIKey]

    def patch(self, request):
        try:
            relevamiento = Relevamiento.objects.get(
                id=request.data["sisoc_id"],
            )
            relevamiento_serializer = RelevamientoSerializer(
                relevamiento, data=request.data, partial=True
            ).clean()
            if relevamiento_serializer.is_valid():
                relevamiento_serializer.save()
                relevamiento = relevamiento_serializer.instance
            else:
                error_message_str = format_serializer_errors(relevamiento_serializer)

                return Response(
                    f"Error en relevamiento: '{error_message_str}'",
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return Response(
                RelevamientoSerializer(relevamiento).data, status=status.HTTP_200_OK
            )
        except Relevamiento.DoesNotExist:
            return Response(
                f"Relevamiento {request.data['sisoc_id']} no encontrado",
                status=status.HTTP_404_NOT_FOUND,
            )
