import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, List

from django.db import connection

logger = logging.getLogger(__name__)


@dataclass
class DWTransaccion:
    """Representa una transacción de la vista DW_sisoc.vw_EC_resumen_transacciones"""

    comedor_id_sisoc: int
    periodo: str  # YYYYMM
    cantidad_debitos: int
    credito_total: Decimal
    debito_total: Decimal
    cereo: Decimal

    def periodo_display(self) -> str:
        """Formatea el período YYYYMM como YYYY-MM"""
        periodo_str = str(self.periodo)
        if len(periodo_str) == 6:
            return f"{periodo_str[:4]}-{periodo_str[4:]}"
        return periodo_str

    def transferido_display(self) -> str:
        """Formatea debito_total como moneda"""
        if self.debito_total is None:
            return "Sin información"
        return f"${self.debito_total:,.0f}".replace(",", ".")

    def gastado_display(self) -> str:
        """Formatea credito_total como moneda"""
        if self.credito_total is None:
            return "Sin información"
        return f"${self.credito_total:,.0f}".replace(",", ".")

    def saldo_display(self) -> str:
        """Formatea cereo como moneda"""
        if self.cereo is None:
            return "Sin información"
        return f"${self.cereo:,.0f}".replace(",", ".")


class DWTransaccionesService:
    """Servicio para consultar la vista externa DW_sisoc.vw_EC_resumen_transacciones"""

    @staticmethod
    def obtener_resumen_ultimo_periodo(comedor_id: int) -> Optional[DWTransaccion]:
        """
        Obtiene el registro del último período disponible para un comedor.

        Args:
            comedor_id: ID del comedor (sisoc_local.comedores_comedor.id)

        Returns:
            DWTransaccion con los datos del último período, o None si no hay registros
        """
        try:
            with connection.cursor() as cursor:
                query = """
                    SELECT
                        comedor_id_sisoc,
                        periodo,
                        cantidad_debitos,
                        credito_total,
                        debito_total,
                        cereo
                    FROM DW_sisoc.vw_EC_resumen_transacciones
                    WHERE comedor_id_sisoc = %s
                    ORDER BY periodo DESC
                    LIMIT 1
                """
                cursor.execute(query, [comedor_id])
                row = cursor.fetchone()

                if not row:
                    return None

                return DWTransaccion(
                    comedor_id_sisoc=row[0],
                    periodo=str(row[1]),
                    cantidad_debitos=row[2],
                    credito_total=row[3],
                    debito_total=row[4],
                    cereo=row[5],
                )
        except Exception as e:
            logger.error(
                f"Error consultando resumen DW para comedor {comedor_id}: {str(e)}",
                exc_info=True,
            )
            return None

    @staticmethod
    def obtener_historico_completo(
        comedor_id: int, page: int = 1, per_page: int = 20
    ) -> tuple[List[DWTransaccion], int]:
        """
        Obtiene el historial completo de períodos para un comedor con paginación.

        Args:
            comedor_id: ID del comedor (sisoc_local.comedores_comedor.id)
            page: Número de página (1-indexed)
            per_page: Registros por página

        Returns:
            Tupla (lista de DWTransaccion, total de registros)
        """
        try:
            with connection.cursor() as cursor:
                # Primero obtener el total de registros
                count_query = """
                    SELECT COUNT(*)
                    FROM DW_sisoc.vw_EC_resumen_transacciones
                    WHERE comedor_id_sisoc = %s
                """
                cursor.execute(count_query, [comedor_id])
                total_count = cursor.fetchone()[0]

                # Luego obtener los datos paginados
                offset = (page - 1) * per_page
                query = """
                    SELECT
                        comedor_id_sisoc,
                        periodo,
                        cantidad_debitos,
                        credito_total,
                        debito_total,
                        cereo
                    FROM DW_sisoc.vw_EC_resumen_transacciones
                    WHERE comedor_id_sisoc = %s
                    ORDER BY periodo DESC
                    LIMIT %s OFFSET %s
                """
                cursor.execute(query, [comedor_id, per_page, offset])
                rows = cursor.fetchall()

                transacciones = [
                    DWTransaccion(
                        comedor_id_sisoc=row[0],
                        periodo=str(row[1]),
                        cantidad_debitos=row[2],
                        credito_total=row[3],
                        debito_total=row[4],
                        cereo=row[5],
                    )
                    for row in rows
                ]

                return transacciones, total_count
        except Exception as e:
            logger.error(
                f"Error consultando historial DW para comedor {comedor_id}: {str(e)}",
                exc_info=True,
            )
            return [], 0
