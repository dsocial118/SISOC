import logging
from django.db import connections

logger = logging.getLogger("django")


class PasService:
    """Service to fetch PA (Prestación Alimentaria) data from DW views."""

    @staticmethod
    def obtener_datos_pas(ciudadano_id):
        """
        Fetch PA data for a citizen from DW_sisoc.vw_pas_ciudadanos_resumen.

        Returns dict with:
        - resumen: dict with PA summary data
        """
        try:
            with connections["dw_sisoc"].cursor() as cursor:
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
                    FROM vw_pas_ciudadanos_resumen
                    WHERE ciudadano_id_sisoc = %s
                    """,
                    [int(ciudadano_id)],
                )
                row = cursor.fetchone()
                logger.info(f"PA data for {ciudadano_id}: {row}")
                if row:
                    return {
                        "resumen": {
                            "ciudadano_id": row[0],
                            "estado": row[1],
                            "fecha_inicio": row[2],
                            "fecha_baja": row[3],
                            "fecha_ultima_liquidacion": row[4],
                            "monto": row[5],
                            "aviso_liquidacion": row[6],
                        }
                    }
                return {"resumen": None}
        except Exception as e:
            logger.exception(
                "Error fetching PA data for ciudadano %s: %s", ciudadano_id, e
            )
            return {"resumen": None}
