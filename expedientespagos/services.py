import logging
from django.db.models import Case, CharField, IntegerField, Value, When
from core.services.advanced_filters import AdvancedFilterEngine
from expedientespagos.filter_config import (
    CHOICE_OPS,
    FIELD_MAP,
    FIELD_TYPES,
    TEXT_OPS,
    VINCULO_CON_ADMISION,
    VINCULO_SIN_ADMISION,
)
from expedientespagos.models import ExpedientePago
from expedientespagos.vinculacion import asignar_admision

logger = logging.getLogger("django")

EXPEDIENTES_PAGOS_ADVANCED_FILTER = AdvancedFilterEngine(
    field_map=FIELD_MAP,
    field_types=FIELD_TYPES,
    allowed_ops={"text": TEXT_OPS, "choice": CHOICE_OPS},
)


_MES_PAGO_ALIASES = (
    (1, ("enero", "1", "01")),
    (2, ("febrero", "2", "02")),
    (3, ("marzo", "3", "03")),
    (4, ("abril", "4", "04")),
    (5, ("mayo", "5", "05")),
    (6, ("junio", "6", "06")),
    (7, ("julio", "7", "07")),
    (8, ("agosto", "8", "08")),
    (9, ("septiembre", "setiembre", "9", "09")),
    (10, ("octubre", "10")),
    (11, ("noviembre", "11")),
    (12, ("diciembre", "12")),
)


def ordenar_expedientes_por_periodo_desc(queryset):
    mes_order = Case(
        *[
            When(mes_pago__iexact=alias, then=Value(numero))
            for numero, aliases in _MES_PAGO_ALIASES
            for alias in aliases
        ],
        default=Value(0),
        output_field=IntegerField(),
    )
    return queryset.annotate(_mes_pago_order=mes_order).order_by(
        "-ano", "-_mes_pago_order", "-fecha_creacion", "-id"
    )


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
                total_prestaciones=data.get("total_prestaciones"),
                gastos_accesorios=data.get("gastos_accesorios"),
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
            asignar_admision(expediente_pago, data.get("admision"))
            expediente_pago.save(update_fields=["admision"])
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
            expediente_pago.total_prestaciones = data.get("total_prestaciones")
            expediente_pago.gastos_accesorios = data.get("gastos_accesorios")
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
            asignar_admision(expediente_pago, data.get("admision"))
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
    def obtener_expedientes_pagos(comedor, request_or_query=None):
        """Expedientes de pago del comedor, con filtros combinables opcionales.

        Args:
            comedor: Comedor dueño de los expedientes.
            request_or_query: HttpRequest con los filtros, o None.

        Returns:
            QuerySet de ExpedientePago anotado con ``vinculo_admision``.
        """
        try:
            qs = (
                ExpedientePago.objects.filter(comedor=comedor)
                .select_related("admision")
                .annotate(
                    vinculo_admision=Case(
                        When(
                            admision__isnull=True,
                            then=Value(VINCULO_SIN_ADMISION),
                        ),
                        default=Value(VINCULO_CON_ADMISION),
                        output_field=CharField(),
                    )
                )
            )

            if hasattr(request_or_query, "GET"):
                qs = EXPEDIENTES_PAGOS_ADVANCED_FILTER.filter_queryset(
                    qs, request_or_query
                )

            return ordenar_expedientes_por_periodo_desc(qs)
        except Exception:
            logger.exception(
                "Error en ExpedientesPagosService.obtener_expedientes_pagos",
                extra={"comedor_pk": getattr(comedor, "pk", None)},
            )
            raise

    @staticmethod
    def contar_sin_admision(comedor):
        """Cuántos expedientes del comedor quedaron sin admisión asignada."""
        try:
            return ExpedientePago.objects.filter(
                comedor=comedor, admision__isnull=True
            ).count()
        except Exception:
            logger.exception(
                "Error en ExpedientesPagosService.contar_sin_admision",
                extra={"comedor_pk": getattr(comedor, "pk", None)},
            )
            return 0

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
