import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from relevamientos.models import Relevamiento
from relevamientos.serializer import RelevamientoSerializer
from core.utils import format_serializer_errors

logger = logging.getLogger("django")


class RelevamientoApiView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        try:
            relevamiento = Relevamiento.objects.get(
                id=request.data["sisoc_id"],
            )
            relevamiento_serializer = RelevamientoSerializer(
                relevamiento, data=request.data, partial=True
            )
            try:
                relevamiento_serializer.clean()
            except Exception as clean_error:
                logger.exception(f"Error en clean(): {clean_error}")
                return Response(
                    f"Error procesando datos del relevamiento: {clean_error}",
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if relevamiento_serializer.is_valid():
                relevamiento_serializer.save()
                relevamiento = relevamiento_serializer.instance
            else:
                error_message_str = format_serializer_errors(relevamiento_serializer)

                return Response(
                    f"Error en relevamiento: '{error_message_str}'",
                    status=status.HTTP_400_BAD_REQUEST,
                )

            logger.info(f"Relevamiento {relevamiento.id} actualizado correctamente")
            return Response(
                RelevamientoSerializer(relevamiento).data, status=status.HTTP_200_OK
            )
        except Relevamiento.DoesNotExist:
            return Response(
                f"Relevamiento {request.data['sisoc_id']} no encontrado",
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception:
            logger.exception(
                "Error en PATCH al relevamiento",
                extra={
                    "sisoc_id": request.data.get("sisoc_id"),
                    "data": request.data,
                },
            )
            return Response(
                f"Error al actualizar el relevamiento {request.data['sisoc_id']}",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
