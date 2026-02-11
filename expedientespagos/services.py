import logging
from expedientespagos.models import ExpedientePago

logger = logging.getLogger("django")


class ExpedientesPagosService:
    @staticmethod
    def crear_expediente_pago(comedor, data):
        try:
            expediente_pago = ExpedientePago.objects.create(
                expediente_pago=data.get("expediente_pago"),
                expediente_convenio=data.get("expediente_convenio"),
                anexo=data.get("anexo"),
                if_cantidad_de_prestaciones=data.get("if_cantidad_de_prestaciones"),
                if_pagado=data.get("if_pagado"),
                total=data.get("total"),
                mes_pago=data.get("mes_pago"),
                ano=data.get("ano"),
                organizacion_creacion=data.get("organizacion_creacion"),
                numero_orden_pago=data.get("numero_orden_pago"),
                fecha_pago_al_banco=data.get("fecha_pago_al_banco"),
                fecha_acreditacion=data.get("fecha_acreditacion"),
                observaciones=data.get("observaciones"),
                prestaciones_mensuales_desayuno=data.get(
                    "prestaciones_mensuales_desayuno"
                ),
                prestaciones_mensuales_almuerzo=data.get(
                    "prestaciones_mensuales_almuerzo"
                ),
                prestaciones_mensuales_merienda=data.get(
                    "prestaciones_mensuales_merienda"
                ),
                prestaciones_mensuales_cena=data.get("prestaciones_mensuales_cena"),
                monto_mensual_desayuno=data.get("monto_mensual_desayuno"),
                monto_mensual_almuerzo=data.get("monto_mensual_almuerzo"),
                monto_mensual_merienda=data.get("monto_mensual_merienda"),
                monto_mensual_cena=data.get("monto_mensual_cena"),
                comedor=comedor,
            )
            return expediente_pago
        except Exception:
            logger.exception(
                "Error en ExpedientesPagosService.crear_expediente_pago",
                extra={"comedor_pk": getattr(comedor, "pk", None)},
            )
            raise

    @staticmethod
    def actualizar_expediente_pago(expediente_pago, data):
        try:
            expediente_pago.expediente_pago = data.get("expediente_pago")
            expediente_pago.expediente_convenio = data.get("expediente_convenio")
            expediente_pago.anexo = data.get("anexo")
            expediente_pago.if_cantidad_de_prestaciones = data.get(
                "if_cantidad_de_prestaciones"
            )
            expediente_pago.if_pagado = data.get("if_pagado")
            expediente_pago.total = data.get("total")
            expediente_pago.mes_pago = data.get("mes_pago")
            expediente_pago.ano = data.get("ano")
            expediente_pago.organizacion_creacion = data.get("organizacion_creacion")
            expediente_pago.numero_orden_pago = data.get("numero_orden_pago")
            expediente_pago.fecha_pago_al_banco = data.get("fecha_pago_al_banco")
            expediente_pago.fecha_acreditacion = data.get("fecha_acreditacion")
            expediente_pago.observaciones = data.get("observaciones")
            expediente_pago.prestaciones_mensuales_desayuno = data.get(
                "prestaciones_mensuales_desayuno"
            )
            expediente_pago.prestaciones_mensuales_almuerzo = data.get(
                "prestaciones_mensuales_almuerzo"
            )
            expediente_pago.prestaciones_mensuales_merienda = data.get(
                "prestaciones_mensuales_merienda"
            )
            expediente_pago.prestaciones_mensuales_cena = data.get(
                "prestaciones_mensuales_cena"
            )
            expediente_pago.monto_mensual_desayuno = data.get("monto_mensual_desayuno")
            expediente_pago.monto_mensual_almuerzo = data.get("monto_mensual_almuerzo")
            expediente_pago.monto_mensual_merienda = data.get("monto_mensual_merienda")
            expediente_pago.monto_mensual_cena = data.get("monto_mensual_cena")
            expediente_pago.save()
            return expediente_pago
        except Exception:
            logger.exception(
                "Error en ExpedientesPagosService.actualizar_expediente_pago",
                extra={"expediente_pago_pk": getattr(expediente_pago, "pk", None)},
            )
            raise

    @staticmethod
    def eliminar_expediente_pago(expediente_pago):
        try:
            expediente_pago.delete()
        except Exception:
            logger.exception(
                "Error en ExpedientesPagosService.eliminar_expediente_pago",
                extra={"expediente_pago_pk": getattr(expediente_pago, "pk", None)},
            )
            raise

    @staticmethod
    def obtener_expedientes_pagos(comedor):
        try:
            return ExpedientePago.objects.filter(comedor=comedor)
        except Exception:
            logger.exception(
                "Error en ExpedientesPagosService.obtener_expedientes_pagos",
                extra={"comedor_pk": getattr(comedor, "pk", None)},
            )
            raise

    @staticmethod
    def obtener_expediente_pago(id_enviado):
        # Obtener un expediente de pago
        try:
            return ExpedientePago.objects.get(pk=id_enviado)
        except Exception:
            logger.exception(
                "Error en ExpedientesPagosService.obtener_expediente_pago",
                extra={"expediente_pago_pk": id_enviado},
            )
            raise
