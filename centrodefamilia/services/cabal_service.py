"""
Servicios para el procesamiento de Informes Cabal global en el módulo Centro de Familia.

Funciones:
- previsualizar_informe: lee el archivo (Excel o CSV) y valida filas.
- procesar_informe: inserta en bloque los movimientos válidos.
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
    def previsualizar_informe(expediente: Expediente, archivo) -> Tuple[List[Dict], List[Tuple[int, str]]]:

        filename = archivo.name.lower()
        expected = ["CUIT_CENTRO", "CUIT_PERSONA", "MONTO", "FECHA"]
        try:
            if filename.endswith('.csv'):
                raw_df = pd.read_csv(archivo)
            else:
                raw_df = pd.read_excel(archivo, engine='openpyxl')
        except Exception as e:
            raise ValueError(f"No se pudo leer el archivo: {e}")

        # Normalizar nombres de columna
        cols_map = {col.upper().strip(): col for col in raw_df.columns}
        missing = [exp for exp in expected if exp not in cols_map]
        if missing:
            raise ValueError(f"Columnas esperadas no encontradas: {missing}")
        # Renombrar para usar expected names
        df = raw_df.rename(columns={cols_map[exp]: exp for exp in expected})

        # Usar solo las columnas necesarias
        df = df[expected]

        # Preparar mapeos
        df["CUIT_CENTRO"] = df["CUIT_CENTRO"].astype(str).str.strip()
        df["CUIT_PERSONA"] = pd.to_numeric(df["CUIT_PERSONA"], errors='coerce')
        codigos = df["CUIT_CENTRO"].dropna().unique().tolist()
        documentos = df["CUIT_PERSONA"].dropna().astype(int).unique().tolist()
        centros_map = {c.codigo: c for c in Centro.objects.filter(codigo__in=codigos)}
        ciudadanos_map = {c.documento: c for c in Ciudadano.objects.filter(documento__in=documentos)}

        validos, errores = [], []
        for idx, row in df.iterrows():
            fila = idx + 2
            codigo = row["CUIT_CENTRO"]
            doc = row["CUIT_PERSONA"]
            monto = row["MONTO"]
            fecha_raw = row["FECHA"]
            msg = None
            centro_obj = centros_map.get(codigo)
            if not centro_obj:
                msg = f"Fila {fila}: Centro código '{codigo}' inexistente"
            ciudadano_obj = None
            if not msg:
                if pd.isna(doc):
                    msg = f"Fila {fila}: Documento inválido"
                else:
                    ciudadano_obj = ciudadanos_map.get(int(doc))
                    if not ciudadano_obj:
                        msg = f"Fila {fila}: Ciudadano doc. '{int(doc)}' no encontrado"
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
        Inserta en bloque los movimientos válidos y registra errores en el expediente.
        """
        expediente.errores = '\n'.join([msg for _, msg in errores])
        try:
            with transaction.atomic():
                MovimientoCabal.objects.bulk_create(
                    [MovimientoCabal(**data) for data in validos],
                    batch_size=1000
                )
                expediente.procesado = True
                expediente.save(update_fields=['procesado', 'errores'])
        except Exception as e:
            logger.error(f"Error procesando Informe Cabal (Expediente {expediente.pk}): {e}", exc_info=True)
            raise
