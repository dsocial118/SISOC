import logging
from expedientespagos.models import ExpedientePago

logger = logging.getLogger("django")


class ExpedientesPagosService:
    @staticmethod
    def crear_expediente_pago(comedor, data):
        try:
            expediente_pago = ExpedientePago.objects.create(
                expediente_pago=data.get("expediente_pago"),
                resolucion_pago=data.get("resolucion_pago"),
                anexo=data.get("anexo"),
                if_cantidad_de_prestaciones=data.get("if_cantidad_de_prestaciones"),
                if_pagado=data.get("if_pagado"),
                monto=data.get("monto"),
                numero_orden_pago=data.get("numero_orden_pago"),
                fecha_pago_al_banco=data.get("fecha_pago_al_banco"),
                fecha_acreditacion=data.get("fecha_acreditacion"),
                observaciones=data.get("observaciones"),
                comedor=comedor,
            )
            return expediente_pago
        except Exception as e:
            logger.error(
                f"Error en ExpedientesPagosService.crear_expediente_pago para comedor: {comedor} {e}",
                exc_info=True,
            )
            raise

    @staticmethod
    def actualizar_expediente_pago(expediente_pago, data):
        try:
            expediente_pago.expediente_pago = data.get("expediente_pago")
            expediente_pago.resolucion_pago = data.get("resolucion_pago")
            expediente_pago.anexo = data.get("anexo")
            expediente_pago.if_cantidad_de_prestaciones = data.get(
                "if_cantidad_de_prestaciones"
            )
            expediente_pago.if_pagado = data.get("if_pagado")
            expediente_pago.monto = data.get("monto")
            expediente_pago.numero_orden_pago = data.get("numero_orden_pago")
            expediente_pago.fecha_pago_al_banco = data.get("fecha_pago_al_banco")
            expediente_pago.fecha_acreditacion = data.get("fecha_acreditacion")
            expediente_pago.observaciones = data.get("observaciones")
            expediente_pago.save()
            return expediente_pago
        except Exception as e:
            logger.error(
                f"Error en ExpedientesPagosService.actualizar_expediente_pago para comedor: {expediente_pago} {e}",
                exc_info=True,
            )
            raise

    @staticmethod
    def eliminar_expediente_pago(expediente_pago):
        try:
            expediente_pago.delete()
        except Exception as e:
            logger.error(
                f"Error en ExpedientesPagosService.eliminar_expediente_pago para comedor: {expediente_pago} {e}",
                exc_info=True,
            )
            raise

    @staticmethod
    def obtener_expedientes_pagos(comedor):
        try:
            return ExpedientePago.objects.filter(comedor=comedor)
        except Exception as e:
            logger.error(
                f"Error en ExpedientesPagosService.obtener_expedientes_pagos para comedor: {comedor} {e}",
                exc_info=True,
            )
            raise

    @staticmethod
    def obtener_expediente_pago(id_enviado):
        # Obtener un expediente de pago
        try:
            return ExpedientePago.objects.get(pk=id_enviado)
        except Exception as e:
            logger.error(
                f"Error en ExpedientesPagosService.obtener_expediente_pago para comedor: {id_enviado} {e}",
                exc_info=True,
            )
            raise
