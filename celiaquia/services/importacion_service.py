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


@lru_cache(maxsize=1)
def _tipo_doc_cuit():
    try:
        return TipoDocumento.objects.only("id").get(tipo__iexact="CUIT").id
    except TipoDocumento.DoesNotExist as exc:
        raise ValidationError("Falta configurar el TipoDocumento CUIT") from exc


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
    def generar_plantilla_excel() -> bytes:
        """Genera y devuelve un archivo de Excel vacío para importar expedientes.

        Returns
        -------
        bytes
            Contenido binario del archivo XLSX con las columnas necesarias
            para la importación de legajos en un expediente.
        """

        columnas = [
            "apellido",
            "nombre",
            "documento",
            "fecha_nacimiento",
            "sexo",
            "nacionalidad",
            "municipio",
            "localidad",
            "calle",
            "altura",
            "codigo_postal",
            "telefono",
            "email",
        ]
        df = pd.DataFrame(columns=columnas)
        output = BytesIO()
        df.to_excel(output, index=False, engine="openpyxl")
        return output.getvalue()

    @staticmethod
    def preview_excel(archivo_excel, max_rows=None):
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
                return None
            txt = str(v).strip().lower()
            if txt in ("all", "none", "0", "todos"):
                return None
            try:
                n = int(txt)
                return n if n > 0 else None
            except Exception:
                return None

        limit = _parse_max_rows(max_rows)
        sample_df = df if limit is None else df.head(limit)
        sample = sample_df.to_dict(orient="records")
        
        # Agregar columna ID al inicio
        headers = ["ID"] + list(df.columns)
        rows_with_id = []
        for i, row in enumerate(sample, start=1):
            row_with_id = {"ID": i}
            row_with_id.update(row)
            rows_with_id.append(row_with_id)
        
        return {
            "headers": headers,
            "rows": rows_with_id,
            "total_rows": total_rows,
            "shown_rows": len(sample),
        }

    @staticmethod
    @transaction.atomic
    def importar_legajos_desde_excel(
        expediente, archivo_excel, usuario, batch_size=1000
    ):
        """Importa legajos desde un archivo Excel al expediente indicado.
        
        Versión optimizada que reduce consultas a la base de datos mediante:
        - Precarga de todos los datos necesarios
        - Bulk operations para ciudadanos y legajos
        - Cache de FKs y validaciones
        - Procesamiento por lotes más eficiente
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
            "sexo": "sexo",
            "nacionalidad": "nacionalidad",
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
        tipo_doc_cuit_id = _tipo_doc_cuit()
        
        # Obtener provincia del usuario una sola vez
        provincia_usuario_id = None
        try:
            if hasattr(usuario, "profile") and usuario.profile.provincia_id:
                provincia_usuario_id = usuario.profile.provincia_id
        except Exception:
            pass

        validos = errores = 0
        detalles_errores = []
        excluidos = []
        warnings = []
        
        # Precarga de datos para optimizar consultas
        existentes_ids = set(
            ExpedienteCiudadano.objects.filter(expediente=expediente).values_list(
                "ciudadano_id", flat=True
            )
        )

        # Precarga de conflictos en una sola consulta
        conflictos_qs = (
            ExpedienteCiudadano.objects.select_related(
                "expediente", "expediente__estado"
            )
            .exclude(expediente=expediente)
            .filter(
                Q(estado_cupo=EstadoCupo.DENTRO)
                | Q(expediente__estado__nombre__in=ESTADOS_PRE_CUPO)
            )
            .values(
                "ciudadano_id", "estado_cupo", "es_titular_activo", 
                "expediente_id", "expediente__estado__nombre"
            )
        )

        en_programa = {}
        abiertos = {}
        for ec in conflictos_qs:
            cid = ec["ciudadano_id"]
            if ec["estado_cupo"] == EstadoCupo.DENTRO:
                en_programa[cid] = ec
            else:
                abiertos[cid] = ec

        # Precarga de todos los FKs necesarios
        fk_cache = {
            "tipo_documento": {td.tipo.lower(): td.id for td in TipoDocumento.objects.all()},
            "sexo": {s.sexo.lower(): s.id for s in Sexo.objects.all()},
            "nacionalidad": {n.nacionalidad.lower(): n.id for n in Nacionalidad.objects.all()},
            "provincia": {p.nombre.lower(): p.id for p in Provincia.objects.all()},
            "municipio": {m.nombre.lower(): m.id for m in Municipio.objects.select_related('provincia').all()},
            "localidad": {l.nombre.lower(): l.id for l in Localidad.objects.select_related('municipio').all()},
        }
        
        # Precarga de ciudadanos existentes por documento
        documentos_excel = [str(row.get('documento', '')).strip() for _, row in df.iterrows() if row.get('documento')]
        ciudadanos_existentes = {}
        if documentos_excel:
            for c in Ciudadano.objects.filter(
                tipo_documento_id=tipo_doc_cuit_id,
                documento__in=documentos_excel
            ).select_related('tipo_documento', 'sexo', 'nacionalidad', 'provincia', 'municipio', 'localidad'):
                ciudadanos_existentes[c.documento] = c

        numeric_fields = {
            "documento", "altura", "telefono", "telefono_alternativo", "codigo_postal"
        }

        def add_warning(fila, campo, detalle):
            warnings.append({"fila": fila, "campo": campo, "detalle": detalle})
            logger.warning("Fila %s: %s (%s)", fila, detalle, campo)

        def resolve_fk_cached(field, value):
            if not value:
                return None
            key = str(value).strip().lower()
            return fk_cache.get(field, {}).get(key)

        # Procesar cada fila y usar get_or_create_ciudadano directamente
        legajos_crear = []

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

                # Asignar tipo de documento CUIT resolviendo el ID en runtime
                payload["tipo_documento"] = _tipo_doc_cuit()

                # Asignar provincia del usuario automáticamente
                try:
                    if hasattr(usuario, "profile") and usuario.profile.provincia_id:
                        payload["provincia"] = usuario.profile.provincia_id
                except Exception:
                    pass

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

                # Manejar municipio y localidad por ID si son numéricos
                for fk in ["municipio", "localidad"]:
                    val = payload.get(fk)
                    if val:
                        val_str = str(val).strip()
                        resolved = None
                        
                        # Intentar por ID si es numérico
                        if val_str.isdigit():
                            try:
                                if fk == "municipio":
                                    resolved = Municipio.objects.get(pk=int(val_str)).id
                                elif fk == "localidad":
                                    resolved = Localidad.objects.get(pk=int(val_str)).id
                            except (Municipio.DoesNotExist, Localidad.DoesNotExist):
                                pass
                        
                        # Fallback: buscar por nombre
                        if resolved is None:
                            resolved = resolve_fk_cached(fk, val)
                        
                        if resolved is None:
                            add_warning(offset, fk, f"{val} no encontrado")
                            payload[fk] = None
                        else:
                            payload[fk] = resolved
                
                # Manejar otros FKs normalmente
                for fk in ["sexo", "nacionalidad"]:
                    val = payload.get(fk)
                    if val:
                        resolved = resolve_fk_cached(fk, val)
                        if resolved is None:
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

                # Usar get_or_create_ciudadano que maneja correctamente la creación
                try:
                    ciudadano = CiudadanoService.get_or_create_ciudadano(
                        datos=payload,
                        usuario=usuario,
                        expediente=expediente,
                        programa_id=3,
                    )
                    
                    if not ciudadano:
                        logger.error("get_or_create_ciudadano retornó None en fila %s", offset)
                        continue
                        
                    if not hasattr(ciudadano, 'pk') or not ciudadano.pk:
                        logger.error("Ciudadano sin PK en fila %s: %s", offset, ciudadano)
                        continue
                        
                except Exception as e:
                    logger.error("Error creando ciudadano en fila %s: %s", offset, e)
                    errores += 1
                    detalles_errores.append({"fila": offset, "error": f"Error creando ciudadano: {str(e)}"})
                    continue

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
                    estado_text = "ACEPTADO" if prog["es_titular_activo"] else "SUSPENDIDO"
                    excluidos.append(
                        {
                            "fila": offset,
                            "ciudadano_id": cid,
                            "documento": getattr(ciudadano, "documento", ""),
                            "nombre": getattr(ciudadano, "nombre", ""),
                            "apellido": getattr(ciudadano, "apellido", ""),
                            "expediente_origen_id": prog["expediente_id"],
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
                            "expediente_origen_id": conflict["expediente_id"],
                            "estado_expediente_origen": conflict["expediente__estado__nombre"],
                            "motivo": "Duplicado en otro expediente abierto",
                        }
                    )
                    logger.warning(
                        "Fila %s excluida: duplicado en otro expediente abierto (ciudadano_id=%s)",
                        offset,
                        cid,
                    )
                    continue

                # 4) OK para crear legajo
                legajos_crear.append(ExpedienteCiudadano(
                    expediente=expediente,
                    ciudadano=ciudadano,
                    estado_id=estado_id,
                ))
                existentes_ids.add(cid)
                validos += 1

            except Exception as e:
                errores += 1
                detalles_errores.append({"fila": offset, "error": str(e)})
                logger.error("Error fila %s: %s", offset, e)

        # Bulk create de legajos
        if legajos_crear:
            try:
                logger.info("Creando %s legajos en bulk_create", len(legajos_crear))
                ExpedienteCiudadano.objects.bulk_create(legajos_crear, batch_size=batch_size)
                logger.info("Legajos creados exitosamente")
            except Exception as e:
                logger.error("Error en bulk_create de legajos: %s", e)
        else:
            logger.warning("No hay legajos para crear - lista vacía")

        logger.info(
            "Import optimizado completo: %s válidos, %s errores, %s excluidos.",
            validos, errores, len(excluidos)
        )

        return {
            "validos": validos,
            "errores": errores,
            "detalles_errores": detalles_errores,
            "excluidos_count": len(excluidos),
            "excluidos": excluidos,
            "warnings": warnings,
        }
