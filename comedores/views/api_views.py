from django.forms.models import model_to_dict
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_api_key.permissions import HasAPIKey
from comedores.models.relevamiento import Relevamiento
from comedores.models.comedor import Comedor, Observacion
from comedores.serializers.comedor_serializer import ComedorSerializer
from comedores.serializers.relevamiento_serializer import RelevamientoSerializer
from comedores.serializers.observacion_serializer import ObservacionSerializer
from comedores.services.comedor_service import ComedorService
from comedores.utils import format_serializer_errors, format_fecha_django


class RelevamientoApiView(APIView):
    permission_classes = [HasAPIKey]

    def patch(self, request):
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
