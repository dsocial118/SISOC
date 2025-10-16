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

logger = logging.getLogger("django")


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


# Estados de expediente considerados "abiertos / pre-cupo" para evitar duplicados inter-expedientes
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
        """Genera y devuelve un archivo de Excel vacío para importar expedientes."""
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
            "APELLIDO_RESPONSABLE",
            "NOMBRE_REPSONSABLE",
            "Cuit_Responsable",
            "FECHA_DE_NACIMIENTO_RESPONSABLE",
            "SEXO",
            "DOMICILIO_RESPONSABLE",
            "LOCALIDAD_RESPONSABLE",
            "CELULAR_RESPONSABLE",
            "CORREO_RESPONSABLE",
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

        # Normalizar nombres de columnas y manejar duplicados
        normalized_cols = [_norm_col(c) for c in df.columns]

        # Resolver duplicados agregando sufijo numérico
        seen = {}
        unique_cols = []
        for col in normalized_cols:
            if col in seen:
                seen[col] += 1
                unique_cols.append(f"{col}_{seen[col]}")
            else:
                seen[col] = 0
                unique_cols.append(col)

        df.columns = unique_cols
        df = df.fillna("")
        for c in df.columns:
            try:
                if hasattr(df[c], "dt"):
                    df[c] = df[c].apply(
                        lambda x: (
                            x.date()
                            if hasattr(x, "date") and pd.notna(x)
                            else ("" if pd.isna(x) else x)
                        )
                    )
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
        # Verificar columnas únicas antes de convertir
        if len(set(sample_df.columns)) != len(sample_df.columns):
            logger.warning("Columnas duplicadas detectadas en preview")

        sample = sample_df.to_dict(orient="records")

        # Agregar columna ID al inicio y convertir IDs a nombres
        headers = ["ID"] + list(df.columns)
        rows_with_id = []
        for i, row in enumerate(sample, start=1):
            row_with_id = {"ID": i}

            # Convertir IDs a nombres para preview
            if "municipio" in row and row["municipio"]:
                municipio_str = str(row["municipio"]).strip()
                if (
                    municipio_str
                    and municipio_str != "nan"
                    and municipio_str.replace(".0", "").isdigit()
                ):
                    try:
                        municipio_id = int(float(municipio_str))
                        municipio = Municipio.objects.get(pk=municipio_id)
                        row["municipio"] = municipio.nombre
                    except:
                        pass

            if "localidad" in row and row["localidad"]:
                localidad_str = str(row["localidad"]).strip()
                if (
                    localidad_str
                    and localidad_str != "nan"
                    and localidad_str.replace(".0", "").isdigit()
                ):
                    try:
                        localidad_id = int(float(localidad_str))
                        localidad = Localidad.objects.get(pk=localidad_id)
                        row["localidad"] = localidad.nombre
                    except:
                        pass

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
        """Importa legajos desde un archivo Excel al expediente indicado."""

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
            # Campos del responsable
            "apellido_responsable": "apellido_responsable",
            "nombre_responsable": "nombre_responsable",
            "nombre_repsonsable": "nombre_responsable",  # typo en el requerimiento
            "fecha_de_nacimiento_responsable": "fecha_nacimiento_responsable",
            "fecha_nacimiento_responsable": "fecha_nacimiento_responsable",
            "sexo_responsable": "sexo_responsable",
            "domicilio_responsable": "domicilio_responsable",
            "localidad_responsable": "localidad_responsable",
            "contacto_responsable": "contacto_responsable",
            "telefono_celular_responsable": "telefono_responsable",
            "telefono_responsable": "telefono_responsable",
            "correo_electronico_responsable": "email_responsable",
            "email_responsable": "email_responsable",
            "cuit_responsable": "documento_responsable",
            "documento_responsable": "documento_responsable",
            # Variantes en mayusculas del excel
            "APELLIDO_RESPONSABLE": "apellido_responsable",
            "NOMBRE_RESPONSABLE": "nombre_responsable",
            "NOMBRE_REPSONSABLE": "nombre_responsable",
            "FECHA_DE_NACIMIENTO_RESPONSABLE": "fecha_nacimiento_responsable",
            "SEXO_RESPONSABLE": "sexo_responsable",
            "SEXO": "sexo_responsable",  # columnas en mayusculas para responsable
            "DOMICILIO_RESPONSABLE": "domicilio_responsable",
            "LOCALIDAD_RESPONSABLE": "localidad_responsable",
            "CELULAR_RESPONSABLE": "telefono_responsable",
            "TELEFONO_RESPONSABLE": "telefono_responsable",
            "CUIT_RESPONSABLE": "documento_responsable",
            "Cuit_Responsable": "documento_responsable",
            "CORREO_RESPONSABLE": "email_responsable",
            "EMAIL_RESPONSABLE": "email_responsable",
        }

        present = [c for c in df.columns if c in column_map]
        df = df[present].rename(columns={c: column_map[c] for c in present}).fillna("")
        # Eliminar posibles columnas duplicadas despues del renombrado
        df = df.loc[:, ~df.columns.duplicated()]
        if "fecha_nacimiento" in df.columns:
            df["fecha_nacimiento"] = df["fecha_nacimiento"].apply(
                lambda x: x.date() if hasattr(x, "date") else x
            )

        _tipo_doc_por_defecto()
        estado_id = _estado_doc_pendiente_id()
        tipo_doc_cuit_id = _tipo_doc_cuit()

        # Obtener provincia del usuario
        provincia_usuario_id = None
        try:
            if (
                hasattr(usuario, "profile")
                and usuario.profile
                and usuario.profile.provincia_id
            ):
                provincia_usuario_id = usuario.profile.provincia_id
        except Exception as e:
            logger.warning("No se pudo obtener provincia del usuario: %s", e)

        if not provincia_usuario_id:
            raise ValidationError(
                "El usuario debe tener una provincia configurada para importar legajos"
            )

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

        # Precarga de conflictos
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
                "ciudadano_id",
                "estado_cupo",
                "es_titular_activo",
                "expediente_id",
                "expediente__estado__nombre",
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

        numeric_fields = {
            "documento",
            "altura",
            "telefono",
            "telefono_alternativo",
            "codigo_postal",
            "documento_responsable",
            "telefono_responsable",
            "contacto_responsable",
        }

        def add_warning(fila, campo, detalle):
            warnings.append({"fila": fila, "campo": campo, "detalle": detalle})
            logger.warning("Fila %s: %s (%s)", fila, detalle, campo)

        # Precarga de datos para optimizar consultas
        municipios_cache = {}
        localidades_cache = {}
        sexos_cache = {}
        nacionalidades_cache = {}

        # Obtener todos los IDs únicos del Excel
        municipio_ids = set()
        localidad_ids = set()
        sexos_nombres = set()
        nacionalidades_nombres = set()

        for _, row in df.iterrows():
            if row.get("municipio"):
                mun_str = str(row["municipio"]).strip()
                if mun_str and mun_str != "nan" and mun_str.replace(".0", "").isdigit():
                    municipio_ids.add(int(float(mun_str)))
            if row.get("localidad"):
                loc_str = str(row["localidad"]).strip()
                if loc_str and loc_str != "nan" and loc_str.replace(".0", "").isdigit():
                    localidad_ids.add(int(float(loc_str)))
            if row.get("sexo"):
                sexos_nombres.add(str(row["sexo"]).strip().lower())
            if row.get("nacionalidad"):
                nacionalidades_nombres.add(str(row["nacionalidad"]).strip().lower())

        # Cargar todos los datos de una vez
        if municipio_ids:
            for m in Municipio.objects.filter(
                pk__in=municipio_ids, provincia_id=provincia_usuario_id
            ):
                municipios_cache[m.pk] = m.pk

        if localidad_ids:
            for l in Localidad.objects.filter(pk__in=localidad_ids):
                localidades_cache[l.pk] = l.pk

        if sexos_nombres:
            try:
                for s in Sexo.objects.all():
                    if s.sexo.lower() in sexos_nombres:
                        sexos_cache[s.sexo.lower()] = s.id
            except Exception as e:
                logger.warning("Error cargando sexos: %s", e)

        if nacionalidades_nombres:
            try:
                for n in Nacionalidad.objects.all():
                    if n.nacionalidad.lower() in nacionalidades_nombres:
                        nacionalidades_cache[n.nacionalidad.lower()] = n.id
            except Exception as e:
                logger.warning("Error cargando nacionalidades: %s", e)

        # Procesar cada fila
        legajos_crear = []
        relaciones_familiares = []  # Para almacenar las relaciones padre-hijo
        relaciones_familiares_pairs = set()

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
                                add_warning(offset, field, "valor numerico vacio")
                    else:
                        if v.lower() in {"nan", "nat", "none"}:
                            payload[field] = None
                        else:
                            payload[field] = v or None

                # Asignar tipo de documento CUIT
                payload["tipo_documento"] = tipo_doc_cuit_id

                # Asignar provincia del usuario
                payload["provincia"] = provincia_usuario_id

                required = ["apellido", "nombre", "documento", "fecha_nacimiento"]
                for req in required:
                    if not payload.get(req):
                        raise ValidationError(f"Campo obligatorio faltante: {req}")

                doc = payload.get("documento")
                if not str(doc).isdigit():
                    raise ValidationError("Documento debe contener sólo dígitos")

                # Convertir fecha de nacimiento
                from celiaquia.services.ciudadano_service import CiudadanoService

                try:
                    payload["fecha_nacimiento"] = CiudadanoService._to_date(
                        payload.get("fecha_nacimiento")
                    )
                except ValidationError as e:
                    raise ValidationError(str(e))

                # CONVERSIÓN OPTIMIZADA: IDs a nombres usando cache
                # Municipio
                municipio_val = payload.get("municipio")
                if municipio_val:
                    municipio_str = str(municipio_val).strip()
                    if (
                        municipio_str
                        and municipio_str != "nan"
                        and municipio_str.replace(".0", "").isdigit()
                    ):
                        municipio_id = int(float(municipio_str))
                        if municipio_id in municipios_cache:
                            payload["municipio"] = municipios_cache[municipio_id]
                        else:
                            add_warning(
                                offset, "municipio", f"{municipio_id} no encontrado"
                            )
                            payload.pop("municipio", None)
                    # Si no es numérico, asumir que ya es nombre
                else:
                    payload.pop("municipio", None)

                # Localidad
                localidad_val = payload.get("localidad")
                if localidad_val:
                    localidad_str = str(localidad_val).strip()
                    if (
                        localidad_str
                        and localidad_str != "nan"
                        and localidad_str.replace(".0", "").isdigit()
                    ):
                        localidad_id = int(float(localidad_str))
                        if localidad_id in localidades_cache:
                            payload["localidad"] = localidades_cache[localidad_id]
                        else:
                            add_warning(
                                offset, "localidad", f"{localidad_id} no encontrado"
                            )
                            payload.pop("localidad", None)
                    # Si no es numérico, asumir que ya es nombre
                else:
                    payload.pop("localidad", None)

                # Resolver sexo y nacionalidad usando cache
                sexo_val = payload.get("sexo")
                if sexo_val:
                    sexo_key = str(sexo_val).strip().lower()
                    if sexo_key in sexos_cache:
                        payload["sexo"] = sexos_cache[sexo_key]
                    else:
                        add_warning(offset, "sexo", f"{sexo_val} no encontrado")
                        payload.pop("sexo", None)
                else:
                    payload.pop("sexo", None)

                nacionalidad_val = payload.get("nacionalidad")
                if nacionalidad_val:
                    nac_key = str(nacionalidad_val).strip().lower()
                    if nac_key in nacionalidades_cache:
                        payload["nacionalidad"] = nacionalidades_cache[nac_key]
                    else:
                        add_warning(
                            offset, "nacionalidad", f"{nacionalidad_val} no encontrado"
                        )
                        payload.pop("nacionalidad", None)
                else:
                    payload.pop("nacionalidad", None)

                # Validar email
                email = payload.get("email")
                if email:
                    try:
                        EmailValidator()(email)
                    except ValidationError:
                        add_warning(offset, "email", f"Email inválido: {email}")
                        payload.pop("email", None)

                # Crear ciudadano - AHORA CON NOMBRES EN LUGAR DE IDs
                try:
                    ciudadano = CiudadanoService.get_or_create_ciudadano(
                        datos=payload,
                        usuario=usuario,
                        expediente=expediente,
                        programa_id=3,
                    )

                    if not ciudadano or not ciudadano.pk:
                        errores += 1
                        detalles_errores.append(
                            {"fila": offset, "error": "No se pudo crear el ciudadano"}
                        )
                        continue

                except Exception as e:
                    logger.error("Error creando ciudadano en fila %s: %s", offset, e)
                    errores += 1
                    detalles_errores.append(
                        {"fila": offset, "error": f"Error creando ciudadano: {str(e)}"}
                    )
                    continue

                cid = ciudadano.pk

                # Validaciones de duplicados
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
                    continue

                if cid in en_programa:
                    prog = en_programa[cid]
                    estado_text = (
                        "ACEPTADO" if prog["es_titular_activo"] else "SUSPENDIDO"
                    )
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
                    continue

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
                            "estado_expediente_origen": conflict[
                                "expediente__estado__nombre"
                            ],
                            "motivo": "Duplicado en otro expediente abierto",
                        }
                    )
                    continue

                # Verificar si hay datos del responsable
                tiene_responsable = any(
                    [
                        payload.get("apellido_responsable"),
                        payload.get("nombre_responsable"),
                        payload.get("fecha_nacimiento_responsable"),
                    ]
                )

                # OK para crear legajo del hijo
                legajos_crear.append(
                    ExpedienteCiudadano(
                        expediente=expediente,
                        ciudadano=ciudadano,
                        estado_id=estado_id,
                    )
                )
                existentes_ids.add(cid)
                validos += 1

                # Si hay datos del responsable, crear también el legajo del responsable
                if tiene_responsable:
                    try:
                        # Preparar datos del responsable
                        responsable_payload = {
                            "apellido": payload.get("apellido_responsable"),
                            "nombre": payload.get("nombre_responsable"),
                            "fecha_nacimiento": payload.get(
                                "fecha_nacimiento_responsable"
                            ),
                            "sexo": payload.get("sexo_responsable"),
                            "telefono": payload.get("telefono_responsable"),
                            "email": payload.get("email_responsable"),
                            "tipo_documento": tipo_doc_cuit_id,
                            "provincia": provincia_usuario_id,
                        }
                        doc_resp = payload.get("documento_responsable")
                        if doc_resp:
                            responsable_payload["documento"] = doc_resp

                        # Procesar domicilio del responsable
                        domicilio_resp = payload.get("domicilio_responsable", "")
                        if domicilio_resp:
                            # Intentar extraer calle y altura del domicilio
                            match = re.match(
                                r"^(.+?)\s+(\d+)\s*$", domicilio_resp.strip()
                            )
                            if match:
                                responsable_payload["calle"] = match.group(1).strip()
                                responsable_payload["altura"] = match.group(2)
                            else:
                                responsable_payload["calle"] = domicilio_resp

                        # Procesar localidad del responsable
                        localidad_resp = payload.get("localidad_responsable")
                        if localidad_resp:
                            # Buscar localidad por nombre
                            try:
                                localidad_obj = Localidad.objects.filter(
                                    nombre__icontains=localidad_resp,
                                    municipio__provincia_id=provincia_usuario_id,
                                ).first()
                                if localidad_obj:
                                    responsable_payload["localidad"] = localidad_obj.pk
                                    responsable_payload["municipio"] = (
                                        localidad_obj.municipio.pk
                                    )
                            except Exception as e:
                                add_warning(
                                    offset,
                                    "localidad_responsable",
                                    f"No se pudo procesar: {e}",
                                )

                        # Generar documento ficticio para el responsable si no tiene
                        if not responsable_payload.get("documento"):
                            # Usar timestamp + offset para generar un documento único
                            import time

                            responsable_payload["documento"] = (
                                f"99{int(time.time())}{offset:04d}"[-11:]
                            )

                        # Convertir fecha de nacimiento del responsable
                        if responsable_payload.get("fecha_nacimiento"):
                            try:
                                responsable_payload["fecha_nacimiento"] = (
                                    CiudadanoService._to_date(
                                        responsable_payload["fecha_nacimiento"]
                                    )
                                )
                            except ValidationError:
                                add_warning(
                                    offset,
                                    "fecha_nacimiento_responsable",
                                    "Fecha inválida",
                                )
                                responsable_payload.pop("fecha_nacimiento", None)

                        # Crear ciudadano responsable
                        ciudadano_responsable = (
                            CiudadanoService.get_or_create_ciudadano(
                                datos=responsable_payload,
                                usuario=usuario,
                                expediente=expediente,
                                programa_id=3,
                            )
                        )

                        if ciudadano_responsable and ciudadano_responsable.pk:
                            cid_resp = ciudadano_responsable.pk

                            # Guardar relacion familiar SIEMPRE
                            pair = (cid_resp, cid)
                            if pair not in relaciones_familiares_pairs:
                                relaciones_familiares_pairs.add(pair)
                                relaciones_familiares.append(
                                    {
                                        "hijo_id": cid,
                                        "responsable_id": cid_resp,
                                        "fila": offset,
                                    }
                                )

                            # Validar duplicados del responsable antes de crear el legajo
                            if cid_resp not in existentes_ids:
                                # Verificar si ya está en otro expediente
                                if cid_resp not in en_programa and cid_resp not in abiertos:
                                    legajos_crear.append(
                                        ExpedienteCiudadano(
                                            expediente=expediente,
                                            ciudadano=ciudadano_responsable,
                                            estado_id=estado_id,
                                        )
                                    )
                                    existentes_ids.add(cid_resp)
                                    validos += 1
                                else:
                                    add_warning(
                                        offset,
                                        "responsable",
                                        "Responsable ya existe en otro expediente",
                                    )
                            # Si ya existe en este expediente, no hacer nada (la relación se guardará igual)

                    except Exception as e:
                        add_warning(
                            offset,
                            "responsable",
                            f"Error creando responsable: {str(e)}",
                        )
                        logger.error(
                            "Error creando responsable en fila %s: %s", offset, e
                        )

            except Exception as e:
                errores += 1
                detalles_errores.append({"fila": offset, "error": str(e)})
                logger.error("Error fila %s: %s", offset, e)

        # Bulk create de legajos
        if legajos_crear:
            try:
                logger.info("Creando %s legajos en bulk_create", len(legajos_crear))
                ExpedienteCiudadano.objects.bulk_create(
                    legajos_crear, batch_size=batch_size
                )
                logger.info("Legajos creados exitosamente")

                # Crear relaciones familiares
                if relaciones_familiares:
                    try:
                        from ciudadanos.models import GrupoFamiliar, VinculoFamiliar

                        # Buscar vinculo "Hijo" y "Padre/Madre"
                        vinculo_hijo = VinculoFamiliar.objects.filter(
                            vinculo__icontains="hijo"
                        ).first()

                        if vinculo_hijo is None:
                            vinculo_hijo = VinculoFamiliar.objects.create(
                                vinculo="Hijo/a",
                                inverso="Padre/Madre",
                            )

                        relaciones_crear = []
                        for rel in relaciones_familiares:
                            try:
                                relaciones_crear.append(
                                    GrupoFamiliar(
                                        ciudadano_1_id=rel["responsable_id"],
                                        ciudadano_2_id=rel["hijo_id"],
                                        vinculo=vinculo_hijo,
                                        vinculo_inverso=vinculo_hijo.inverso,
                                        conviven=True,
                                        cuidador_principal=True,
                                    )
                                )
                            except Exception as e:
                                logger.error(
                                    "Error preparando relacion familiar fila %s: %s",
                                    rel["fila"],
                                    e,
                                )

                        if relaciones_crear:
                            # Eliminar duplicados existentes antes de crear
                            existing_pairs = set(
                                GrupoFamiliar.objects.filter(
                                    ciudadano_1_id__in=[r.ciudadano_1_id for r in relaciones_crear],
                                    ciudadano_2_id__in=[r.ciudadano_2_id for r in relaciones_crear],
                                ).values_list('ciudadano_1_id', 'ciudadano_2_id')
                            )
                            relaciones_crear = [
                                r for r in relaciones_crear 
                                if (r.ciudadano_1_id, r.ciudadano_2_id) not in existing_pairs
                            ]
                            if relaciones_crear:
                                GrupoFamiliar.objects.bulk_create(
                                    relaciones_crear,
                                    batch_size=batch_size,
                                    ignore_conflicts=True,
                                )
                            logger.info(
                                "Creadas %s relaciones familiares",
                                len(relaciones_crear),
                            )
                    except Exception as e:
                        logger.error("Error creando relaciones familiares: %s", e)
                        warnings.append(
                            {
                                "fila": "general",
                                "campo": "relaciones_familiares",
                                "detalle": f"Error creando relaciones: {str(e)}",
                            }
                        )

            except Exception as e:
                logger.error("Error en bulk_create de legajos: %s", e)
        else:
            logger.warning("No hay legajos para crear - lista vacía")

        logger.info(
            "Import completo: %s válidos, %s errores, %s excluidos.",
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
            "relaciones_familiares_creadas": len(relaciones_familiares),
        }
