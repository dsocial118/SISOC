import logging
from django.db import connections

logger = logging.getLogger("django")


class PasService:
    """Service to fetch PAS (Prestación Alimentaria) data from DW views."""

    @staticmethod
    def obtener_datos_pas(ciudadano_id):
        """
        Fetch PAS data for a citizen from DW views.
        
        Returns dict with:
        - resumen: data from vw_pas_ciudadanos_resumen
        - programas: data from vw_PA_ciudadanos_resumen
        """
        try:
            with connections["dw_sisoc"].cursor() as cursor:
                # Get PAS summary data
                cursor.execute(
                    """
                    SELECT 
                        ciudadano_id_sisoc,
                        UltimoEstadoPas,
                        FechaInicioPas,
                        FechaBajaPas,
                        FechaUltimaLiquidacion,
                        monto,
                        AvisoLiquidacion
                    FROM DW_sisoc.vw_pas_ciudadanos_resumen
                    WHERE ciudadano_id_sisoc = %s
                    """,
                    [ciudadano_id],
                )
                resumen = cursor.fetchone()

                # Get PA programs data
                cursor.execute(
                    """
                    SELECT 
                        ciudadano_id_sisoc,
                        ciudadano_programa_rol_desc,
                        monto,
                        periodo_mes,
                        idSisocRelacionTitular
                    FROM DW_sisoc.vw_PA_ciudadanos_resumen
                    WHERE ciudadano_id_sisoc = %s
                    ORDER BY periodo_mes DESC
                    """,
                    [ciudadano_id],
                )
                programas = cursor.fetchall()

                return {
                    "resumen": resumen,
                    "programas": programas,
                }
        except Exception as e:
            logger.exception("Error fetching PAS data for ciudadano %s: %s", ciudadano_id, e)
            return {"error": str(e), "resumen": None, "programas": []}

    @staticmethod
    def obtener_historial_pas(ciudadano_id, meses=12):
        """Fetch historical PAS data for the last N months."""
        try:
            with connections["dw_sisoc"].cursor() as cursor:
                cursor.execute(
                    """
                    SELECT 
                        ciudadano_id_sisoc,
                        ciudadano_programa_rol_desc,
                        monto,
                        periodo_mes,
                        idSisocRelacionTitular
                    FROM DW_sisoc.vw_PA_ciudadanos_resumen
                    WHERE ciudadano_id_sisoc = %s
                    ORDER BY periodo_mes DESC
                    LIMIT %s
                    """,
                    [ciudadano_id, meses],
                )
                return cursor.fetchall()
        except Exception as e:
            logger.exception("Error fetching PAS history for ciudadano %s: %s", ciudadano_id, e)
            return []
