"""
Servicios para el procesamiento de Informes Cabal en el módulo Centro de Familia.

Funciones:
- previsualizar_informe: lee el archivo Excel de forma eficiente, valida filas y retorna registros válidos y errores.
- procesar_informe: inserta en bloque los movimientos válidos con batch y registra errores en el expediente.
"""
import logging
from typing import List, Tuple, Dict
import pandas as pd
from django.db import transaction

from centrodefamilia.models import Expediente, MovimientoCabal, Centro
from ciudadanos.models import Ciudadano

logger = logging.getLogger(__name__)

class CabalService:
    @staticmethod
    def previsualizar_informe(expediente: Expediente, archivo_excel) -> Tuple[List[Dict], List[Tuple[int, str]]]:
        """
        Lee el Excel de Informe Cabal usando solo las columnas necesarias y mapea en memoria
        todos los Centros y Ciudadanos para evitar consultas repetidas.
        Devuelve:
          - validos: lista de dicts con datos para crear MovimientoCabal
          - errores: lista de tuplas (fila_numero, mensaje_error)
        """
        # Leer solo columnas necesarias
        usecols = ["CUIT_CENTRO", "CUIT_PERSONA", "MONTO", "FECHA"]
        df = pd.read_excel(archivo_excel, usecols=usecols)

        # Limpiar datos y preparar sets únicos
        df["CUIT_CENTRO"] = df["CUIT_CENTRO"].astype(str).str.strip()
        df["CUIT_PERSONA"] = pd.to_numeric(df["CUIT_PERSONA"], errors='coerce')

        codigos = df["CUIT_CENTRO"].dropna().unique().tolist()
        documentos = df["CUIT_PERSONA"].dropna().astype(int).unique().tolist()

        # Fetch masivo desde DB
        centros_map = {c.codigo: c for c in Centro.objects.filter(codigo__in=codigos)}
        ciudadanos_map = {c.documento: c for c in Ciudadano.objects.filter(documento__in=documentos)}

        validos = []
        errores = []

        for idx, row in df.iterrows():
            fila = idx + 2
            codigo_centro = row["CUIT_CENTRO"]
            documento_persona = row["CUIT_PERSONA"]
            monto = row["MONTO"]
            fecha_raw = row["FECHA"]
            msg = None

            centro_obj = centros_map.get(codigo_centro)
            if not centro_obj:
                msg = f"Fila {fila}: Centro código '{codigo_centro}' inexistente"

            ciudadano_obj = None
            if not msg:
                if pd.isna(documento_persona):
                    msg = f"Fila {fila}: Documento persona inválido"
                else:
                    ciudadano_obj = ciudadanos_map.get(int(documento_persona))
                    if not ciudadano_obj:
                        msg = f"Fila {fila}: Ciudadano doc. '{int(documento_persona)}' no encontrado"

            if not msg and (monto is None or pd.isna(monto)):
                msg = f"Fila {fila}: Monto inválido"

            fecha = None
            if not msg:
                try:
                    fecha = pd.to_datetime(fecha_raw, dayfirst=True).date()
                except Exception:
                    msg = f"Fila {fila}: Fecha inválida '{fecha_raw}'"

            if msg:
                errores.append((fila, msg))
            else:
                validos.append({
                    'expediente': expediente,
                    'centro': centro_obj,
                    'ciudadano': ciudadano_obj,
                    'monto': monto,
                    'fecha': fecha,
                    'fila_origen': fila,
                })

        return validos, errores

    @staticmethod
    def procesar_informe(expediente: Expediente, validos: List[Dict], errores: List[Tuple[int, str]]) -> None:
        """
        Inserta en bloque los movimientos válidos usando batch_size y registra errores en el expediente.
        """
        # Guardar errores
        expediente.errores = '\n'.join([msg for _, msg in errores])

        try:
            with transaction.atomic():
                # Bulk create en batches para alta performance
                MovimientoCabal.objects.bulk_create(
                    [MovimientoCabal(**data) for data in validos],
                    batch_size=1000
                )
                expediente.procesado = True
                expediente.save(update_fields=['procesado', 'errores'])
        except Exception as e:
            logger.error(
                f"Error procesando Informe Cabal (Expediente {expediente.pk}): {e}", exc_info=True
            )
            raise
