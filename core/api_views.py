"""
API Views para core (proxy a RENAPER).
"""

import logging

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_api_key.permissions import HasAPIKey

# FIXME: Cuando se mergee development a main, cambiar este import a:
# from centrodefamilia.services.consulta_renaper.impl import APIClient
# (en development, consulta_renaper es un paquete, no un archivo)
from centrodefamilia.services.consulta_renaper import APIClient
from core.api_serializers import RenaperConsultaSerializer

logger = logging.getLogger("django")


class RenaperConsultaViewSet(viewsets.ViewSet):
    """
    Endpoint proxy a RENAPER.

    POST /api/renaper/consultar/
    Requiere autenticación con APIKey.
    Devuelve respuesta de RENAPER sin transformación (pass-through).
    """

    permission_classes = [HasAPIKey]

    @action(detail=False, methods=["post"])
    def consultar(self, request):
        """
        Consulta datos de un ciudadano en RENAPER.

        Request body:
        {
            "dni": "12345678",
            "sexo": "M"  (M, F o X)
        }

        Response (éxito):
        {
            "success": true,
            "data": {...datos de RENAPER...}
        }

        Response (error):
        {
            "success": false,
            "error": "Descripción del error"
        }
        """
        serializer = RenaperConsultaSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(
                f"Validación fallida en /api/renaper/consultar: {serializer.errors}"
            )
            return Response(
                {
                    "success": False,
                    "error": "Datos inválidos",
                    "details": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        dni = serializer.validated_data["dni"]
        sexo = serializer.validated_data["sexo"]

        # Log técnico (sin PII detallado)
        logger.info(
            f"Consulta RENAPER vía API: DNI hash={hash(dni) % 10000}, sexo={sexo}"
        )

        try:
            client = APIClient()
            response = client.consultar_ciudadano(dni, sexo)
        except Exception as exc:
            logger.error(f"Excepción en consulta RENAPER: {str(exc)}")
            return Response(
                {"success": False, "error": f"Error interno: {str(exc)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Pass-through: devolver respuesta del APIClient tal cual
        # (que ya contiene success, error, y data de RENAPER)
        if response.get("success"):
            return Response(
                {"success": True, "data": response.get("data")},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"success": False, "error": response.get("error", "Error desconocido")},
                status=status.HTTP_200_OK,  # RENAPER puede tener error pero HTTP 200
            )
