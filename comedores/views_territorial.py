"""
Vistas para gestión de territoriales con cache.
"""

import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from comedores.services.comedor_service import ComedorService
from users.services_pwa import get_territorial_comedor_users_for_provincia

logger = logging.getLogger("django")


def _territoriales_sisoc_para_comedor(comedor):
    """Lista de territoriales (usuarios SISOC) con alcance en la provincia del comedor.

    Reemplaza el pull viejo desde GESTIONAR/AppSheet: ahora los territoriales son
    usuarios de SISOC (`Profile.es_territorial_comedor`) filtrados por provincia.
    Se mantiene la forma `{gestionar_uid, nombre, desactualizado}` para no romper
    el front del modal de relevamiento; `gestionar_uid` viaja con el id del user.
    """
    provincia_id = getattr(comedor, "provincia_id", None)
    territoriales = []
    for user in get_territorial_comedor_users_for_provincia(provincia_id):
        nombre = (user.get_full_name() or "").strip() or user.username
        territoriales.append(
            {
                "gestionar_uid": str(user.id),
                "nombre": nombre,
                "desactualizado": False,
            }
        )
    return territoriales


@login_required
@require_http_methods(["GET"])
def obtener_territoriales_api(request, comedor_id):
    """Territoriales asignables al comedor (usuarios SISOC por provincia)."""
    try:
        comedor = ComedorService.get_scoped_comedor_or_404(comedor_id, request.user)
        territoriales = _territoriales_sisoc_para_comedor(comedor)

        response = JsonResponse(
            {
                "success": True,
                "territoriales": territoriales,
                "meta": {
                    "desactualizados": False,
                    "fuente": "db_provincia",
                    "total": len(territoriales),
                },
            }
        )
        response["Cache-Control"] = "no-cache"
        return response

    except Exception as e:
        logger.exception(
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
    """Refresca la lista de territoriales (usuarios SISOC por provincia)."""
    try:
        comedor = ComedorService.get_scoped_comedor_or_404(comedor_id, request.user)
        territoriales = _territoriales_sisoc_para_comedor(comedor)

        return JsonResponse(
            {
                "success": True,
                "mensaje": "Lista actualizada",
                "territoriales": territoriales,
                "meta": {
                    "desactualizados": False,
                    "fuente": "db_provincia",
                    "total": len(territoriales),
                },
            }
        )

    except Exception as e:
        logger.exception(f"Error en sincronizar_territoriales_api: {e}", exc_info=True)

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
        logger.exception(f"Error obteniendo estadísticas de cache: {e}", exc_info=True)

        return JsonResponse(
            {"success": False, "error": "Error obteniendo estadísticas"}, status=500
        )
