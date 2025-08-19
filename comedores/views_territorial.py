"""
Vistas para gestión de territoriales con cache.
"""

import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from comedores.services.territorial_service import TerritorialService

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def obtener_territoriales_api(request, comedor_id):
    """
    API endpoint para obtener territoriales con cache híbrido.

    Query params opcionales:
    - force_sync: 'true' para forzar sincronización con GESTIONAR
    """
    try:
        forzar_sync = request.GET.get("force_sync", "false").lower() == "true"

        resultado = TerritorialService.obtener_territoriales_para_comedor(
            comedor_id=comedor_id, forzar_sync=forzar_sync
        )

        response_data = {
            "success": True,
            "territoriales": resultado["territoriales"],
            "meta": {
                "desactualizados": resultado["desactualizados"],
                "fuente": resultado["fuente"],
                "total": len(resultado["territoriales"]),
            },
        }

        response = JsonResponse(response_data)

        if not resultado["desactualizados"]:
            # Cache en navegador por 10 minutos si los datos están actualizados
            response["Cache-Control"] = "public, max-age=600"
        else:
            # No cachear en navegador si los datos están desactualizados
            response["Cache-Control"] = "no-cache"

        return response

    except Exception as e:
        logger.error(
            f"Error en obtener_territoriales_api para comedor {comedor_id}: {e}",
            exc_info=True,
        )

        return JsonResponse(
            {
                "success": False,
                "error": "Error interno del servidor",
                "territoriales": [],
                "meta": {"desactualizados": True, "fuente": "error", "total": 0},
            },
            status=500,
        )


@login_required
@require_http_methods(["POST"])
def sincronizar_territoriales_api(request, comedor_id):
    """
    Endpoint para forzar sincronización con GESTIONAR.
    """
    try:
        resultado = TerritorialService.obtener_territoriales_para_comedor(
            comedor_id=comedor_id, forzar_sync=True
        )

        return JsonResponse(
            {
                "success": True,
                "mensaje": "Sincronización completada",
                "territoriales": resultado["territoriales"],
                "meta": {
                    "desactualizados": resultado["desactualizados"],
                    "fuente": resultado["fuente"],
                    "total": len(resultado["territoriales"]),
                },
            }
        )

    except Exception as e:
        logger.error(f"Error en sincronizar_territoriales_api: {e}", exc_info=True)

        return JsonResponse(
            {
                "success": False,
                "error": "Error en la sincronización",
                "mensaje": str(e),
            },
            status=500,
        )


@login_required
@require_http_methods(["GET"])
def estadisticas_cache_territoriales(request):
    """
    Endpoint para obtener estadísticas del cache de territoriales.
    Solo para administradores.
    """
    if not request.user.is_staff:
        return JsonResponse({"error": "Acceso denegado"}, status=403)

    try:
        stats = TerritorialService.obtener_estadisticas_cache()

        return JsonResponse({"success": True, "estadisticas": stats})

    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de cache: {e}", exc_info=True)

        return JsonResponse(
            {"success": False, "error": "Error obteniendo estadísticas"}, status=500
        )
