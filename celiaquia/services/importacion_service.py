import logging
from io import BytesIO
import re

import pandas as pd
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from functools import lru_cache

from celiaquia.models import EstadoCupo, EstadoLegajo, ExpedienteCiudadano

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


# Estados de expediente considerados “abiertos / pre-cupo” para evitar duplicados inter-expedientes
ESTADOS_PRE_CUPO = [
    "CREADO",
    "PROCESADO",
    "EN_ESPERA",
    "CONFIRMACION_DE_ENVIO",
    "RECEPCIONADO",
    "ASIGNADO",
    "PROCESO_DE_CRUCE",
]


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
        """Importa legajos desde un archivo Excel al expediente indicado.

        Antes de iterar filas, precalcula conjuntos de ciudadanos existentes en
        el expediente y aquellos que ya están en el programa (cupo DENTRO) o en
        expedientes abiertos para evitar consultas repetidas dentro del bucle.
        """

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
        excluidos = (
            []
        )  # lista con todos los excluidos (mismo expediente, en cupo en otro, u otro expediente abierto)
        batch = []

        existentes_ids = set(
            ExpedienteCiudadano.objects.filter(expediente=expediente).values_list(
                "ciudadano_id", flat=True
            )
        )

        conflictos_qs = (
            ExpedienteCiudadano.objects.select_related(
                "expediente", "expediente__estado"
            )
            .exclude(expediente=expediente)
            .filter(
                Q(estado_cupo=EstadoCupo.DENTRO)
                | Q(expediente__estado__nombre__in=ESTADOS_PRE_CUPO)
            )
            .order_by("ciudadano_id", "-creado_en")
        )

        en_programa = {}
        abiertos = {}
        for ec in conflictos_qs:
            if ec.estado_cupo == EstadoCupo.DENTRO:
                en_programa.setdefault(ec.ciudadano_id, ec)
            else:
                abiertos.setdefault(ec.ciudadano_id, ec)

        for offset, row in enumerate(df.to_dict(orient="records"), start=2):
            try:
                # Crear/obtener ciudadano (puede asignar programa si corresponde)
                ciudadano = CiudadanoService.get_or_create_ciudadano(
                    row, usuario=usuario, expediente=expediente
                )

                cid = ciudadano.pk

                # 1) Ya existe en ESTE expediente -> excluir
                if cid in existentes_ids:
                    excluidos.append(
                        {
                            "fila": offset,
                            "ciudadano_id": cid,
                            "documento": getattr(ciudadano, "documento", ""),
                            "nombre": getattr(ciudadano, "nombre", ""),
                            "apellido": getattr(ciudadano, "apellido", ""),
                            "motivo": "Ya existe en este expediente",
                        }
                    )
                    logger.warning(
                        "Fila %s excluida: ya existe en este expediente (ciudadano_id=%s)",
                        offset,
                        cid,
                    )
                    continue

                # 2) Ya está dentro del programa (cupo DENTRO) en OTRO expediente -> excluir
                if cid in en_programa:
                    prog = en_programa[cid]
                    estado_text = "ACEPTADO" if prog.es_titular_activo else "SUSPENDIDO"
                    excluidos.append(
                        {
                            "fila": offset,
                            "ciudadano_id": cid,
                            "documento": getattr(ciudadano, "documento", ""),
                            "nombre": getattr(ciudadano, "nombre", ""),
                            "apellido": getattr(ciudadano, "apellido", ""),
                            "expediente_origen_id": prog.expediente_id,
                            "estado_programa": estado_text,
                            "motivo": "Ya está dentro del programa en otro expediente",
                        }
                    )
                    logger.warning(
                        "Fila %s excluida: ya está dentro del programa en otro expediente (ciudadano_id=%s)",
                        offset,
                        cid,
                    )
                    continue

                # 3) Ya figura en OTRO expediente “abierto / pre-cupo” -> excluir
                if cid in abiertos:
                    conflict = abiertos[cid]
                    excluidos.append(
                        {
                            "fila": offset,
                            "ciudadano_id": cid,
                            "documento": getattr(ciudadano, "documento", ""),
                            "nombre": getattr(ciudadano, "nombre", ""),
                            "apellido": getattr(ciudadano, "apellido", ""),
                            "expediente_origen_id": conflict.expediente_id,
                            "estado_expediente_origen": (
                                getattr(
                                    getattr(conflict, "expediente", None),
                                    "estado",
                                    None,
                                ).nombre
                                if getattr(
                                    getattr(conflict, "expediente", None),
                                    "estado",
                                    None,
                                )
                                else ""
                            ),
                            "motivo": "Duplicado en otro expediente abierto",
                        }
                    )
                    logger.warning(
                        "Fila %s excluida: duplicado en otro expediente abierto (ciudadano_id=%s)",
                        offset,
                        cid,
                    )
                    continue

                # 4) OK para crear en este expediente
                batch.append(
                    ExpedienteCiudadano(
                        expediente=expediente,
                        ciudadano=ciudadano,
                        estado_id=estado_id,
                    )
                )
                existentes_ids.add(cid)
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

        logger.info(
            "Import completo: %s válidos, %s errores, %s advertencias (excluidos: duplicados o ya en programa).",
            validos,
            errores,
            len(excluidos),
        )

        return {
            "validos": validos,
            "errores": errores,
            "detalles_errores": detalles_errores,
            "excluidos_count": len(excluidos),
            "excluidos": excluidos,
        }
