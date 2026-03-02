import logging
from django.shortcuts import get_object_or_404
from rendicioncuentasmensual.models import RendicionCuentaMensual

logger = logging.getLogger("django")


class RendicionCuentaMensualService:
    @staticmethod
    def _get_archivos_adjuntos_data(data):
        return data.get("archivos_adjuntos", data.get("arvhios_adjuntos"))

    @staticmethod
    def _asignar_archivos_adjuntos(rendicion, archivos_adjuntos):
        if archivos_adjuntos is None:
            return

        manager = getattr(rendicion, "archivos_adjuntos", None)
        if hasattr(manager, "set"):
            manager.set(archivos_adjuntos)
            return

        # Compatibilidad con tests unitarios que usan SimpleNamespace.
        setattr(rendicion, "archivos_adjuntos", archivos_adjuntos)

    @staticmethod
    def crear_rendicion_cuenta_mensual(comedor, data):
        try:
            archivos_adjuntos = (
                RendicionCuentaMensualService._get_archivos_adjuntos_data(data)
            )
            rendicion = RendicionCuentaMensual.objects.create(
                comedor=comedor,
                mes=data.get("mes"),
                anio=data.get("anio"),
                documento_adjunto=data.get("documento_adjunto"),
                observaciones=data.get("observaciones"),
            )
            RendicionCuentaMensualService._asignar_archivos_adjuntos(
                rendicion, archivos_adjuntos
            )
            return rendicion
        except Exception:
            logger.exception(
                "Error en RendicionCuentaMensualService.crear_rendicion_cuenta_mensual",
                extra={"comedor_pk": getattr(comedor, "pk", None)},
            )
            raise

    @staticmethod
    def actualizar_rendicion_cuenta_mensual(rendicion, data):
        try:
            archivos_adjuntos = (
                RendicionCuentaMensualService._get_archivos_adjuntos_data(data)
            )
            rendicion.mes = data.get("mes")
            rendicion.anio = data.get("anio")
            rendicion.documento_adjunto = data.get("documento_adjunto")
            rendicion.observaciones = data.get("observaciones")
            RendicionCuentaMensualService._asignar_archivos_adjuntos(
                rendicion, archivos_adjuntos
            )
            rendicion.save()
            return rendicion
        except Exception:
            logger.exception(
                "Error en RendicionCuentaMensualService.actualizar_rendicion_cuenta_mensual",
                extra={"rendicion_pk": getattr(rendicion, "pk", None)},
            )
            raise

    @staticmethod
    def eliminar_rendicion_cuenta_mensual(rendicion):
        try:
            rendicion.delete()
        except Exception:
            logger.exception(
                "Error en RendicionCuentaMensualService.eliminar_rendicion_cuenta_mensual",
                extra={"rendicion_pk": getattr(rendicion, "pk", None)},
            )
            raise

    @staticmethod
    def obtener_rendiciones_cuentas_mensuales(comedor):
        try:
            return RendicionCuentaMensual.objects.filter(
                comedor=comedor
            ).prefetch_related("archivos_adjuntos")
        except Exception:
            logger.exception(
                "Error en RendicionCuentaMensualService.obtener_rendiciones_cuentas_mensuales",
                extra={"comedor_pk": getattr(comedor, "pk", None)},
            )
            raise

    @staticmethod
    def obtener_rendicion_cuenta_mensual(id_enviado):
        try:
            return get_object_or_404(RendicionCuentaMensual, pk=id_enviado)
        except Exception:
            logger.exception(
                f"Error en RendicionCuentaMensualService.obtener_rendicion_cuenta_mensual para {id_enviado}"
            )
            raise

    # TODO: Cambiar nombre y añadir verbo
    @staticmethod
    def cantidad_rendiciones_cuentas_mensuales(comedor):
        try:
            return RendicionCuentaMensual.objects.filter(comedor=comedor).count()
        except Exception:
            logger.exception(
                "Error en RendicionCuentaMensualService.cantidad_rendiciones_cuentas_mensuales",
                extra={"comedor_pk": getattr(comedor, "pk", None)},
            )
            raise
