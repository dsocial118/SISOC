from typing import Dict
from dashboard.models import Dashboard
from dashboard.utils import (
    contar_adolescente_riesgo,
    contar_adolescente_sin_derivacion_aceptada,
    contar_bb_riesgo,
    contar_bb_sin_derivacion_aceptada,
    contar_embarazos_en_riesgo,
    contar_embarazos_sin_derivacion_aceptada,
    contar_legajos,
    contar_legajos_con_alarmas_activas,
    contar_legajos_con_planes_sociales,
    contar_legajos_embarazados,
    contar_legajos_entre_0_y_18_anios,
    contar_legajos_entre_0_y_40_dias,
    deriv_pendientes,
)


class DashboardService:
    @staticmethod
    def obtener_dashboard_data() -> Dict[str, int]:
        return {item.llave: item.cantidad for item in Dashboard.objects.all()}

    @staticmethod
    def actualizar_valor_via_llave(llave: str, valor: int) -> tuple[Dashboard, bool]:
        """
        Actualiza o crea un elemento del Dashboard para el concepto deseado con la cantidad recibida

        :param llave: Concepto en el Dashboard
        :param cantidad: Cantidad a definir del concepto en el Dashboard
        """
        try:
            return Dashboard.objects.update_or_create(
                llave=llave,
                defaults={"cantidad": valor},
            )
        except Exception as e:
            return e

    @staticmethod
    def ejecutar_actualizaciones_legajos() -> True:
        """
        Ejecuta todas las operaciones de legajos para que el Dashboard tenga informacion en tiempo real.
        Guarda el resultado de dichas operaciones en el modelo Dashboard.
        """
        try:
            DashboardService.actualizar_valor_via_llave(
                "cantidad_legajos_con_alarmas_activas",
                contar_legajos_con_alarmas_activas(),
            )
            DashboardService.actualizar_valor_via_llave(
                "cantidad_legajos_con_planes_sociales",
                contar_legajos_con_planes_sociales(),
            )
            cantidad_total_legajos, cantidad_legajos_activos = contar_legajos()
            DashboardService.actualizar_valor_via_llave(
                "cantidad_total_legajos", cantidad_total_legajos
            )
            DashboardService.actualizar_valor_via_llave(
                "cantidad_legajos_activos", cantidad_legajos_activos
            )
            DashboardService.actualizar_valor_via_llave(
                "cantidad_legajos_entre_0_y_18_anios",
                contar_legajos_entre_0_y_18_anios(),
            )
            DashboardService.actualizar_valor_via_llave(
                "cantidad_legajos_40_dias", contar_legajos_entre_0_y_40_dias()
            )
            DashboardService.actualizar_valor_via_llave(
                "cantidad_legajos_embarazados", contar_legajos_embarazados()
            )
            DashboardService.actualizar_valor_via_llave(
                "cantidad_bb_riesgo", contar_bb_riesgo()
            )
            DashboardService.actualizar_valor_via_llave(
                "cantidad_adolescente_riesgo", contar_adolescente_riesgo()
            )
            DashboardService.actualizar_valor_via_llave(
                "cantidad_bb_sin_derivacion_aceptada",
                contar_bb_sin_derivacion_aceptada(),
            )
            DashboardService.actualizar_valor_via_llave(
                "cantidad_adolescente_sin_derivacion_aceptada",
                contar_adolescente_sin_derivacion_aceptada(),
            )
            DashboardService.actualizar_valor_via_llave(
                "embarazos_sin_derivacion_aceptada",
                contar_embarazos_sin_derivacion_aceptada(),
            )
            DashboardService.actualizar_valor_via_llave(
                "cantidad_embarazos_en_riesgo", contar_embarazos_en_riesgo()
            )
            DashboardService.actualizar_valor_via_llave(
                "cantidad_dv_pendientes", deriv_pendientes()
            )
            return True
        except Exception as e:
            return e
