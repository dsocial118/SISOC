import logging
from functools import lru_cache
from io import BytesIO
import re

import pandas as pd
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.db import transaction
from django.db.models import Q

from ciudadanos.models import Ciudadano, TipoDocumento, Sexo, Nacionalidad
from core.models import Provincia, Municipio, Localidad
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


@lru_cache(maxsize=1)
def _tipo_doc_por_defecto():
    try:
        return TipoDocumento.objects.only("id").get(tipo__iexact="DNI").id
    except TipoDocumento.DoesNotExist:
        raise ValidationError("Falta el TipoDocumento por defecto (DNI)")


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

        from celiaquia.services.ciudadano_service import (
            CiudadanoService,
            _tipo_doc_por_defecto,
        )

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

        df.columns = [_norm_col(col) for col in df.columns]

        column_map = {
            "apellido": "apellido",
            "apellidos": "apellido",
            "nombre": "nombre",
            "nombres": "nombre",
            "documento": "documento",
            "numerodoc": "documento",
            "numero_documento": "documento",
            "dni": "documento",
            "fecha_nacimiento": "fecha_nacimiento",
            "fecha_de_nacimiento": "fecha_nacimiento",
            "tipo_documento": "tipo_documento",
            "tipo_doc": "tipo_documento",
            "sexo": "sexo",
            "nacionalidad": "nacionalidad",
            "provincia": "provincia",
            "municipio": "municipio",
            "localidad": "localidad",
            "email": "email",
            "telefono": "telefono",
            "codigo_postal": "codigo_postal",
            "calle": "calle",
            "altura": "altura",
        }

        present = [c for c in df.columns if c in column_map]
        df = df[present].rename(columns={c: column_map[c] for c in present}).fillna("")
        if "fecha_nacimiento" in df.columns:
            df["fecha_nacimiento"] = df["fecha_nacimiento"].apply(
                lambda x: x.date() if hasattr(x, "date") else x
            )

        _tipo_doc_por_defecto()

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

        warnings = []

        fk_models = {
            "tipo_documento": (TipoDocumento, "tipo"),
            "sexo": (Sexo, "sexo"),
            "nacionalidad": (Nacionalidad, "nacionalidad"),
            "provincia": (Provincia, "nombre"),
            "municipio": (Municipio, "nombre"),
            "localidad": (Localidad, "nombre"),
        }

        numeric_fields = {
            "documento",
            "altura",
            "telefono",
            "telefono_alternativo",
            "codigo_postal",
        }

        def add_warning(fila, campo, detalle):
            warnings.append({"fila": fila, "campo": campo, "detalle": detalle})
            logger.warning("Fila %s: %s (%s)", fila, detalle, campo)

        def resolve_fk(field, value):
            model, lookup = fk_models[field]
            if str(value).isdigit():
                try:
                    return model.objects.only("id").get(pk=int(value)).id
                except model.DoesNotExist:
                    return None
            try:
                return (
                    model.objects.only("id")
                    .get(**{f"{lookup}__iexact": str(value).strip()})
                    .id
                )
            except model.DoesNotExist:
                return None

        for offset, row in enumerate(df.to_dict(orient="records"), start=2):
            try:
                payload = {}
                for field, value in row.items():
                    v = str(value).strip()
                    if field in numeric_fields:
                        cleaned = re.sub(r"\D", "", v)
                        if cleaned:
                            payload[field] = cleaned
                        else:
                            payload[field] = None
                            if v:
                                add_warning(offset, field, "valor numérico vacío")
                    else:
                        payload[field] = v or None

                if not payload.get("tipo_documento"):
                    payload["tipo_documento"] = _tipo_doc_por_defecto()

                required = ["apellido", "nombre", "documento", "fecha_nacimiento"]
                for req in required:
                    if not payload.get(req):
                        raise ValidationError(f"Campo obligatorio faltante: {req}")

                doc = payload.get("documento")
                if not str(doc).isdigit():
                    raise ValidationError("Documento debe contener sólo dígitos")
                try:
                    Ciudadano._meta.get_field("documento").run_validators(int(doc))
                except ValidationError as e:
                    raise ValidationError(f"Documento inválido: {e.messages[0]}")

                try:
                    payload["fecha_nacimiento"] = CiudadanoService._to_date(
                        payload.get("fecha_nacimiento")
                    )
                except ValidationError as e:
                    raise ValidationError(str(e))

                for fk in fk_models:
                    val = payload.get(fk)
                    if val in (None, ""):
                        if fk != "tipo_documento":
                            payload[fk] = None
                        continue
                    resolved = resolve_fk(fk, val)
                    if resolved is None:
                        if fk == "tipo_documento":
                            raise ValidationError(f"Tipo de documento inválido: {val}")
                        add_warning(offset, fk, f"{val} no encontrado")
                        payload[fk] = None
                    else:
                        payload[fk] = resolved

                email = payload.get("email")
                if email:
                    try:
                        EmailValidator()(email)
                    except ValidationError:
                        add_warning(offset, "email", f"Email inválido: {email}")
                        payload.pop("email", None)

                ciudadano = CiudadanoService.get_or_create_ciudadano(
                    datos=payload,
                    usuario=usuario,
                    expediente=expediente,
                    programa_id=3,
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
            "warnings": warnings,
        }
