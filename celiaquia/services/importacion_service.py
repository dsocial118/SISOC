# services/importacion_service.py
import logging
from io import BytesIO
import re
from django.db.models import Q
import pandas as pd
from django.core.exceptions import ValidationError
from django.db import transaction

from celiaquia.models import EstadoLegajo, ExpedienteCiudadano

logger = logging.getLogger(__name__)


class ImportacionService:
    @staticmethod
    def preview_excel(archivo_excel, max_rows=5):
        """
        Lee el archivo subido (XLSX/XLS/CSV) y devuelve:
        - headers: lista de columnas normalizadas (snake_case)
        - rows: primeras N filas (N = max_rows) o todas si max_rows es None/"all"/"none"/0
        - total_rows: cantidad total de filas en el archivo
        - shown_rows: cuántas filas se están mostrando en 'rows'
        """
        # Asegurar lectura desde el inicio
        try:
            archivo_excel.open()
        except Exception:
            pass
        archivo_excel.seek(0)
        raw = archivo_excel.read()

        # Heurística por extensión
        name = (getattr(archivo_excel, "name", "") or "").lower()

        df = None
        # 1) Intento como Excel (prioritario para .xlsx/.xls, pero tolerante si no hay extensión)
        try:
            if name.endswith((".xlsx", ".xls")) or True:
                df = pd.read_excel(BytesIO(raw), engine="openpyxl")
        except Exception:
            df = None

        # 2) Fallback como CSV (coma y luego punto y coma)
        if df is None:
            try:
                df = pd.read_csv(BytesIO(raw), dtype=str, encoding="utf-8-sig")
            except Exception:
                try:
                    df = pd.read_csv(BytesIO(raw), dtype=str, sep=";", encoding="utf-8-sig")
                except Exception as e:
                    raise ValidationError(f"Error al leer el archivo (XLSX/XLS/CSV): {e}")

        # Normalizar encabezados -> snake_case simple
        def _norm_col(col: str) -> str:
            s = str(col).strip().lower()
            s = re.sub(r"\s+", "_", s)            # espacios -> _
            s = re.sub(r"[^a-z0-9_]", "_", s)     # otros símbolos -> _
            s = re.sub(r"_+", "_", s).strip("_")  # colapsar múltiples _
            return s or "columna"

        df.columns = [_norm_col(c) for c in df.columns]

        # Reemplazar NaN por vacío para la vista previa
        df = df.fillna("")

        # Convertir columnas de tipo datetime a date (y mantener compatibilidad con 'fecha_nacimiento')
        # Si vienen como strings, se las deja como están; si pandas detectó datetime, se pasa a date
        for c in df.columns:
            # Intento seguro: si la serie tiene dt accessor (datetime64), convierto a date
            try:
                if hasattr(df[c], "dt"):
                    # Esto no rompe si la columna no es datetime (raise AttributeError)
                    df[c] = df[c].apply(lambda x: x.date() if hasattr(x, "date") else x)
            except Exception:
                # Si falla el .dt por ser string/mixto, lo dejamos como está
                pass

        total_rows = int(len(df))

        # Determinar límite
        def _parse_max_rows(v):
            if v is None:
                return 5
            txt = str(v).strip().lower()
            if txt in ("all", "none", "0", "todos"):
                return None
            try:
                n = int(txt)
                return n if n > 0 else None
            except Exception:
                return 5

        limit = _parse_max_rows(max_rows)
        sample_df = df if limit is None else df.head(limit)

        sample = sample_df.to_dict(orient="records")
        return {
            "headers": list(df.columns),
            "rows": sample,
            "total_rows": total_rows,
            "shown_rows": len(sample),
        }

    @staticmethod
    @transaction.atomic
    def importar_legajos_desde_excel(expediente, archivo_excel, usuario, batch_size=500):
        """
        Importa legajos desde el Excel subido:
        - Normaliza encabezados y campos.
        - Crea Ciudadano (vía CiudadanoService) y ExpedienteCiudadano en batches.
        - Valida encabezados esperados (misma lógica que tu versión estable).
        - Requiere que luego cada legajo tenga su archivo (validación existente).
        """
        # Import local para evitar circularidad
        from celiaquia.services.ciudadano_service import CiudadanoService

        # Asegurar lectura desde el inicio
        try:
            archivo_excel.open()
        except Exception:
            pass
        archivo_excel.seek(0)
        data = archivo_excel.read()

        try:
            df = pd.read_excel(BytesIO(data), engine="openpyxl")
        except Exception as e:
            raise ValidationError(f"No se pudo leer Excel: {e}")

        # Normalizar encabezados
        df.columns = [str(col).strip().lower().replace(" ", "_") for col in df.columns]
        expected = [
            "nombre",
            "apellido",
            "documento",
            "fecha_nacimiento",
            "tipo_documento",
            "sexo",
        ]
        if set(df.columns) != set(expected):
            raise ValidationError(
                f"Encabezados inválidos: {list(df.columns)} — esperados: {expected}"
            )

        # Reordenar y limpiar
        df = df[expected]
        df = df.fillna("")
        if "fecha_nacimiento" in df.columns:
            df["fecha_nacimiento"] = df["fecha_nacimiento"].apply(
                lambda x: x.date() if hasattr(x, "date") else x
            )

        estado_inicial = EstadoLegajo.objects.get(nombre="DOCUMENTO_PENDIENTE")
        validos = errores = 0
        detalles_errores = []
        batch = []

        # Empezamos en 2 para reflejar fila real de Excel (1 = encabezados)
        for offset, row in enumerate(df.to_dict(orient="records"), start=2):
            logger.debug(f"Fila {offset}: {row}")
            try:
                ciudadano = CiudadanoService.get_or_create_ciudadano(row, usuario)
                batch.append(
                    ExpedienteCiudadano(
                        expediente=expediente,
                        ciudadano=ciudadano,
                        estado=estado_inicial,
                    )
                )
                validos += 1
            except Exception as e:
                errores += 1
                detalles_errores.append({"fila": offset, "error": str(e)})
                logger.error(f"Error fila {offset}: {e}")

            if len(batch) >= batch_size:
                ExpedienteCiudadano.objects.bulk_create(batch)
                batch.clear()

        if batch:
            ExpedienteCiudadano.objects.bulk_create(batch)

        logger.info(f"Import completo: {validos} válidos, {errores} errores")

        # Validación: todos los legajos con archivo antes de continuar
        faltantes = (
            ExpedienteCiudadano.objects
            .filter(expediente=expediente)
            .filter(
                Q(archivo1__isnull=True) |
                Q(archivo2__isnull=True) |
                Q(archivo3__isnull=True)
            )
        )

        if faltantes:
            raise ValidationError(
                "Debe subir un archivo para cada legajo antes de continuar."
            )

        return {
            "validos": validos,
            "errores": errores,
            "detalles_errores": detalles_errores,
        }
