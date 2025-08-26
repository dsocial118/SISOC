import logging
from io import BytesIO
import re

import pandas as pd
from django.core.exceptions import ValidationError
from django.db import transaction
from functools import lru_cache

from celiaquia.models import EstadoLegajo, ExpedienteCiudadano

logger = logging.getLogger(__name__)


def _norm_col(col: str) -> str:
    s = str(col).strip().lower()
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^a-z0-9_]", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "columna"


@lru_cache(maxsize=1)
def _estado_doc_pendiente_id():
    try:
        return EstadoLegajo.objects.only("id").get(nombre="DOCUMENTO_PENDIENTE").id
    except EstadoLegajo.DoesNotExist:
        raise ValidationError("Falta el estado DOCUMENTO_PENDIENTE")


class ImportacionService:
    @staticmethod
    def preview_excel(archivo_excel, max_rows=5):
        try:
            archivo_excel.open()
        except Exception:
            pass
        archivo_excel.seek(0)
        raw = archivo_excel.read()
        name = (getattr(archivo_excel, "name", "") or "").lower()

        df = None
        try:
            if name.endswith((".xlsx", ".xls")):
                df = pd.read_excel(BytesIO(raw), engine="openpyxl")
        except Exception:
            df = None
        if df is None:
            try:
                df = pd.read_csv(BytesIO(raw), dtype=str, encoding="utf-8-sig")
            except Exception:
                df = pd.read_csv(BytesIO(raw), dtype=str, sep=";", encoding="utf-8-sig")

        df.columns = [_norm_col(c) for c in df.columns]
        df = df.fillna("")
        for c in df.columns:
            try:
                if hasattr(df[c], "dt"):
                    df[c] = df[c].apply(lambda x: x.date() if hasattr(x, "date") else x)
            except Exception:
                pass

        total_rows = int(len(df))

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
    def importar_legajos_desde_excel(
        expediente, archivo_excel, usuario, batch_size=500
    ):
        from celiaquia.services.ciudadano_service import CiudadanoService

        try:
            archivo_excel.open()
        except Exception:
            pass
        archivo_excel.seek(0)
        data = archivo_excel.read()

        try:
            df = pd.read_excel(BytesIO(data), engine="openpyxl", dtype=str)
        except Exception as e:
            raise ValidationError(f"No se pudo leer Excel: {e}")

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

        df = df[expected].fillna("")
        if "fecha_nacimiento" in df.columns:
            df["fecha_nacimiento"] = df["fecha_nacimiento"].apply(
                lambda x: x.date() if hasattr(x, "date") else x
            )

        estado_id = _estado_doc_pendiente_id()
        validos = errores = 0
        detalles_errores = []
        batch = []

        for offset, row in enumerate(df.to_dict(orient="records"), start=2):
            try:
                ciudadano = CiudadanoService.get_or_create_ciudadano(row, usuario)
                batch.append(
                    ExpedienteCiudadano(
                        expediente=expediente,
                        ciudadano=ciudadano,
                        estado_id=estado_id,
                    )
                )
                validos += 1
            except Exception as e:
                errores += 1
                detalles_errores.append({"fila": offset, "error": str(e)})
                logger.error("Error fila %s: %s", offset, e)

            if len(batch) >= batch_size:
                ExpedienteCiudadano.objects.bulk_create(batch, batch_size=batch_size)
                batch.clear()

        if batch:
            ExpedienteCiudadano.objects.bulk_create(batch, batch_size=batch_size)

        logger.info("Import completo: %s válidos, %s errores", validos, errores)

        return {
            "validos": validos,
            "errores": errores,
            "detalles_errores": detalles_errores,
        }
