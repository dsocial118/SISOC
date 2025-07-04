from rendicioncuentasmensual.models import RendicionCuentaMensual


class RendicionCuentaMensualService:
    @staticmethod
    def crear_rendicion_cuenta_mensual(comedor, data):
        rendicion = RendicionCuentaMensual.objects.create(
            comedor=comedor,
            mes=data.get("mes"),
            anio=data.get("anio"),
            documento_adjunto=data.get("documento_adjunto"),
            observaciones=data.get("observaciones"),
            arvhios_adjuntos=data.get("arvhios_adjuntos"),
        )
        return rendicion

    @staticmethod
    def actualizar_rendicion_cuenta_mensual(rendicion, data):
        rendicion.mes = data.get("mes")
        rendicion.anio = data.get("anio")
        rendicion.documento_adjunto = data.get("documento_adjunto")
        rendicion.observaciones = data.get("observaciones")
        rendicion.arvhios_adjuntos = data.get("arvhios_adjuntos")
        rendicion.save()
        return rendicion

    @staticmethod
    def eliminar_rendicion_cuenta_mensual(rendicion):
        rendicion.delete()

    @staticmethod
    def obtener_rendiciones_cuentas_mensuales(comedor):
        return RendicionCuentaMensual.objects.filter(comedor=comedor).prefetch_related(
            "arvhios_adjuntos"
        )

    @staticmethod
    def obtener_rendicion_cuenta_mensual(id_enviado):
        return RendicionCuentaMensual.objects.get(pk=id_enviado)

    # TODO: Cambiar nombre y añadir verbo
    @staticmethod
    def cantidad_rendiciones_cuentas_mensuales(comedor):
        return RendicionCuentaMensual.objects.filter(comedor=comedor).count()
