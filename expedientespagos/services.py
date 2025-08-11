from expedientespagos.models import ExpedientePago
import logging

logger = logging.getLogger(__name__)


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
                f"Ocurrió un error inesperado en ExpedientesPagosService.crear_expediente_pago para comedor: {comedor} {e}",
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
                f"Ocurrió un error inesperado en ExpedientesPagosService.crear_expediente_pago para expediente:{expediente_pago} {data} {e}",
                exc_info=True,
            )
            raise

    @staticmethod
    def eliminar_expediente_pago(expediente_pago):
        try:
            expediente_pago.delete()
        except Exception as e:
            logger.error(
                f"Ocurrió un error inesperado en ExpedientesPagosService.eliminar_expediente_pago para expediente:{expediente_pago} {e}",
                exc_info=True,
            )
            raise

    @staticmethod
    def obtener_expedientes_pagos(comedor):
        try:
            return ExpedientePago.objects.filter(comedor=comedor)
        except Exception as e:
            logger.error(
                f"Ocurrió un error inesperado en ExpedientesPagosService.eliminar_expediente_pago para comedor:{comedor} {e}",
                exc_info=True,
            )
            raise

    @staticmethod
    def obtener_expediente_pago(id_enviado):
        try:
            return ExpedientePago.objects.get(pk=id_enviado)
        except ExpedientePago.DoesNotExist:
            logger.error(
                "ExpedientePago no encontrado en obtener_expediente_pago", exc_info=True
            )
            return None
        except Exception as e:
            logger.error(
                f"Ocurrió un error inesperado en ExpedientesPagosService.eliminar_expediente_pago para expediente:{id_enviado} {e}",
                exc_info=True,
            )
            raise
