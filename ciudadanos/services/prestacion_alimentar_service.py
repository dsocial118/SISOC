import logging
from django.db import connections

logger = logging.getLogger("django")


class PrestacionAlimentarService:
    """Service to fetch Prestación Alimentar data from DW."""

    @staticmethod
    def obtener_prestacion_alimentar(ciudadano_id):
        """Fetch Prestación Alimentar data from vw_PA_ciudadanos_resumen."""
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
                    FROM vw_PA_ciudadanos_resumen
                    WHERE ciudadano_id_sisoc = %s
                    """,
                    [int(ciudadano_id)],
                )
                rows = cursor.fetchall()
                programas = []
                for row in rows:
                    programas.append({
                        "rol_desc": row[1],
                        "monto": row[2],
                        "periodo_mes": row[3],
                        "id_relacion_titular": row[4],
                    })
                return {"programas": programas}
        except Exception as e:
            logger.exception("Error fetching Prestación Alimentar for ciudadano %s: %s", ciudadano_id, e)
            return {"programas": []}
