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

    @staticmethod
    def _resolve_seguimiento(data):
        """Resuelve el PrimerSeguimiento por cualquiera de los identificadores
        que GESTIONAR puede enviar: sisoc_id (PK SISOC), gestionar_id /
        ID_Seguimiento1 (PK GESTIONAR) o id_relevamiento (FK al ancla).
        Retorna (seguimiento, error_response). Si los identificadores
        informados refieren a distintos registros, retorna 400.
        """
        sisoc_id = data.get("sisoc_id") or data.get("Id_SISOC")
        gestionar_id = data.get("gestionar_id") or data.get("ID_Seguimiento1")
        id_relevamiento = data.get("id_relevamiento") or data.get("Id_Relevamiento")

        if not any([sisoc_id, gestionar_id, id_relevamiento]):
            return None, Response(
                "Debe informar al menos uno de: sisoc_id, gestionar_id o "
                "id_relevamiento.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = PrimerSeguimiento.objects.select_related(
            "id_relevamiento__comedor"
        )
        try:
            if sisoc_id:
                seguimiento = queryset.get(id=int(sisoc_id))
            elif gestionar_id:
                seguimiento = queryset.get(gestionar_id=str(gestionar_id).strip())
            else:
                seguimiento = queryset.get(
                    id_relevamiento_id=int(id_relevamiento)
                )
        except (TypeError, ValueError):
            return None, Response(
                "Identificador invalido.",
                status=status.HTTP_400_BAD_REQUEST,
            )
        except PrimerSeguimiento.DoesNotExist:
            ref = sisoc_id or gestionar_id or id_relevamiento
            return None, Response(
                f"Primer seguimiento {ref} no encontrado",
                status=status.HTTP_404_NOT_FOUND,
            )

        if sisoc_id and seguimiento.id != int(sisoc_id):
            return None, Response(
                "El sisoc_id informado no coincide con el seguimiento resuelto.",
                status=status.HTTP_400_BAD_REQUEST,
            )
        if gestionar_id and seguimiento.gestionar_id != str(gestionar_id).strip():
            return None, Response(
                "El gestionar_id informado no coincide con el seguimiento "
                "resuelto.",
                status=status.HTTP_400_BAD_REQUEST,
            )
        if id_relevamiento and seguimiento.id_relevamiento_id != int(
            id_relevamiento
        ):
            return None, Response(
                "El id_relevamiento informado no coincide con el seguimiento "
                "resuelto.",
                status=status.HTTP_400_BAD_REQUEST,
            )
        return seguimiento, None

    def patch(self, request):
        seguimiento, error_response = self._resolve_seguimiento(request.data)
        if error_response is not None:
            return error_response

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
