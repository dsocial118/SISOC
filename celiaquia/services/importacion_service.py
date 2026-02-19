import logging
from functools import lru_cache
from io import BytesIO
import re

import pandas as pd
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.db import transaction
from django.db.models import Q

from ciudadanos.models import Ciudadano
from core.models import Provincia, Municipio, Localidad, Sexo
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


def _get_tipo_documento(doc_str):
    """Retorna el tipo de documento basado en la longitud"""
    if len(str(doc_str or "")) == 11:
        return Ciudadano.DOCUMENTO_CUIT
    return Ciudadano.DOCUMENTO_DNI


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


def validar_edad_responsable(fecha_nac_responsable, fecha_nac_beneficiario):
    """Valida edad del responsable vs beneficiario. Retorna (ok, warnings, error)."""
    from datetime import date

    warnings_edad = []
    error = None

    if not fecha_nac_responsable or not fecha_nac_beneficiario:
        return True, warnings_edad, None

    try:
        edad_responsable = (date.today() - fecha_nac_responsable).days // 365
        edad_beneficiario = (date.today() - fecha_nac_beneficiario).days // 365

        if edad_responsable < 18:
            error = f"Responsable debe ser mayor de 18 anos (tiene {edad_responsable})"
        elif edad_responsable < edad_beneficiario:
            error = "Responsable mas joven que beneficiario"
    except Exception as e:
        logger.warning("Error validando edad: %s", e)
        return True, warnings_edad, None

    return error is None, warnings_edad, error


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

        # Almacenar datos en sesión para paginación
        preview_data = {
            "headers": headers,
            "rows": rows_with_id,
            "total_rows": total_rows,
            "shown_rows": len(sample),
            "all_rows": (
                df.to_dict(orient="records")
                if limit is None
                else df.head(5000).to_dict(orient="records")
            ),
        }

        return preview_data

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
        # Limpiar espacios en blanco de todos los valores
        df = df.map(lambda x: str(x).strip() if isinstance(x, str) else x)
        if "fecha_nacimiento" in df.columns:
            df["fecha_nacimiento"] = df["fecha_nacimiento"].apply(
                lambda x: x.date() if hasattr(x, "date") else x
            )

        estado_id = _estado_doc_pendiente_id()

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
            logger.warning(
                "Usuario sin provincia configurada; se importara sin filtro provincial."
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
            "documento_responsable",
            "telefono_responsable",
            "contacto_responsable",
        }

        def add_warning(fila, campo, detalle):
            warnings.append({"fila": fila, "campo": campo, "detalle": detalle})
            logger.warning("Fila %s: %s (%s)", fila, detalle, campo)

        def add_error(fila, campo, detalle):
            raise ValidationError(f"Fila {fila}: {detalle} ({campo})")

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
            municipios_qs = Municipio.objects.filter(pk__in=municipio_ids)
            if provincia_usuario_id:
                municipios_qs = municipios_qs.filter(provincia_id=provincia_usuario_id)
            for m in municipios_qs:
                municipios_cache[m.pk] = m.pk

        if localidad_ids:
            for l in Localidad.objects.filter(pk__in=localidad_ids):
                localidades_cache[l.pk] = l.pk

        # Cargar sexos con mapeo mejorado
        try:
            for s in Sexo.objects.all():
                sexo_lower = s.sexo.lower()
                sexos_cache[sexo_lower] = s.id
                # Agregar mapeos comunes
                if (
                    "masculino" in sexo_lower
                    or "hombre" in sexo_lower
                    or "male" in sexo_lower
                ):
                    sexos_cache["m"] = s.id
                    sexos_cache["masculino"] = s.id
                    sexos_cache["hombre"] = s.id
                elif (
                    "femenino" in sexo_lower
                    or "mujer" in sexo_lower
                    or "female" in sexo_lower
                ):
                    sexos_cache["f"] = s.id
                    sexos_cache["femenino"] = s.id
                    sexos_cache["mujer"] = s.id
        except Exception as e:
            logger.warning("Error cargando sexos: %s", e)

        # Funciones de validación
        def validar_documento(doc_str, campo_nombre, fila):
            """Valida formato y longitud de documento"""
            if not doc_str or not doc_str.isdigit():
                raise ValidationError(f"{campo_nombre} debe contener solo dígitos")

            doc_len = len(doc_str)

            # Validar longitud según tipo
            if campo_nombre == "documento":
                # Aceptar DNI (10-11 dígitos) o CUIT (11 dígitos con prefijos 20/23/27)
                if doc_len == 11:
                    # Podría ser CUIT o DNI de 11 dígitos
                    if doc_str.startswith(("20", "23", "27")):
                        # Es CUIT válido
                        pass
                    else:
                        # Es DNI de 11 dígitos
                        pass
                elif doc_len == 10:
                    # DNI de 10 dígitos
                    pass
                else:
                    raise ValidationError(
                        f"{campo_nombre} debe tener entre 10 y 11 dígitos"
                    )
            elif (
                "responsable" in campo_nombre
                and "telefono" not in campo_nombre
                and "contacto" not in campo_nombre
            ):
                if doc_len == 11:
                    # Podría ser CUIT o DNI de 11 dígitos
                    if doc_str.startswith(("20", "23", "27")):
                        # Es CUIT válido
                        pass
                    else:
                        # Es DNI de 11 dígitos
                        pass
                elif doc_len == 10:
                    # DNI de 10 dígitos
                    pass
                else:
                    raise ValidationError(
                        f"{campo_nombre} debe tener entre 10 y 11 dígitos"
                    )

            return doc_str

        def normalizar_sexo(sexo_valor):
            """Normaliza valores de sexo comunes"""
            if not sexo_valor:
                return None

            sexo_lower = str(sexo_valor).strip().lower()
            return sexos_cache.get(sexo_lower)

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
                            # Validar documento después de limpiar
                            try:
                                validar_documento(cleaned, field, offset)
                                payload[field] = cleaned
                            except ValidationError as e:
                                raise ValidationError(f"{field}: {str(e)}")
                        else:
                            payload[field] = None
                            if v:
                                add_warning(offset, field, "valor numerico vacio")
                    else:
                        if v.lower() in {"nan", "nat", "none"}:
                            payload[field] = None
                        else:
                            payload[field] = v or None

                # Asignar tipo de documento basado en longitud
                payload["tipo_documento"] = _get_tipo_documento(
                    payload.get("documento", "")
                )

                # Asignar provincia del usuario si existe
                if provincia_usuario_id:
                    payload["provincia"] = provincia_usuario_id

                required = [
                    "apellido",
                    "nombre",
                    "documento",
                    "fecha_nacimiento",
                ]
                for req in required:
                    if not payload.get(req):
                        raise ValidationError(f"Campo obligatorio faltante: {req}")

                doc = payload.get("documento")
                if not doc:
                    raise ValidationError("Documento es obligatorio")
                if not str(doc).isdigit():
                    raise ValidationError("Documento debe contener sólo dígitos")

                # Convertir fecha de nacimiento
                from celiaquia.services.ciudadano_service import CiudadanoService

                try:
                    payload["fecha_nacimiento"] = CiudadanoService._to_date(
                        payload.get("fecha_nacimiento")
                    )
                except ValidationError as e:
                    # Si la fecha es inválida, registrar error pero continuar
                    add_warning(
                        offset,
                        "fecha_nacimiento",
                        f"Fecha inválida: {payload.get('fecha_nacimiento')} - {str(e)}",
                    )
                    raise ValidationError(
                        f"Fecha de nacimiento inválida: {payload.get('fecha_nacimiento')}"
                    )

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

                # Resolver sexo usando normalización mejorada
                sexo_val = payload.get("sexo")
                if sexo_val:
                    sexo_id = normalizar_sexo(sexo_val)
                    if sexo_id:
                        payload["sexo"] = sexo_id
                    else:
                        raise ValidationError(
                            f"Sexo '{sexo_val}' no válido. Use M/F, Masculino/Femenino, etc."
                        )
                else:
                    payload.pop("sexo", None)

                # Resolver nacionalidad
                nacionalidad_val = payload.get("nacionalidad")
                if nacionalidad_val:
                    # Intentar resolver por nombre
                    from core.models import Nacionalidad

                    nacionalidad_obj = Nacionalidad.objects.filter(
                        nacionalidad__iexact=str(nacionalidad_val).strip()
                    ).first()
                    if nacionalidad_obj:
                        payload["nacionalidad"] = nacionalidad_obj.pk
                    else:
                        # Si no encuentra, usar Argentina como default
                        argentina = Nacionalidad.objects.filter(
                            nacionalidad__iexact="Argentina"
                        ).first()
                        if argentina:
                            payload["nacionalidad"] = argentina.pk
                        else:
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

                # Validar teléfono si existe
                telefono = payload.get("telefono")
                if telefono and len(telefono) < 8:
                    raise ValidationError(
                        f"Teléfono '{telefono}' debe tener al menos 8 dígitos"
                    )

                # Crear ciudadano - AHORA CON NOMBRES EN LUGAR DE IDs
                try:
                    ciudadano = CiudadanoService.get_or_create_ciudadano(
                        datos=payload,
                        usuario=usuario,
                        expediente=expediente,
                    )

                    if not ciudadano or not ciudadano.pk:
                        errores += 1
                        datos_para_guardar = {
                            k: v for k, v in payload.items() if v is not None
                        }
                        detalles_errores.append(
                            {
                                "fila": offset,
                                "error": "No se pudo crear el ciudadano",
                                "datos": datos_para_guardar,
                            }
                        )
                        continue

                except Exception as e:
                    logger.error("Error creando ciudadano en fila %s: %s", offset, e)
                    errores += 1
                    # Guardar payload procesado con los datos que se intentaron usar
                    datos_para_guardar = {
                        k: v for k, v in payload.items() if v is not None
                    }
                    detalles_errores.append(
                        {
                            "fila": offset,
                            "error": f"Error creando ciudadano: {str(e)}",
                            "datos": datos_para_guardar,
                        }
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

                # Detectar si responsable = beneficiario
                doc_beneficiario = payload.get("documento")
                doc_responsable = payload.get("documento_responsable")

                es_mismo_documento = (
                    tiene_responsable
                    and doc_responsable
                    and str(doc_responsable).strip() == str(doc_beneficiario).strip()
                )

                # Determinar rol del beneficiario
                rol_beneficiario = ExpedienteCiudadano.ROLE_BENEFICIARIO

                # OK para crear legajo del beneficiario CON ROL
                legajos_crear.append(
                    ExpedienteCiudadano(
                        expediente=expediente,
                        ciudadano=ciudadano,
                        estado_id=estado_id,
                        rol=rol_beneficiario,
                    )
                )
                existentes_ids.add(cid)
                abiertos[cid] = {
                    "ciudadano_id": cid,
                    "estado_cupo": EstadoCupo.NO_EVAL,
                    "es_titular_activo": False,
                    "expediente_id": expediente.id,
                    "expediente__estado__nombre": expediente.estado.nombre,
                }
                validos += 1

                # Si hay datos del responsable, crear también el ciudadano y vínculo
                if tiene_responsable:
                    try:
                        # Validar mínimos obligatorios del responsable
                        if not payload.get("documento_responsable"):
                            add_error(
                                offset,
                                "documento_responsable",
                                "Documento del responsable obligatorio",
                            )
                        if not payload.get("nombre_responsable"):
                            add_error(
                                offset,
                                "nombre_responsable",
                                "Nombre del responsable obligatorio",
                            )

                        # Preparar datos del responsable
                        responsable_payload = {
                            "apellido": payload.get("apellido_responsable"),
                            "nombre": payload.get("nombre_responsable"),
                            "fecha_nacimiento": payload.get(
                                "fecha_nacimiento_responsable"
                            ),
                            "telefono": payload.get("telefono_responsable"),
                            "email": payload.get("email_responsable"),
                            "documento": payload.get("documento_responsable"),
                            "tipo_documento": _get_tipo_documento(
                                payload.get("documento_responsable", "")
                            ),
                            "provincia": provincia_usuario_id,
                        }

                        # Resolver sexo del responsable
                        sexo_resp_val = payload.get("sexo_responsable")
                        if sexo_resp_val:
                            sexo_resp_id = normalizar_sexo(sexo_resp_val)
                            if sexo_resp_id:
                                responsable_payload["sexo"] = sexo_resp_id

                        # Verificar si el responsable es la misma persona que el beneficiario
                        es_mismo_documento_resp = (
                            doc_responsable
                            and str(doc_responsable).strip()
                            == str(payload.get("documento", "")).strip()
                        )

                        cid_resp = None
                        if es_mismo_documento_resp:
                            # Es la misma persona - solo crear la relación familiar pero no duplicar el legajo
                            cid_resp = cid  # Usar el mismo ciudadano
                            add_warning(
                                offset,
                                "responsable",
                                "Responsable es el mismo beneficiario - no se duplica legajo",
                            )
                        else:
                            # Procesar domicilio del responsable
                            domicilio_resp = payload.get("domicilio_responsable", "")
                            if domicilio_resp:
                                # Intentar extraer calle y altura del domicilio
                                match = re.match(
                                    r"^(.+?)\s+(\d+)\s*$", domicilio_resp.strip()
                                )
                                if match:
                                    responsable_payload["calle"] = match.group(
                                        1
                                    ).strip()
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
                                        responsable_payload["localidad"] = (
                                            localidad_obj.pk
                                        )
                                        responsable_payload["municipio"] = (
                                            localidad_obj.municipio.pk
                                        )
                                except Exception as e:
                                    add_warning(
                                        offset,
                                        "localidad_responsable",
                                        f"No se pudo procesar: {e}",
                                    )

                            # Convertir fecha de nacimiento del responsable
                            if responsable_payload.get("fecha_nacimiento"):
                                try:
                                    responsable_payload["fecha_nacimiento"] = (
                                        CiudadanoService._to_date(
                                            responsable_payload["fecha_nacimiento"]
                                        )
                                    )
                                except ValidationError as e:
                                    add_warning(
                                        offset,
                                        "fecha_nacimiento_responsable",
                                        f"Fecha inválida: {responsable_payload.get('fecha_nacimiento')} - {str(e)}",
                                    )
                                    responsable_payload.pop("fecha_nacimiento", None)

                            # Crear ciudadano responsable
                            ciudadano_responsable = (
                                CiudadanoService.get_or_create_ciudadano(
                                    datos=responsable_payload,
                                    usuario=usuario,
                                    expediente=expediente,
                                )
                            )

                            if ciudadano_responsable and ciudadano_responsable.pk:
                                cid_resp = ciudadano_responsable.pk

                                # Validar edad SOLO si se creó un nuevo responsable con fecha de nacimiento
                                if responsable_payload.get("fecha_nacimiento"):
                                    valido_edad, edad_warnings, error_edad = (
                                        validar_edad_responsable(
                                            responsable_payload.get("fecha_nacimiento"),
                                            payload.get("fecha_nacimiento"),
                                        )
                                    )
                                    # Agregar warnings ANTES de verificar errores
                                    for warning in edad_warnings:
                                        add_warning(offset, "edad", warning)
                                    if error_edad:
                                        add_warning(
                                            offset, "edad_responsable", error_edad
                                        )

                                # Crear legajo del responsable si no existe ya
                                if cid_resp not in existentes_ids:
                                    legajos_crear.append(
                                        ExpedienteCiudadano(
                                            expediente=expediente,
                                            ciudadano=ciudadano_responsable,
                                            estado_id=estado_id,
                                            rol=ExpedienteCiudadano.ROLE_RESPONSABLE,
                                        )
                                    )
                                    existentes_ids.add(cid_resp)

                        # Crear GrupoFamiliar SOLO si son personas diferentes
                        if not es_mismo_documento_resp and cid_resp:
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
                error_msg = str(e)
                # Guardar datos originales del row antes de cualquier procesamiento
                datos_originales = {
                    k: v
                    for k, v in row.items()
                    if v
                    and str(v).strip()
                    and str(v).lower() not in ["nan", "nat", "none"]
                }
                detalles_errores.append(
                    {"fila": offset, "error": error_msg, "datos": datos_originales}
                )
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
                        from ciudadanos.models import GrupoFamiliar

                        relaciones_creadas = 0
                        for rel in relaciones_familiares:
                            try:
                                _, created = GrupoFamiliar.objects.get_or_create(
                                    ciudadano_1_id=rel["responsable_id"],
                                    ciudadano_2_id=rel["hijo_id"],
                                    defaults={
                                        "vinculo": GrupoFamiliar.RELACION_PADRE,
                                        "estado_relacion": GrupoFamiliar.ESTADO_BUENO,
                                        "conviven": True,
                                        "cuidador_principal": True,
                                    },
                                )
                                if created:
                                    relaciones_creadas += 1
                            except Exception as e:
                                logger.error(
                                    "Error creando relacion familiar fila %s: %s",
                                    rel["fila"],
                                    e,
                                )

                        logger.info(
                            "Creadas %s relaciones familiares",
                            relaciones_creadas,
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

        # Guardar registros erróneos en la base de datos
        if detalles_errores:
            from celiaquia.models import RegistroErroneo
            import datetime

            def serializar_datos(datos):
                """Convierte objetos date/datetime a strings para JSON"""
                resultado = {}
                for key, value in datos.items():
                    if isinstance(value, (datetime.date, datetime.datetime)):
                        resultado[key] = value.strftime("%d/%m/%Y")
                    else:
                        resultado[key] = value
                return resultado

            registros_erroneos = []
            for detalle in detalles_errores:
                datos_serializados = serializar_datos(detalle.get("datos", {}))
                registros_erroneos.append(
                    RegistroErroneo(
                        expediente=expediente,
                        fila_excel=detalle.get("fila", 0),
                        datos_raw=datos_serializados,
                        mensaje_error=detalle.get("error", ""),
                    )
                )
            if registros_erroneos:
                RegistroErroneo.objects.bulk_create(
                    registros_erroneos, batch_size=batch_size
                )
                logger.info("Guardados %s registros erróneos", len(registros_erroneos))

        # Post-procesamiento: Detectar y crear relaciones familiares cruzadas
        relaciones_cruzadas_creadas = 0
        try:
            from ciudadanos.models import GrupoFamiliar

            # Obtener todos los legajos del expediente
            legajos_expediente = ExpedienteCiudadano.objects.filter(
                expediente=expediente
            ).select_related("ciudadano")

            # Agrupar por ciudadano
            ciudadanos_roles = {}
            for legajo in legajos_expediente:
                cid = legajo.ciudadano_id
                if cid not in ciudadanos_roles:
                    ciudadanos_roles[cid] = []
                ciudadanos_roles[cid].append(legajo.rol)

            # Buscar relaciones responsable-beneficiario que no estén vinculadas
            responsables = legajos_expediente.filter(
                rol=ExpedienteCiudadano.ROLE_RESPONSABLE
            ).values_list("ciudadano_id", flat=True)

            beneficiarios = legajos_expediente.filter(
                rol=ExpedienteCiudadano.ROLE_BENEFICIARIO
            ).values_list("ciudadano_id", flat=True)

            # Detectar ciudadanos que son ambos responsable y beneficiario
            ambos_roles = set(responsables) & set(beneficiarios)

            for ciudadano_id in ambos_roles:
                # Obtener los legajos de este ciudadano
                legajo_responsable = legajos_expediente.filter(
                    ciudadano_id=ciudadano_id, rol=ExpedienteCiudadano.ROLE_RESPONSABLE
                ).first()

                legajo_beneficiario = legajos_expediente.filter(
                    ciudadano_id=ciudadano_id, rol=ExpedienteCiudadano.ROLE_BENEFICIARIO
                ).first()

                if legajo_responsable and legajo_beneficiario:
                    # Actualizar el rol del beneficiario a "Beneficiario y Responsable"
                    legajo_beneficiario.rol = (
                        ExpedienteCiudadano.ROLE_BENEFICIARIO_Y_RESPONSABLE
                    )
                    legajo_beneficiario.save(update_fields=["rol"])

                    # Eliminar el legajo duplicado del responsable
                    legajo_responsable.delete()
                    relaciones_cruzadas_creadas += 1
                    logger.info(
                        "Consolidado ciudadano %s: rol actualizado a BENEFICIARIO_Y_RESPONSABLE",
                        ciudadano_id,
                    )

            # Post-procesamiento: Los beneficiarios sin relaciones familiares mantienen su rol BENEFICIARIO
            # No se cambia automáticamente a RESPONSABLE
        except Exception as e:
            logger.error("Error en post-procesamiento de relaciones cruzadas: %s", e)
            warnings.append(
                {
                    "fila": "general",
                    "campo": "relaciones_cruzadas",
                    "detalle": f"Error procesando relaciones cruzadas: {str(e)}",
                }
            )

        logger.info(
            "Import completo: %s legajos creados, %s errores, %s excluidos, %s relaciones cruzadas.",
            len(legajos_crear),
            errores,
            len(excluidos),
            relaciones_cruzadas_creadas,
        )

        return {
            "validos": len(legajos_crear),
            "errores": errores,
            "detalles_errores": detalles_errores,
            "excluidos_count": len(excluidos),
            "excluidos": excluidos,
            "warnings": warnings,
            "relaciones_familiares_creadas": len(relaciones_familiares),
            "relaciones_cruzadas_consolidadas": relaciones_cruzadas_creadas,
        }
