"""Variables documentales derivadas para templates de Informes Técnicos."""

from django.db.models import Q
from django.utils.html import format_html_join

from admisiones.models.admisiones import Admision
from comedores.services.comedor_service import ComedorService


class InformeTecnicoVariablesDocumentalesService:
    """Resuelve valores históricos sin persistir copias en el informe actual."""

    DIAS = (
        "lunes",
        "martes",
        "miercoles",
        "jueves",
        "viernes",
        "sabado",
        "domingo",
    )
    COMIDAS = ("desayuno", "almuerzo", "merienda", "cena")
    ESTADOS_DESCARTADOS = ("descartado", "inactivada")
    ESTADOS_LEGALES_DESCARTADOS = ("Descartado", "Inactivada")

    @classmethod
    def enriquecer_informe(cls, informe):
        """Agrega atributos de sólo lectura para ``{{ informe.<variable> }}``."""

        valores = cls.obtener_valores(informe)
        for nombre, valor in valores.items():
            setattr(informe, nombre, valor)
        return informe

    @classmethod
    def obtener_valores(cls, informe):
        """Construye el catálogo documental; los datos ausentes quedan vacíos."""

        valores = cls._valores_vacios()
        if not informe or not getattr(informe, "admision_id", None):
            return valores

        admision_actual = informe.admision
        admisiones_anteriores = cls._admisiones_anteriores(admision_actual)
        ultima_admision = admisiones_anteriores.order_by("-creado", "-pk").first()
        ultima_incorporacion = (
            admisiones_anteriores.filter(tipo="incorporacion")
            .order_by("-creado", "-pk")
            .first()
        )
        renovaciones_anteriores = admisiones_anteriores.filter(
            tipo="renovacion"
        ).order_by("creado", "pk")

        valores.update(
            {
                "resolucion_o_disposicion_incorporacion": cls._texto(
                    getattr(ultima_incorporacion, "numero_disposicion", "")
                ),
                "renovaciones_anteriores_detalladas": cls._formatear_renovaciones(
                    renovaciones_anteriores
                ),
                "referencia_itcomp_modificacion_prestaciones": cls._texto(
                    getattr(informe, "if_it_complementario", "")
                ),
                "expediente_pago_en_curso": cls._texto(
                    getattr(ultima_admision, "num_expediente", "")
                ),
                "expediente_ultimo_convenio": cls._texto(
                    getattr(ultima_admision, "num_expediente", "")
                ),
            }
        )
        valores.update(cls._totales_semanales(informe, "total_semanal_actual"))

        informe_ultimo_convenio = (
            ComedorService.get_informe_tecnico_finalizado_efectivo(ultima_admision)
            if ultima_admision
            else None
        )
        if informe_ultimo_convenio:
            valores.update(
                cls._totales_semanales(
                    informe_ultimo_convenio,
                    "total_semanal_ultimo_convenio",
                )
            )
        return valores

    @classmethod
    def _admisiones_anteriores(cls, admision_actual):
        """Antecedentes válidos del mismo comedor, anteriores al trámite actual."""

        if not getattr(admision_actual, "comedor_id", None):
            return Admision.objects.none()

        criterio_anterior = Q(creado__lt=admision_actual.creado) | Q(
            creado=admision_actual.creado,
            pk__lt=admision_actual.pk,
        )
        return (
            Admision.objects.filter(
                comedor_id=admision_actual.comedor_id,
                activa=True,
            )
            .filter(criterio_anterior)
            .exclude(estado_admision__in=cls.ESTADOS_DESCARTADOS)
            .exclude(estado_legales__in=cls.ESTADOS_LEGALES_DESCARTADOS)
        )

    @classmethod
    def _totales_semanales(cls, informe, prefijo):
        return {
            f"{prefijo}_{comida}s": str(
                sum(
                    getattr(informe, f"aprobadas_{comida}_{dia}", 0) or 0
                    for dia in cls.DIAS
                )
            )
            for comida in cls.COMIDAS
        }

    @classmethod
    def _valores_vacios(cls):
        valores = {
            "resolucion_o_disposicion_incorporacion": "",
            "renovaciones_anteriores_detalladas": "",
            "referencia_itcomp_modificacion_prestaciones": "",
            "expediente_pago_en_curso": "",
            "expediente_ultimo_convenio": "",
        }
        for prefijo in (
            "total_semanal_ultimo_convenio",
            "total_semanal_actual",
        ):
            for comida in cls.COMIDAS:
                valores[f"{prefijo}_{comida}s"] = ""
        return valores

    @staticmethod
    def _texto(valor):
        return str(valor or "")

    @classmethod
    def _formatear_renovaciones(cls, renovaciones):
        return format_html_join(
            "<br>",
            "Resolución / Disposición: {}; Convenio: {}; Expediente: {}",
            (
                (
                    cls._texto(renovacion.numero_disposicion),
                    cls._texto(renovacion.numero_convenio),
                    cls._texto(renovacion.num_expediente),
                )
                for renovacion in renovaciones
            ),
        )
