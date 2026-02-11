import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api_auth import HasAPIKeyOrToken
from core.utils import format_error_detail
from relevamientos.models import Relevamiento
from relevamientos.serializer import RelevamientoSerializer

logger = logging.getLogger("django")


class RelevamientoApiView(APIView):
    serializer_class = RelevamientoSerializer
    permission_classes = [HasAPIKeyOrToken]

    def patch(self, request):
        relevamiento_serializer = None
        try:
            relevamiento = Relevamiento.objects.get(
                id=request.data["sisoc_id"],
            )
            try:
                relevamiento_serializer = RelevamientoSerializer(
                    relevamiento, data=request.data, partial=True
                )
                with transaction.atomic():
                    try:
                        relevamiento_serializer.clean()
                    except DjangoValidationError as clean_error:
                        logger.exception(f"Error en clean(): {clean_error}")
                        raise ValidationError(clean_error.message_dict) from clean_error
                    except ValidationError:
                        raise
                    except Exception as clean_error:
                        logger.exception(f"Error en clean(): {clean_error}")
                        raise ValidationError(
                            {"non_field_errors": [str(clean_error)]}
                        ) from clean_error
                    relevamiento_serializer.is_valid(raise_exception=True)
                    relevamiento_serializer.save()
                    relevamiento = relevamiento_serializer.instance
            except ValidationError as exc:
                error_message_str = format_error_detail(getattr(exc, "detail", exc))
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
