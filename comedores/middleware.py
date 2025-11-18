import logging

from django.core.cache import cache
from django.utils import timezone

from comedores.services.validacion_service import ValidacionService

logger = logging.getLogger(__name__)


class AutoResetValidacionesMiddleware:
    """Middleware que verifica automáticamente si es necesario resetear validaciones"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Verificar solo una vez por día para evitar múltiples checks
        cache_key = "ultimo_check_reset_validaciones"
        ultimo_check = cache.get(cache_key)
        hoy = timezone.now().date()

        if not ultimo_check or ultimo_check != hoy:
            # Solo activar a partir de diciembre 2024 (evitar reset en deploy inicial)
            if hoy >= timezone.datetime(2024, 12, 1).date():
                # Verificar si necesita reset mensual (cualquier día del mes nuevo)
                reset_key = f'reset_validaciones_{hoy.strftime("%Y_%m")}'
                if not cache.get(reset_key):
                try:
                    comedores_actualizados = (
                        ValidacionService.resetear_validaciones()
                    )
                    logger.info(
                        "Auto-reset middleware: %s comedores reseteados (mes %s, día %s)",
                        comedores_actualizados,
                        hoy.strftime("%Y-%m"),
                        hoy.day,
                    )
                    # Marcar como ejecutado este mes
                    cache.set(reset_key, True, 60 * 60 * 24 * 32)
                except Exception as exc:  # pragma: no cover
                    logger.error("Error en auto-reset middleware: %s", exc)

            # Actualizar último check
            cache.set(cache_key, hoy, 60 * 60 * 24)

        response = self.get_response(request)
        return response
