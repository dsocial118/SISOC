from rendicioncuentasmensual.models import RendicionCuentaMensual
import logging

logger = logging.getLogger(__name__)

class RendicionCuentaMensualService:
    @staticmethod
    def crear_rendicion_cuenta_mensual(comedor, data):
        try:
            rendicion = RendicionCuentaMensual.objects.create(
                comedor=comedor,
                mes=data.get("mes"),
                anio=data.get("anio"),
                documento_adjunto=data.get("documento_adjunto"),
                observaciones=data.get("observaciones"),
                arvhios_adjuntos=data.get("arvhios_adjuntos"),
            )
            return rendicion
        except Exception as e:
            logger.error("Ocurrió un error inesperado en crear_rendicion_cuenta_mensual", exc_info=True)
            return None

    @staticmethod
    def actualizar_rendicion_cuenta_mensual(rendicion, data):
        try:
            rendicion.mes = data.get("mes")
            rendicion.anio = data.get("anio")
            rendicion.documento_adjunto = data.get("documento_adjunto")
            rendicion.observaciones = data.get("observaciones")
            rendicion.arvhios_adjuntos = data.get("arvhios_adjuntos")
            rendicion.save()
            return rendicion
        except Exception as e:
            logger.error("Ocurrió un error inesperado en actualizar_rendicion_cuenta_mensual", exc_info=True)
            return None

    @staticmethod
    def eliminar_rendicion_cuenta_mensual(rendicion):
        try:
            rendicion.delete()
        except Exception as e:
            logger.error("Ocurrió un error inesperado en eliminar_rendicion_cuenta_mensual", exc_info=True)

    @staticmethod
    def obtener_rendiciones_cuentas_mensuales(comedor):
        try:
            return RendicionCuentaMensual.objects.filter(comedor=comedor).prefetch_related(
                "arvhios_adjuntos"
            )
        except Exception as e:
            logger.error("Ocurrió un error inesperado en obtener_rendiciones_cuentas_mensuales", exc_info=True)
            return RendicionCuentaMensual.objects.none()

    @staticmethod
    def obtener_rendicion_cuenta_mensual(id_enviado):
        try:
            return RendicionCuentaMensual.objects.get(pk=id_enviado)
        except RendicionCuentaMensual.DoesNotExist:
            logger.error("RendicionCuentaMensual no encontrada en obtener_rendicion_cuenta_mensual", exc_info=True)
            return None
        except Exception as e:
            logger.error("Ocurrió un error inesperado en obtener_rendicion_cuenta_mensual", exc_info=True)
            return None

    # TODO: Cambiar nombre y añadir verbo
    @staticmethod
    def cantidad_rendiciones_cuentas_mensuales(comedor):
        try:
            return RendicionCuentaMensual.objects.filter(comedor=comedor).count()
        except Exception as e:
            logger.error("Ocurrió un error inesperado en cantidad_rendiciones_cuentas_mensuales", exc_info=True)
            return 0