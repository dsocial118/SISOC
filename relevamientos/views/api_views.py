import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api_auth import HasAPIKeyOrToken
from core.utils import format_error_detail
from relevamientos.models import PrimerSeguimiento, Relevamiento
from relevamientos.serializer import PrimerSeguimientoSerializer, RelevamientoSerializer

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


class PrimerSeguimientoApiView(APIView):
    serializer_class = PrimerSeguimientoSerializer
    permission_classes = [HasAPIKeyOrToken]

    def patch(self, request):
        sisoc_id = request.data.get("sisoc_id")
        id_relevamiento = request.data.get("id_relevamiento")
        if not sisoc_id or not id_relevamiento:
            return Response(
                "Debe informar sisoc_id e id_relevamiento.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            seguimiento = PrimerSeguimiento.objects.select_related(
                "id_relevamiento__comedor"
            ).get(id=sisoc_id)
        except PrimerSeguimiento.DoesNotExist:
            return Response(
                f"Primer seguimiento {sisoc_id} no encontrado",
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            id_relevamiento_int = int(id_relevamiento)
        except (TypeError, ValueError):
            return Response(
                "id_relevamiento invalido.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        if seguimiento.id_relevamiento_id != id_relevamiento_int:
            return Response(
                "El id_relevamiento no corresponde al primer seguimiento informado.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        seguimiento_serializer = PrimerSeguimientoSerializer(
            seguimiento,
            data=request.data,
            partial=True,
        )
        try:
            with transaction.atomic():
                try:
                    seguimiento_serializer.clean()
                except DjangoValidationError as clean_error:
                    logger.exception("Error en clean() de primer seguimiento")
                    detail = getattr(clean_error, "message_dict", None) or getattr(
                        clean_error, "messages", clean_error
                    )
                    raise ValidationError(detail) from clean_error
                seguimiento_serializer.is_valid(raise_exception=True)
                seguimiento_serializer.save()
        except ValidationError as exc:
            error_message_str = format_error_detail(getattr(exc, "detail", exc))
            return Response(
                f"Error en primer seguimiento: '{error_message_str}'",
                status=status.HTTP_400_BAD_REQUEST,
            )

        logger.info(
            "Primer seguimiento %s actualizado correctamente",
            seguimiento_serializer.instance.id,
        )
        return Response(
            PrimerSeguimientoSerializer(seguimiento_serializer.instance).data,
            status=status.HTTP_200_OK,
        )
