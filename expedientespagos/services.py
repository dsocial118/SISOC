from expedientespagos.models import ExpedientePago


class ExpedientesPagosService:
    @staticmethod
    def crear_expediente_pago(comedor, data):
        # Crear un nuevo expediente de pago
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

    @staticmethod
    def actualizar_expediente_pago(expediente_pago, data):
        # Actualizar un expediente de pago existente
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

    @staticmethod
    def eliminar_expediente_pago(expediente_pago):
        # Eliminar un expediente de pago
        expediente_pago.delete()

    @staticmethod
    def obtener_expedientes_pagos(comedor):
        # Obtener todos los expedientes de pago para un comedor
        return ExpedientePago.objects.filter(comedor=comedor)

    @staticmethod
    def obtener_expediente_pago(id_enviado):
        # Obtener un expediente de pago
        return ExpedientePago.objects.get(pk=id_enviado)
