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

IMPORTACION_COLUMN_MAP = {
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
    "sexo_1": "sexo_responsable",
    "nacionalidad": "nacionalidad",
    "municipio": "municipio",
    "localidad": "localidad",
    "email": "email",
    "telefono": "telefono",
    "codigo_postal": "codigo_postal",
    "calle": "calle",
    "altura": "altura",
    "apellido_responsable": "apellido_responsable",
    "nombre_responsable": "nombre_responsable",
    "nombre_repsonsable": "nombre_responsable",
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

IMPORTACION_REQUIRED_FIELDS = (
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
    "apellido_responsable",
    "nombre_responsable",
    "documento_responsable",
    "fecha_nacimiento_responsable",
    "sexo_responsable",
    "domicilio_responsable",
    "localidad_responsable",
)

IMPORTACION_OPTIONAL_FIELDS = (
    "telefono",
    "email",
    "telefono_responsable",
    "email_responsable",
)

IMPORTACION_RESPONSABLE_REQUIRED_FIELDS = (
    "apellido_responsable",
    "nombre_responsable",
    "documento_responsable",
    "fecha_nacimiento_responsable",
    "sexo_responsable",
    "domicilio_responsable",
    "localidad_responsable",
)

IMPORTACION_EDITABLE_FIELDS = (
    *IMPORTACION_REQUIRED_FIELDS,
    *IMPORTACION_OPTIONAL_FIELDS,
)


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


def _leer_excel_importacion(data: bytes) -> pd.DataFrame:
    try:
        return pd.read_excel(BytesIO(data), engine="openpyxl", dtype=str)
    except Exception as exc:
        raise ValidationError(f"No se pudo leer Excel: {exc}") from exc


def _normalizar_dataframe_importacion(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    normalized_cols = [_norm_col(col) for col in df.columns]
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

    present = [c for c in df.columns if c in IMPORTACION_COLUMN_MAP]
    df = (
        df[present]
        .rename(columns={c: IMPORTACION_COLUMN_MAP[c] for c in present})
        .fillna("")
    )
    df = df.loc[:, ~df.columns.duplicated()]
    df = df.map(lambda x: str(x).strip() if isinstance(x, str) else x)

    if "fecha_nacimiento" in df.columns:
        df["fecha_nacimiento"] = df["fecha_nacimiento"].apply(
            lambda x: x.date() if hasattr(x, "date") else x
        )

    return df


def _obtener_provincia_usuario_id(usuario):
    provincia_usuario_id = None
    try:
        if (
            hasattr(usuario, "profile")
            and usuario.profile
            and usuario.profile.provincia_id
        ):
            provincia_usuario_id = usuario.profile.provincia_id
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.warning("No se pudo obtener provincia del usuario: %s", exc)

    if not provincia_usuario_id:
        logger.warning(
            "Usuario sin provincia configurada; se importara sin filtro provincial."
        )

    return provincia_usuario_id


def _colectar_ids_y_nombres_importacion(df: pd.DataFrame):
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

    return {
        "municipio_ids": municipio_ids,
        "localidad_ids": localidad_ids,
        "sexos_nombres": sexos_nombres,
        "nacionalidades_nombres": nacionalidades_nombres,
    }


def _cargar_municipios_cache(municipio_ids, provincia_usuario_id):
    municipios_cache = {}
    if not municipio_ids:
        return municipios_cache

    municipios_qs = Municipio.objects.filter(pk__in=municipio_ids)
    if provincia_usuario_id:
        municipios_qs = municipios_qs.filter(provincia_id=provincia_usuario_id)
    for municipio in municipios_qs:
        municipios_cache[municipio.pk] = municipio.pk
    return municipios_cache


def _cargar_localidades_cache(localidad_ids):
    localidades_cache = {}
    if not localidad_ids:
        return localidades_cache

    for localidad in Localidad.objects.filter(pk__in=localidad_ids):
        localidades_cache[localidad.pk] = localidad.pk
    return localidades_cache


def _cargar_sexos_cache():
    sexos_cache = {}
    try:
        for sexo in Sexo.objects.all():
            sexo_lower = sexo.sexo.lower()
            sexos_cache[sexo_lower] = sexo.id
            if (
                "masculino" in sexo_lower
                or "hombre" in sexo_lower
                or "male" in sexo_lower
            ):
                sexos_cache["m"] = sexo.id
                sexos_cache["masculino"] = sexo.id
                sexos_cache["hombre"] = sexo.id
            elif (
                "femenino" in sexo_lower
                or "mujer" in sexo_lower
                or "female" in sexo_lower
            ):
                sexos_cache["f"] = sexo.id
                sexos_cache["femenino"] = sexo.id
                sexos_cache["mujer"] = sexo.id
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.warning("Error cargando sexos: %s", exc)
    return sexos_cache


def _precargar_datos_importacion(df: pd.DataFrame, provincia_usuario_id):
    lookup_values = _colectar_ids_y_nombres_importacion(df)
    return {
        "municipios_cache": _cargar_municipios_cache(
            lookup_values["municipio_ids"], provincia_usuario_id
        ),
        "localidades_cache": _cargar_localidades_cache(lookup_values["localidad_ids"]),
        "sexos_cache": _cargar_sexos_cache(),
        "nacionalidades_nombres": lookup_values["nacionalidades_nombres"],
        "sexos_nombres": lookup_values["sexos_nombres"],
    }


def _agregar_warning_general_importacion(warnings, campo, detalle):
    warnings.append(
        {
            "fila": "general",
            "campo": campo,
            "detalle": detalle,
        }
    )


def _crear_relacion_familiar_importacion(rel, grupo_familiar_model):
    return grupo_familiar_model.objects.get_or_create(
        ciudadano_1_id=rel["responsable_id"],
        ciudadano_2_id=rel["hijo_id"],
        defaults={
            "vinculo": grupo_familiar_model.RELACION_PADRE,
            "estado_relacion": grupo_familiar_model.ESTADO_BUENO,
            "conviven": True,
            "cuidador_principal": True,
        },
    )


def _crear_relaciones_familiares_importacion(relaciones_familiares, warnings):
    if not relaciones_familiares:
        return

    try:
        from ciudadanos.models import GrupoFamiliar

        relaciones_creadas = 0
        for rel in relaciones_familiares:
            try:
                _, created = _crear_relacion_familiar_importacion(rel, GrupoFamiliar)
                if created:
                    relaciones_creadas += 1
            except Exception as exc:  # pylint: disable=broad-exception-caught
                logger.error(
                    "Error creando relacion familiar fila %s: %s",
                    rel["fila"],
                    exc,
                )

        logger.info("Creadas %s relaciones familiares", relaciones_creadas)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.error("Error creando relaciones familiares: %s", exc)
        _agregar_warning_general_importacion(
            warnings,
            "relaciones_familiares",
            f"Error creando relaciones: {str(exc)}",
        )


def _persistir_legajos_importacion(
    legajos_crear, batch_size, relaciones_familiares, warnings
):
    if not legajos_crear:
        logger.warning("No hay legajos para crear - lista vacía")
        return

    try:
        logger.info("Creando %s legajos en bulk_create", len(legajos_crear))
        ExpedienteCiudadano.objects.bulk_create(legajos_crear, batch_size=batch_size)
        logger.info("Legajos creados exitosamente")
        _crear_relaciones_familiares_importacion(relaciones_familiares, warnings)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.error("Error en bulk_create de legajos: %s", exc)
        raise


def _serializar_datos_importacion_para_json(datos):
    import datetime

    resultado = {}
    for key, value in datos.items():
        if isinstance(value, (datetime.date, datetime.datetime)):
            resultado[key] = value.strftime("%d/%m/%Y")
        else:
            resultado[key] = value
    return resultado


def _guardar_registros_erroneos_importacion(expediente, detalles_errores, batch_size):
    if not detalles_errores:
        return

    from celiaquia.models import RegistroErroneo

    registros_erroneos = []
    for detalle in detalles_errores:
        datos_serializados = _serializar_datos_importacion_para_json(
            detalle.get("datos", {})
        )
        registros_erroneos.append(
            RegistroErroneo(
                expediente=expediente,
                fila_excel=detalle.get("fila", 0),
                datos_raw=datos_serializados,
                mensaje_error=detalle.get("error", ""),
            )
        )

    if registros_erroneos:
        RegistroErroneo.objects.bulk_create(registros_erroneos, batch_size=batch_size)
        logger.info("Guardados %s registros erróneos", len(registros_erroneos))


def _obtener_ids_con_roles_cruzados_importacion(legajos_expediente):
    responsables = legajos_expediente.filter(
        rol=ExpedienteCiudadano.ROLE_RESPONSABLE
    ).values_list("ciudadano_id", flat=True)
    beneficiarios = legajos_expediente.filter(
        rol=ExpedienteCiudadano.ROLE_BENEFICIARIO
    ).values_list("ciudadano_id", flat=True)
    return set(responsables) & set(beneficiarios)


def _consolidar_ciudadano_roles_cruzados_importacion(legajos_expediente, ciudadano_id):
    legajo_responsable = legajos_expediente.filter(
        ciudadano_id=ciudadano_id, rol=ExpedienteCiudadano.ROLE_RESPONSABLE
    ).first()
    legajo_beneficiario = legajos_expediente.filter(
        ciudadano_id=ciudadano_id, rol=ExpedienteCiudadano.ROLE_BENEFICIARIO
    ).first()

    if not (legajo_responsable and legajo_beneficiario):
        return False

    legajo_beneficiario.rol = ExpedienteCiudadano.ROLE_BENEFICIARIO_Y_RESPONSABLE
    legajo_beneficiario.save(update_fields=["rol"])

    if hasattr(legajo_responsable, "hard_delete"):
        legajo_responsable.hard_delete()
    else:
        legajo_responsable.delete()

    logger.info(
        "Consolidado ciudadano %s: rol actualizado a BENEFICIARIO_Y_RESPONSABLE",
        ciudadano_id,
    )
    return True


def _consolidar_roles_cruzados_importacion(expediente, warnings):
    relaciones_cruzadas_creadas = 0
    try:
        legajos_expediente = ExpedienteCiudadano.objects.filter(
            expediente=expediente
        ).select_related("ciudadano")
        ambos_roles = _obtener_ids_con_roles_cruzados_importacion(legajos_expediente)

        for ciudadano_id in ambos_roles:
            if _consolidar_ciudadano_roles_cruzados_importacion(
                legajos_expediente, ciudadano_id
            ):
                relaciones_cruzadas_creadas += 1

        # Consolidar beneficiarios que son responsables de otros
        _consolidar_beneficiarios_que_son_responsables(expediente, warnings)

    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.error("Error en post-procesamiento de relaciones cruzadas: %s", exc)
        _agregar_warning_general_importacion(
            warnings,
            "relaciones_cruzadas",
            f"Error procesando relaciones cruzadas: {str(exc)}",
        )

    return relaciones_cruzadas_creadas


def _consolidar_beneficiarios_que_son_responsables(expediente, warnings):
    """Actualiza beneficiarios que también son responsables de otros a doble rol."""
    from ciudadanos.models import GrupoFamiliar

    # Obtener todos los responsables (ciudadanos que tienen hijos)
    responsables_ids = set(
        GrupoFamiliar.objects.filter(vinculo=GrupoFamiliar.RELACION_PADRE).values_list(
            "ciudadano_1_id", flat=True
        )
    )

    # Buscar legajos beneficiarios cuyo ciudadano es responsable de otros
    legajos_beneficiarios = ExpedienteCiudadano.objects.filter(
        expediente=expediente,
        rol=ExpedienteCiudadano.ROLE_BENEFICIARIO,
        ciudadano_id__in=responsables_ids,
    )

    actualizados = 0
    for legajo in legajos_beneficiarios:
        legajo.rol = ExpedienteCiudadano.ROLE_BENEFICIARIO_Y_RESPONSABLE
        legajo.save(update_fields=["rol"])
        actualizados += 1
        logger.info(
            "Actualizado legajo %s a BENEFICIARIO_Y_RESPONSABLE (doc: %s)",
            legajo.id,
            legajo.ciudadano.documento,
        )

    if actualizados > 0:
        _agregar_warning_general_importacion(
            warnings,
            "consolidacion_roles",
            f"Se actualizaron {actualizados} beneficiarios a doble rol",
        )


def _parse_numeric_field_importacion(
    *, field, value_str, offset, validar_documento, add_warning
):
    cleaned = re.sub(r"\D", "", value_str)
    if not cleaned:
        if value_str:
            raise ValidationError(f"{field} debe contener solo dígitos")
        return None

    try:
        validar_documento(cleaned, field, offset)
    except ValidationError as exc:
        raise ValidationError(f"{field}: {str(exc)}") from exc
    return cleaned


def _parse_scalar_field_importacion(value_str):
    if value_str.lower() in {"nan", "nat", "none"}:
        return None
    return value_str or None


def _build_payload_importacion_from_row(
    row, numeric_fields, offset, validar_documento, add_warning
):
    payload = {}
    for field, value in row.items():
        value_str = str(value).strip()
        if field in numeric_fields:
            payload[field] = _parse_numeric_field_importacion(
                field=field,
                value_str=value_str,
                offset=offset,
                validar_documento=validar_documento,
                add_warning=add_warning,
            )
            continue

        payload[field] = _parse_scalar_field_importacion(value_str)

    return payload


def _valor_tiene_contenido_importacion(value):
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True


def listar_campos_faltantes_importacion(
    payload, required_fields=IMPORTACION_REQUIRED_FIELDS
):
    return [
        field
        for field in required_fields
        if not _valor_tiene_contenido_importacion(payload.get(field))
    ]


def validar_campos_obligatorios_importacion(
    payload, required_fields=IMPORTACION_REQUIRED_FIELDS
):
    faltantes = listar_campos_faltantes_importacion(
        payload=payload,
        required_fields=required_fields,
    )
    if faltantes:
        raise ValidationError(f"Faltan campos obligatorios: {', '.join(faltantes)}")


def _aplicar_defaults_y_validar_payload_importacion(payload, provincia_usuario_id):
    payload["tipo_documento"] = _get_tipo_documento(payload.get("documento", ""))

    if provincia_usuario_id:
        payload["provincia"] = provincia_usuario_id

    validar_campos_obligatorios_importacion(payload)

    doc = payload.get("documento")
    if not doc:
        raise ValidationError("Documento es obligatorio")
    if not str(doc).isdigit():
        raise ValidationError("Documento debe contener sólo dígitos")


def _payload_sin_nulos(payload):
    return {k: v for k, v in payload.items() if v is not None}


def _build_datos_originales_error_importacion(row):
    return {
        k: v
        for k, v in row.items()
        if v and str(v).strip() and str(v).lower() not in ["nan", "nat", "none"]
    }


def _append_detalle_error_importacion(detalles_errores, fila, error, datos):
    detalles_errores.append({"fila": fila, "error": error, "datos": datos})


def _registrar_error_creacion_ciudadano_importacion(
    *, payload, offset, detalles_errores, error
):
    _append_detalle_error_importacion(
        detalles_errores=detalles_errores,
        fila=offset,
        error=error,
        datos=_payload_sin_nulos(payload),
    )


def _convertir_fecha_nacimiento_payload_importacion(
    payload, offset, add_warning, to_date
):
    try:
        payload["fecha_nacimiento"] = to_date(payload.get("fecha_nacimiento"))
    except ValidationError as exc:
        raise ValidationError(
            f"Fecha de nacimiento inválida: {payload.get('fecha_nacimiento')}"
        ) from exc


def _resolver_campo_lookup_importacion(payload, field_name, cache, offset, add_warning):
    field_value = payload.get(field_name)
    if not field_value:
        payload.pop(field_name, None)
        return

    field_str = str(field_value).strip()
    if not field_str or field_str == "nan":
        payload.pop(field_name, None)
        return

    if not field_str.replace(".0", "").isdigit():
        raise ValidationError(f"{field_name} debe ser un ID válido")

    field_id = int(float(field_str))
    if field_id not in cache:
        raise ValidationError(f"{field_name} {field_id} no encontrado")
    payload[field_name] = cache[field_id]


def _resolver_municipio_y_localidad_payload_importacion(
    payload, municipios_cache, localidades_cache, offset, add_warning
):
    _resolver_campo_lookup_importacion(
        payload=payload,
        field_name="municipio",
        cache=municipios_cache,
        offset=offset,
        add_warning=add_warning,
    )
    _resolver_campo_lookup_importacion(
        payload=payload,
        field_name="localidad",
        cache=localidades_cache,
        offset=offset,
        add_warning=add_warning,
    )


def _resolver_sexo_payload_importacion(payload, normalizar_sexo):
    sexo_val = payload.get("sexo")
    if not sexo_val:
        payload.pop("sexo", None)
        return

    sexo_str = str(sexo_val).strip()
    if sexo_str.isdigit() and Sexo.objects.filter(pk=int(sexo_str)).exists():
        payload["sexo"] = int(sexo_str)
        return

    sexo_id = normalizar_sexo(sexo_val)
    if not sexo_id:
        raise ValidationError(
            f"Sexo '{sexo_val}' no válido. Use M/F, Masculino/Femenino, etc."
        )
    payload["sexo"] = sexo_id


def _resolver_nacionalidad_payload_importacion(payload):
    nacionalidad_val = payload.get("nacionalidad")
    if not nacionalidad_val:
        payload.pop("nacionalidad", None)
        return

    from core.models import Nacionalidad

    nacionalidad_str = str(nacionalidad_val).strip()
    if nacionalidad_str.isdigit():
        nacionalidad_obj = Nacionalidad.objects.filter(pk=int(nacionalidad_str)).first()
    else:
        nacionalidad_obj = Nacionalidad.objects.filter(
            nacionalidad__iexact=nacionalidad_str
        ).first()

    if not nacionalidad_obj:
        raise ValidationError(f"Nacionalidad inválida: {nacionalidad_val}")
    payload["nacionalidad"] = nacionalidad_obj.pk


def _validar_contacto_payload_importacion(
    payload,
    offset,
    add_warning,
    *,
    email_field="email",
    telefono_field="telefono",
    email_label=None,
    telefono_label=None,
):
    del offset, add_warning
    email = payload.get(email_field)
    if email:
        try:
            EmailValidator()(email)
        except ValidationError as exc:
            raise ValidationError(
                f"{email_label or email_field} inválido: {email}"
            ) from exc

    telefono = payload.get(telefono_field)
    if telefono and len(telefono) < 8:
        raise ValidationError(
            f"{telefono_label or telefono_field} debe tener al menos 8 dígitos"
        )


def _validar_campos_resueltos_payload_importacion(payload):
    validar_campos_obligatorios_importacion(
        payload=payload,
        required_fields=("sexo", "nacionalidad", "municipio", "localidad"),
    )


def _normalizar_enriquecer_payload_importacion(
    payload,
    offset,
    add_warning,
    to_date,
    municipios_cache,
    localidades_cache,
    normalizar_sexo,
):
    _convertir_fecha_nacimiento_payload_importacion(
        payload=payload,
        offset=offset,
        add_warning=add_warning,
        to_date=to_date,
    )
    _resolver_municipio_y_localidad_payload_importacion(
        payload=payload,
        municipios_cache=municipios_cache,
        localidades_cache=localidades_cache,
        offset=offset,
        add_warning=add_warning,
    )
    _resolver_sexo_payload_importacion(payload=payload, normalizar_sexo=normalizar_sexo)
    _resolver_nacionalidad_payload_importacion(payload)
    _validar_contacto_payload_importacion(
        payload=payload,
        offset=offset,
        add_warning=add_warning,
    )
    _validar_campos_resueltos_payload_importacion(payload)


def _extraer_lookup_id_importacion(value):
    if value in (None, ""):
        return None

    value_str = str(value).strip()
    if not value_str or value_str.lower() in {"nan", "nat", "none"}:
        return None
    if not value_str.replace(".0", "").isdigit():
        return None
    return int(float(value_str))


def _build_lookup_caches_payload_importacion(payload, provincia_usuario_id):
    municipio_id = _extraer_lookup_id_importacion(payload.get("municipio"))
    localidad_id = _extraer_lookup_id_importacion(payload.get("localidad"))
    return (
        _cargar_municipios_cache(
            {municipio_id} if municipio_id is not None else set(),
            provincia_usuario_id,
        ),
        _cargar_localidades_cache(
            {localidad_id} if localidad_id is not None else set()
        ),
    )


def _build_responsable_payload_importacion(
    payload, provincia_usuario_id, offset, add_error
):
    del offset, add_error
    validar_campos_obligatorios_importacion(
        payload=payload,
        required_fields=IMPORTACION_RESPONSABLE_REQUIRED_FIELDS,
    )

    return {
        "apellido": payload.get("apellido_responsable"),
        "nombre": payload.get("nombre_responsable"),
        "fecha_nacimiento": payload.get("fecha_nacimiento_responsable"),
        "telefono": payload.get("telefono_responsable"),
        "email": payload.get("email_responsable"),
        "documento": payload.get("documento_responsable"),
        "tipo_documento": _get_tipo_documento(payload.get("documento_responsable", "")),
        "provincia": provincia_usuario_id,
    }


def _validar_y_normalizar_responsable_payload_importacion(
    *,
    payload,
    provincia_usuario_id,
    offset,
    normalizar_sexo,
    to_date,
    add_warning,
    add_error,
    validar_edad_responsable_fn,
):
    responsable_payload = _build_responsable_payload_importacion(
        payload=payload,
        provincia_usuario_id=provincia_usuario_id,
        offset=offset,
        add_error=add_error,
    )
    _agregar_sexo_responsable_payload_importacion(
        responsable_payload=responsable_payload,
        payload=payload,
        normalizar_sexo=normalizar_sexo,
    )
    _enriquecer_responsable_payload_importacion(
        responsable_payload=responsable_payload,
        payload=payload,
        provincia_usuario_id=provincia_usuario_id,
        offset=offset,
        add_warning=add_warning,
        to_date=to_date,
    )
    _validar_contacto_payload_importacion(
        payload=responsable_payload,
        offset=offset,
        add_warning=add_warning,
        email_label="email_responsable",
        telefono_label="telefono_responsable",
    )
    _emitir_warnings_edad_responsable_importacion(
        responsable_payload=responsable_payload,
        payload_beneficiario=payload,
        offset=offset,
        add_warning=add_warning,
        validar_edad_responsable_fn=validar_edad_responsable_fn,
    )
    return responsable_payload, _es_mismo_documento_responsable_importacion(payload)


def validar_y_normalizar_payloads_importacion(
    *,
    payload,
    provincia_usuario_id,
    offset=0,
    municipios_cache=None,
    localidades_cache=None,
    normalizar_sexo=None,
    to_date=None,
    add_warning=None,
    add_error=None,
):
    payload_normalizado = dict(payload)
    add_warning = add_warning or (lambda *_args, **_kwargs: None)
    add_error = add_error or (lambda *_args, **_kwargs: None)

    if normalizar_sexo is None:
        normalizar_sexo = _build_normalizar_sexo_importacion(_cargar_sexos_cache())
    if to_date is None:
        from celiaquia.services.ciudadano_service import CiudadanoService

        to_date = CiudadanoService._to_date
    if municipios_cache is None or localidades_cache is None:
        municipios_cache, localidades_cache = _build_lookup_caches_payload_importacion(
            payload_normalizado, provincia_usuario_id
        )

    _aplicar_defaults_y_validar_payload_importacion(
        payload_normalizado, provincia_usuario_id
    )
    _normalizar_enriquecer_payload_importacion(
        payload=payload_normalizado,
        offset=offset,
        add_warning=add_warning,
        to_date=to_date,
        municipios_cache=municipios_cache,
        localidades_cache=localidades_cache,
        normalizar_sexo=normalizar_sexo,
    )

    responsable_payload = None
    es_mismo_documento_resp = False
    if _tiene_datos_responsable_importacion(payload_normalizado):
        (
            responsable_payload,
            es_mismo_documento_resp,
        ) = _validar_y_normalizar_responsable_payload_importacion(
            payload=payload_normalizado,
            provincia_usuario_id=provincia_usuario_id,
            offset=offset,
            normalizar_sexo=normalizar_sexo,
            to_date=to_date,
            add_warning=add_warning,
            add_error=add_error,
            validar_edad_responsable_fn=validar_edad_responsable,
        )

    return payload_normalizado, responsable_payload, es_mismo_documento_resp


def _agregar_sexo_responsable_payload_importacion(
    responsable_payload, payload, normalizar_sexo
):
    sexo_resp_val = payload.get("sexo_responsable")
    if not sexo_resp_val:
        return

    sexo_resp_str = str(sexo_resp_val).strip()
    if sexo_resp_str.isdigit() and Sexo.objects.filter(pk=int(sexo_resp_str)).exists():
        responsable_payload["sexo"] = int(sexo_resp_str)
        return

    sexo_resp_id = normalizar_sexo(sexo_resp_val)
    if not sexo_resp_id:
        raise ValidationError(
            "Sexo responsable invalido. Use M/F, Masculino/Femenino, etc."
        )
    responsable_payload["sexo"] = sexo_resp_id


def _es_mismo_documento_responsable_importacion(payload):
    doc_responsable = payload.get("documento_responsable")
    if not doc_responsable:
        return False

    return str(doc_responsable).strip() == str(payload.get("documento", "")).strip()


def _enriquecer_responsable_payload_importacion(
    responsable_payload,
    payload,
    provincia_usuario_id,
    offset,
    add_warning,
    to_date,
):
    _aplicar_domicilio_responsable_payload_importacion(responsable_payload, payload)
    _resolver_localidad_responsable_payload_importacion(
        responsable_payload=responsable_payload,
        payload=payload,
        provincia_usuario_id=provincia_usuario_id,
        offset=offset,
        add_warning=add_warning,
    )
    _convertir_fecha_nacimiento_responsable_payload_importacion(
        responsable_payload=responsable_payload,
        offset=offset,
        add_warning=add_warning,
        to_date=to_date,
    )


def _aplicar_domicilio_responsable_payload_importacion(responsable_payload, payload):
    domicilio_resp = payload.get("domicilio_responsable", "")
    if domicilio_resp:
        match = re.match(r"^(.+?)\s+(\d+)\s*$", domicilio_resp.strip())
        if match:
            responsable_payload["calle"] = match.group(1).strip()
            responsable_payload["altura"] = match.group(2)
        else:
            responsable_payload["calle"] = domicilio_resp


def _resolver_localidad_responsable_payload_importacion(
    *, responsable_payload, payload, provincia_usuario_id, offset, add_warning
):
    localidad_resp = payload.get("localidad_responsable")
    if localidad_resp:
        try:
            localidad_resp_str = str(localidad_resp).strip()
            localidades_qs = Localidad.objects.select_related("municipio").filter(
                municipio__provincia_id=provincia_usuario_id
            )
            if localidad_resp_str.isdigit():
                coincidencias = list(
                    localidades_qs.filter(pk=int(localidad_resp_str))[:2]
                )
            else:
                coincidencias = list(
                    localidades_qs.filter(nombre__iexact=localidad_resp_str)[:2]
                )

            if len(coincidencias) == 1:
                localidad_obj = coincidencias[0]
                responsable_payload["localidad"] = localidad_obj.pk
                responsable_payload["municipio"] = localidad_obj.municipio.pk
                return
            if len(coincidencias) > 1:
                raise ValidationError(
                    f"Localidad responsable ambigua: {localidad_resp}"
                )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            raise ValidationError(
                f"Localidad responsable invalida: {localidad_resp}"
            ) from exc

        raise ValidationError(f"Localidad responsable invalida: {localidad_resp}")


def _convertir_fecha_nacimiento_responsable_payload_importacion(
    *, responsable_payload, offset, add_warning, to_date
):
    if responsable_payload.get("fecha_nacimiento"):
        try:
            responsable_payload["fecha_nacimiento"] = to_date(
                responsable_payload["fecha_nacimiento"]
            )
        except ValidationError as exc:
            raise ValidationError(
                "Fecha de nacimiento responsable inválida: "
                f"{responsable_payload.get('fecha_nacimiento')}"
            ) from exc


def _crear_responsable_y_legajo_importacion(
    responsable_payload,
    payload_beneficiario,
    usuario,
    expediente,
    estado_id,
    existentes_ids,
    legajos_crear,
    offset,
    add_warning,
    validar_edad_responsable_fn,
    get_or_create_ciudadano,
):
    del payload_beneficiario, offset, add_warning, validar_edad_responsable_fn
    ciudadano_responsable = get_or_create_ciudadano(
        datos=responsable_payload,
        usuario=usuario,
        expediente=expediente,
    )

    if not (ciudadano_responsable and ciudadano_responsable.pk):
        return None, False

    cid_resp = ciudadano_responsable.pk

    legajo_agregado = _registrar_legajo_responsable_importacion_si_corresponde(
        cid_resp=cid_resp,
        ciudadano_responsable=ciudadano_responsable,
        expediente=expediente,
        estado_id=estado_id,
        existentes_ids=existentes_ids,
        legajos_crear=legajos_crear,
    )

    return cid_resp, legajo_agregado


def _emitir_warnings_edad_responsable_importacion(
    *,
    responsable_payload,
    payload_beneficiario,
    offset,
    add_warning,
    validar_edad_responsable_fn,
):
    _valido_edad, edad_warnings, error_edad = validar_edad_responsable_fn(
        responsable_payload.get("fecha_nacimiento"),
        payload_beneficiario.get("fecha_nacimiento"),
    )
    for warning in edad_warnings:
        add_warning(offset, "edad", warning)
    if error_edad:
        raise ValidationError(error_edad)


def _registrar_legajo_responsable_importacion_si_corresponde(
    *,
    cid_resp,
    ciudadano_responsable,
    expediente,
    estado_id,
    existentes_ids,
    legajos_crear,
):
    if cid_resp in existentes_ids:
        return False

    legajos_crear.append(
        ExpedienteCiudadano(
            expediente=expediente,
            ciudadano=ciudadano_responsable,
            estado_id=estado_id,
            rol=ExpedienteCiudadano.ROLE_RESPONSABLE,
        )
    )
    existentes_ids.add(cid_resp)
    return True


def _registrar_relacion_familiar_importacion(
    cid_resp,
    cid_beneficiario,
    offset,
    relaciones_familiares_pairs,
    relaciones_familiares,
):
    pair = (cid_resp, cid_beneficiario)
    if pair in relaciones_familiares_pairs:
        return False

    relaciones_familiares_pairs.add(pair)
    relaciones_familiares.append(
        {
            "hijo_id": cid_beneficiario,
            "responsable_id": cid_resp,
            "fila": offset,
        }
    )
    return True


def _agregar_exclusion_beneficiario_importacion(
    excluidos,
    offset,
    ciudadano,
    ciudadano_id,
    motivo,
    **extra_fields,
):
    excluidos.append(
        {
            "fila": offset,
            "ciudadano_id": ciudadano_id,
            "documento": getattr(ciudadano, "documento", ""),
            "nombre": getattr(ciudadano, "nombre", ""),
            "apellido": getattr(ciudadano, "apellido", ""),
            "motivo": motivo,
            **extra_fields,
        }
    )


def _agregar_exclusion_beneficiario_existente_importacion(
    *, excluidos, offset, ciudadano, ciudadano_id
):
    _agregar_exclusion_beneficiario_importacion(
        excluidos=excluidos,
        offset=offset,
        ciudadano=ciudadano,
        ciudadano_id=ciudadano_id,
        motivo="Ya existe en este expediente",
    )


def _agregar_exclusion_beneficiario_en_programa_importacion(
    *, excluidos, offset, ciudadano, ciudadano_id, programa_data
):
    estado_text = "ACEPTADO" if programa_data["es_titular_activo"] else "SUSPENDIDO"
    _agregar_exclusion_beneficiario_importacion(
        excluidos=excluidos,
        offset=offset,
        ciudadano=ciudadano,
        ciudadano_id=ciudadano_id,
        motivo="Ya está dentro del programa en otro expediente",
        expediente_origen_id=programa_data["expediente_id"],
        estado_programa=estado_text,
    )


def _agregar_exclusion_beneficiario_expediente_abierto_importacion(
    *, excluidos, offset, ciudadano, ciudadano_id, conflicto_data
):
    _agregar_exclusion_beneficiario_importacion(
        excluidos=excluidos,
        offset=offset,
        ciudadano=ciudadano,
        ciudadano_id=ciudadano_id,
        motivo="Duplicado en otro expediente abierto",
        expediente_origen_id=conflicto_data["expediente_id"],
        estado_expediente_origen=conflicto_data["expediente__estado__nombre"],
    )


def _beneficiario_tiene_conflicto_importacion(
    ciudadano,
    offset,
    existentes_ids,
    en_programa,
    abiertos,
    excluidos,
):
    cid = ciudadano.pk

    if cid in existentes_ids:
        _agregar_exclusion_beneficiario_existente_importacion(
            excluidos=excluidos,
            offset=offset,
            ciudadano=ciudadano,
            ciudadano_id=cid,
        )
        return True

    if cid in en_programa:
        _agregar_exclusion_beneficiario_en_programa_importacion(
            excluidos=excluidos,
            offset=offset,
            ciudadano=ciudadano,
            ciudadano_id=cid,
            programa_data=en_programa[cid],
        )
        return True

    if cid in abiertos:
        _agregar_exclusion_beneficiario_expediente_abierto_importacion(
            excluidos=excluidos,
            offset=offset,
            ciudadano=ciudadano,
            ciudadano_id=cid,
            conflicto_data=abiertos[cid],
        )
        return True

    return False


def _registrar_legajo_beneficiario_importacion(
    ciudadano,
    expediente,
    estado_id,
    existentes_ids,
    abiertos,
    legajos_crear,
    es_mismo_documento_resp=False,
):
    cid = ciudadano.pk
    # Si el beneficiario es también responsable, asignar rol doble
    rol = (
        ExpedienteCiudadano.ROLE_BENEFICIARIO_Y_RESPONSABLE
        if es_mismo_documento_resp
        else ExpedienteCiudadano.ROLE_BENEFICIARIO
    )
    legajos_crear.append(
        ExpedienteCiudadano(
            expediente=expediente,
            ciudadano=ciudadano,
            estado_id=estado_id,
            rol=rol,
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
    return cid


def _crear_ciudadano_beneficiario_importacion(
    payload,
    usuario,
    expediente,
    offset,
    detalles_errores,
    get_or_create_ciudadano,
):
    try:
        ciudadano = get_or_create_ciudadano(
            datos=payload,
            usuario=usuario,
            expediente=expediente,
        )
        if ciudadano and ciudadano.pk:
            return ciudadano

        _registrar_error_creacion_ciudadano_importacion(
            payload=payload,
            offset=offset,
            detalles_errores=detalles_errores,
            error="No se pudo crear el ciudadano",
        )
        return None
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.error("Error creando ciudadano en fila %s: %s", offset, exc)
        _registrar_error_creacion_ciudadano_importacion(
            payload=payload,
            offset=offset,
            detalles_errores=detalles_errores,
            error=f"Error creando ciudadano: {str(exc)}",
        )
        return None


def _resolver_cid_responsable_importacion(
    *,
    payload,
    responsable_payload,
    cid_beneficiario,
    usuario,
    expediente,
    estado_id,
    provincia_usuario_id,
    offset,
    normalizar_sexo,
    to_date,
    add_warning,
    validar_edad_responsable_fn,
    existentes_ids,
    legajos_crear,
    get_or_create_ciudadano,
):
    del provincia_usuario_id, normalizar_sexo, to_date
    es_mismo_documento_resp = _es_mismo_documento_responsable_importacion(payload)

    if es_mismo_documento_resp:
        add_warning(
            offset,
            "responsable",
            "Responsable es el mismo beneficiario - no se duplica legajo",
        )
        return cid_beneficiario, True, False

    cid_resp, legajo_agregado = _crear_responsable_y_legajo_importacion(
        responsable_payload=responsable_payload,
        payload_beneficiario=payload,
        usuario=usuario,
        expediente=expediente,
        estado_id=estado_id,
        existentes_ids=existentes_ids,
        legajos_crear=legajos_crear,
        offset=offset,
        add_warning=add_warning,
        validar_edad_responsable_fn=validar_edad_responsable_fn,
        get_or_create_ciudadano=get_or_create_ciudadano,
    )
    return cid_resp, False, legajo_agregado


def _vincular_responsable_a_beneficiario_importacion_si_corresponde(
    *,
    cid_resp,
    es_mismo_documento_resp,
    cid_beneficiario,
    offset,
    relaciones_familiares_pairs,
    relaciones_familiares,
):
    if es_mismo_documento_resp or not cid_resp:
        return False

    return _registrar_relacion_familiar_importacion(
        cid_resp=cid_resp,
        cid_beneficiario=cid_beneficiario,
        offset=offset,
        relaciones_familiares_pairs=relaciones_familiares_pairs,
        relaciones_familiares=relaciones_familiares,
    )


def _procesar_responsable_importacion(
    payload,
    cid_beneficiario,
    usuario,
    expediente,
    estado_id,
    provincia_usuario_id,
    offset,
    normalizar_sexo,
    to_date,
    add_warning,
    add_error,
    validar_edad_responsable_fn,
    existentes_ids,
    legajos_crear,
    relaciones_familiares_pairs,
    relaciones_familiares,
    get_or_create_ciudadano,
    responsable_payload=None,
):
    if responsable_payload is None:
        responsable_payload, _es_mismo_documento_resp = (
            _validar_y_normalizar_responsable_payload_importacion(
                payload=payload,
                provincia_usuario_id=provincia_usuario_id,
                offset=offset,
                normalizar_sexo=normalizar_sexo,
                to_date=to_date,
                add_warning=add_warning,
                add_error=add_error,
                validar_edad_responsable_fn=validar_edad_responsable_fn,
            )
        )

    cid_resp, es_mismo_documento_resp, legajo_agregado = (
        _resolver_cid_responsable_importacion(
            payload=payload,
            responsable_payload=responsable_payload,
            cid_beneficiario=cid_beneficiario,
            usuario=usuario,
            expediente=expediente,
            estado_id=estado_id,
            provincia_usuario_id=provincia_usuario_id,
            offset=offset,
            normalizar_sexo=normalizar_sexo,
            to_date=to_date,
            add_warning=add_warning,
            validar_edad_responsable_fn=validar_edad_responsable_fn,
            existentes_ids=existentes_ids,
            legajos_crear=legajos_crear,
            get_or_create_ciudadano=get_or_create_ciudadano,
        )
    )

    relacion_agregada = _vincular_responsable_a_beneficiario_importacion_si_corresponde(
        cid_resp=cid_resp,
        es_mismo_documento_resp=es_mismo_documento_resp,
        cid_beneficiario=cid_beneficiario,
        offset=offset,
        relaciones_familiares_pairs=relaciones_familiares_pairs,
        relaciones_familiares=relaciones_familiares,
    )
    return cid_resp, legajo_agregado, relacion_agregada


def _construir_payload_fila_importacion(
    row,
    offset,
    numeric_fields,
    provincia_usuario_id,
    validar_documento,
    add_warning,
    to_date,
    municipios_cache,
    localidades_cache,
    normalizar_sexo,
):
    payload = _build_payload_importacion_from_row(
        row=row,
        numeric_fields=numeric_fields,
        offset=offset,
        validar_documento=validar_documento,
        add_warning=add_warning,
    )
    _aplicar_defaults_y_validar_payload_importacion(
        payload=payload,
        provincia_usuario_id=provincia_usuario_id,
    )
    _normalizar_enriquecer_payload_importacion(
        payload=payload,
        offset=offset,
        add_warning=add_warning,
        to_date=to_date,
        municipios_cache=municipios_cache,
        localidades_cache=localidades_cache,
        normalizar_sexo=normalizar_sexo,
    )
    return payload


def _procesar_beneficiario_importacion(
    payload,
    usuario,
    expediente,
    estado_id,
    offset,
    detalles_errores,
    existentes_ids,
    en_programa,
    abiertos,
    excluidos,
    legajos_crear,
    get_or_create_ciudadano,
    es_mismo_documento_resp=False,
):
    ciudadano = _crear_ciudadano_beneficiario_importacion(
        payload=payload,
        usuario=usuario,
        expediente=expediente,
        offset=offset,
        detalles_errores=detalles_errores,
        get_or_create_ciudadano=get_or_create_ciudadano,
    )
    if not ciudadano:
        return "error", None

    if _beneficiario_tiene_conflicto_importacion(
        ciudadano=ciudadano,
        offset=offset,
        existentes_ids=existentes_ids,
        en_programa=en_programa,
        abiertos=abiertos,
        excluidos=excluidos,
    ):
        return "excluido", None

    cid = _registrar_legajo_beneficiario_importacion(
        ciudadano=ciudadano,
        expediente=expediente,
        estado_id=estado_id,
        existentes_ids=existentes_ids,
        abiertos=abiertos,
        legajos_crear=legajos_crear,
        es_mismo_documento_resp=es_mismo_documento_resp,
    )
    return "ok", cid


def _tiene_datos_responsable_importacion(payload):
    return any(
        [
            payload.get("apellido_responsable"),
            payload.get("nombre_responsable"),
            payload.get("fecha_nacimiento_responsable"),
        ]
    )


IMPORTACION_NUMERIC_FIELDS = {
    "documento",
    "altura",
    "telefono",
    "telefono_alternativo",
    "documento_responsable",
    "telefono_responsable",
    "contacto_responsable",
}


def _leer_bytes_archivo_importacion(archivo_excel):
    try:
        archivo_excel.open()
    except Exception:
        pass
    archivo_excel.seek(0)
    return archivo_excel.read()


def _expediente_id(expediente):
    if expediente is None:
        return None
    for attr in ("pk", "id"):
        value = getattr(expediente, attr, None)
        if value is not None:
            return value
    return expediente


def _precargar_conflictos_y_existentes_importacion(expediente):
    # Usar all_objects para incluir legajos soft-deleted: si un ciudadano fue eliminado
    # lógicamente de este expediente, su fila aún existe en BD y el unique_together
    # bloquearía un bulk_create duplicado.
    expediente_id = _expediente_id(expediente)
    existentes_ids = set(
        ExpedienteCiudadano.all_objects.filter(expediente_id=expediente_id).values_list(
            "ciudadano_id", flat=True
        )
    )

    conflictos_qs = (
        ExpedienteCiudadano.objects.select_related("expediente", "expediente__estado")
        .exclude(expediente_id=expediente_id)
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

    return existentes_ids, en_programa, abiertos


def _build_callbacks_importacion(warnings):
    def add_warning(fila, campo, detalle):
        warnings.append({"fila": fila, "campo": campo, "detalle": detalle})
        logger.warning("Fila %s: %s (%s)", fila, detalle, campo)

    def add_error(fila, campo, detalle):
        raise ValidationError(f"Fila {fila}: {detalle} ({campo})")

    return add_warning, add_error


def _validar_documento_importacion(doc_str, campo_nombre, _fila):
    """Valida formato y longitud de documento."""
    if not doc_str or not doc_str.isdigit():
        raise ValidationError(f"{campo_nombre} debe contener solo dígitos")

    doc_len = len(doc_str)

    if campo_nombre == "documento":
        if doc_len in (10, 11):
            return doc_str
        raise ValidationError(f"{campo_nombre} debe tener entre 10 y 11 dígitos")

    if (
        "responsable" in campo_nombre
        and "telefono" not in campo_nombre
        and "contacto" not in campo_nombre
    ):
        if doc_len in (10, 11):
            return doc_str
        raise ValidationError(f"{campo_nombre} debe tener entre 10 y 11 dígitos")

    return doc_str


def _build_normalizar_sexo_importacion(sexos_cache):
    def normalizar_sexo(sexo_valor):
        if not sexo_valor:
            return None
        sexo_lower = str(sexo_valor).strip().lower()
        return sexos_cache.get(sexo_lower)

    return normalizar_sexo


def _registrar_error_fila_importacion(detalles_errores, row, offset, exc):
    error_msg = str(exc)
    datos_originales = _build_datos_originales_error_importacion(row)
    _append_detalle_error_importacion(
        detalles_errores=detalles_errores,
        fila=offset,
        error=error_msg,
        datos=datos_originales,
    )
    logger.error("Error fila %s: %s", offset, exc)


def _procesar_beneficiario_desde_row_importacion(
    *,
    row,
    offset,
    usuario,
    expediente,
    estado_id,
    provincia_usuario_id,
    municipios_cache,
    localidades_cache,
    validar_documento,
    add_warning,
    add_error,
    normalizar_sexo,
    to_date,
    get_or_create_ciudadano,
    detalles_errores,
    existentes_ids,
    en_programa,
    abiertos,
    excluidos,
    legajos_crear,
    doble_rol_docs,
):
    payload = _construir_payload_fila_importacion(
        row=row,
        offset=offset,
        numeric_fields=IMPORTACION_NUMERIC_FIELDS,
        provincia_usuario_id=provincia_usuario_id,
        validar_documento=validar_documento,
        add_warning=add_warning,
        to_date=to_date,
        municipios_cache=municipios_cache,
        localidades_cache=localidades_cache,
        normalizar_sexo=normalizar_sexo,
    )

    responsable_payload = None
    es_mismo_documento_resp = False
    if _tiene_datos_responsable_importacion(payload):
        (
            responsable_payload,
            es_mismo_documento_resp,
        ) = _validar_y_normalizar_responsable_payload_importacion(
            payload=payload,
            provincia_usuario_id=provincia_usuario_id,
            offset=offset,
            normalizar_sexo=normalizar_sexo,
            to_date=to_date,
            add_warning=add_warning,
            add_error=add_error,
            validar_edad_responsable_fn=validar_edad_responsable,
        )

    # Detectar doble rol: mismo documento O documento en lista de doble rol
    doc_beneficiario = str(payload.get("documento", "")).strip()
    es_doble_rol = es_mismo_documento_resp or (doc_beneficiario in doble_rol_docs)

    if es_doble_rol:
        add_warning(
            offset,
            "doble_rol",
            f"Beneficiario con doble rol detectado (doc: {doc_beneficiario})",
        )

    resultado_beneficiario, cid = _procesar_beneficiario_importacion(
        payload=payload,
        usuario=usuario,
        expediente=expediente,
        estado_id=estado_id,
        offset=offset,
        detalles_errores=detalles_errores,
        existentes_ids=existentes_ids,
        en_programa=en_programa,
        abiertos=abiertos,
        excluidos=excluidos,
        legajos_crear=legajos_crear,
        get_or_create_ciudadano=get_or_create_ciudadano,
        es_mismo_documento_resp=es_doble_rol,
    )
    return (
        payload,
        responsable_payload,
        es_mismo_documento_resp,
        resultado_beneficiario,
        cid,
    )


def _procesar_responsable_si_corresponde_importacion(
    *,
    payload,
    cid_beneficiario,
    usuario,
    expediente,
    estado_id,
    provincia_usuario_id,
    offset,
    normalizar_sexo,
    to_date,
    add_warning,
    add_error,
    get_or_create_ciudadano,
    existentes_ids,
    legajos_crear,
    relaciones_familiares_pairs,
    relaciones_familiares,
    responsable_payload=None,
):
    if responsable_payload is None and not _tiene_datos_responsable_importacion(
        payload
    ):
        return None, False, False

    return _procesar_responsable_importacion(
        payload=payload,
        cid_beneficiario=cid_beneficiario,
        usuario=usuario,
        expediente=expediente,
        estado_id=estado_id,
        provincia_usuario_id=provincia_usuario_id,
        offset=offset,
        normalizar_sexo=normalizar_sexo,
        to_date=to_date,
        add_warning=add_warning,
        add_error=add_error,
        validar_edad_responsable_fn=validar_edad_responsable,
        existentes_ids=existentes_ids,
        legajos_crear=legajos_crear,
        relaciones_familiares_pairs=relaciones_familiares_pairs,
        relaciones_familiares=relaciones_familiares,
        get_or_create_ciudadano=get_or_create_ciudadano,
        responsable_payload=responsable_payload,
    )


def _procesar_fila_legajo_importacion(
    *,
    row,
    offset,
    usuario,
    expediente,
    estado_id,
    provincia_usuario_id,
    municipios_cache,
    localidades_cache,
    validar_documento,
    add_warning,
    add_error,
    normalizar_sexo,
    to_date,
    get_or_create_ciudadano,
    detalles_errores,
    existentes_ids,
    en_programa,
    abiertos,
    excluidos,
    legajos_crear,
    relaciones_familiares_pairs,
    relaciones_familiares,
    doble_rol_docs,
    warnings,
):
    cid = None
    cid_resp = None
    legajo_responsable_agregado = False
    relacion_agregada = False
    warnings_len = len(warnings)
    legajos_len = len(legajos_crear)
    relaciones_len = len(relaciones_familiares)

    try:
        with transaction.atomic():
            (
                payload,
                responsable_payload,
                es_mismo_documento_resp,
                resultado_beneficiario,
                cid,
            ) = _procesar_beneficiario_desde_row_importacion(
                row=row,
                offset=offset,
                usuario=usuario,
                expediente=expediente,
                estado_id=estado_id,
                provincia_usuario_id=provincia_usuario_id,
                municipios_cache=municipios_cache,
                localidades_cache=localidades_cache,
                validar_documento=validar_documento,
                add_warning=add_warning,
                add_error=add_error,
                normalizar_sexo=normalizar_sexo,
                to_date=to_date,
                get_or_create_ciudadano=get_or_create_ciudadano,
                detalles_errores=detalles_errores,
                existentes_ids=existentes_ids,
                en_programa=en_programa,
                abiertos=abiertos,
                excluidos=excluidos,
                legajos_crear=legajos_crear,
                doble_rol_docs=doble_rol_docs,
            )
            if resultado_beneficiario == "error":
                del warnings[warnings_len:]
                return 0, 1
            if resultado_beneficiario == "excluido":
                return 0, 0

            (
                cid_resp,
                legajo_responsable_agregado,
                relacion_agregada,
            ) = _procesar_responsable_si_corresponde_importacion(
                payload=payload,
                cid_beneficiario=cid,
                usuario=usuario,
                expediente=expediente,
                estado_id=estado_id,
                provincia_usuario_id=provincia_usuario_id,
                offset=offset,
                normalizar_sexo=normalizar_sexo,
                to_date=to_date,
                add_warning=add_warning,
                add_error=add_error,
                get_or_create_ciudadano=get_or_create_ciudadano,
                existentes_ids=existentes_ids,
                legajos_crear=legajos_crear,
                relaciones_familiares_pairs=relaciones_familiares_pairs,
                relaciones_familiares=relaciones_familiares,
                responsable_payload=responsable_payload,
            )

        return 1, 0
    except Exception as exc:  # pylint: disable=broad-exception-caught
        del warnings[warnings_len:]
        del legajos_crear[legajos_len:]
        del relaciones_familiares[relaciones_len:]
        if relacion_agregada and cid_resp and cid:
            relaciones_familiares_pairs.discard((cid_resp, cid))
        if legajo_responsable_agregado and cid_resp:
            existentes_ids.discard(cid_resp)
        if cid:
            existentes_ids.discard(cid)
            abiertos.pop(cid, None)
        _registrar_error_fila_importacion(detalles_errores, row, offset, exc)
        return 0, 1


def _identificar_documentos_con_doble_rol(df):  # pylint: disable=invalid-name
    """Identifica qué documentos de beneficiarios también son responsables de otros."""
    documentos_beneficiarios = set()
    documentos_responsables = set()

    for _, row in df.iterrows():
        doc_benef = str(row.get("documento", "")).strip()
        doc_resp = str(row.get("documento_responsable", "")).strip()

        if doc_benef and doc_benef not in ("", "nan", "None"):
            documentos_beneficiarios.add(doc_benef)

        if doc_resp and doc_resp not in ("", "nan", "None"):
            documentos_responsables.add(doc_resp)

    # Documentos que son tanto beneficiarios como responsables
    doble_rol_docs = documentos_beneficiarios & documentos_responsables
    logger.info("Documentos con doble rol detectados: %s", doble_rol_docs)
    return doble_rol_docs


def _build_contexto_filas_importacion_legajos(
    *,
    df,
    usuario,
    expediente,
    warnings,
    detalles_errores,
    excluidos,
    legajos_crear,
    relaciones_familiares_pairs,
    relaciones_familiares,
):
    estado_id = _estado_doc_pendiente_id()
    provincia_usuario_id = _obtener_provincia_usuario_id(usuario)
    existentes_ids, en_programa, abiertos = (
        _precargar_conflictos_y_existentes_importacion(expediente)
    )
    add_warning, add_error = _build_callbacks_importacion(warnings)

    precargas = _precargar_datos_importacion(df, provincia_usuario_id)
    sexos_cache = precargas["sexos_cache"]
    normalizar_sexo = _build_normalizar_sexo_importacion(sexos_cache)

    # Identificar documentos con doble rol
    doble_rol_docs = _identificar_documentos_con_doble_rol(df)

    from celiaquia.services.ciudadano_service import CiudadanoService

    return {
        "usuario": usuario,
        "expediente": expediente,
        "estado_id": estado_id,
        "provincia_usuario_id": provincia_usuario_id,
        "municipios_cache": precargas["municipios_cache"],
        "localidades_cache": precargas["localidades_cache"],
        "validar_documento": _validar_documento_importacion,
        "add_warning": add_warning,
        "add_error": add_error,
        "normalizar_sexo": normalizar_sexo,
        "to_date": CiudadanoService._to_date,
        "get_or_create_ciudadano": CiudadanoService.get_or_create_ciudadano,
        "detalles_errores": detalles_errores,
        "existentes_ids": existentes_ids,
        "en_programa": en_programa,
        "abiertos": abiertos,
        "excluidos": excluidos,
        "legajos_crear": legajos_crear,
        "relaciones_familiares_pairs": relaciones_familiares_pairs,
        "relaciones_familiares": relaciones_familiares,
        "doble_rol_docs": doble_rol_docs,
        "warnings": warnings,
    }


def _procesar_dataframe_importacion_legajos(df, contexto_filas):
    validos = 0
    errores = 0
    for offset, row in enumerate(df.to_dict(orient="records"), start=2):
        inc_validos, inc_errores = _procesar_fila_legajo_importacion(
            row=row,
            offset=offset,
            **contexto_filas,
        )
        validos += inc_validos
        errores += inc_errores
    return validos, errores


def _inicializar_buffers_importacion_legajos():
    return {
        "detalles_errores": [],
        "excluidos": [],
        "warnings": [],
        "legajos_crear": [],
        "relaciones_familiares": [],
        "relaciones_familiares_pairs": set(),
    }


def _postprocesar_importacion_legajos(
    *,
    expediente,
    batch_size,
    legajos_crear,
    relaciones_familiares,
    detalles_errores,
    warnings,
):
    _persistir_legajos_importacion(
        legajos_crear=legajos_crear,
        batch_size=batch_size,
        relaciones_familiares=relaciones_familiares,
        warnings=warnings,
    )
    _guardar_registros_erroneos_importacion(
        expediente=expediente,
        detalles_errores=detalles_errores,
        batch_size=batch_size,
    )
    return _consolidar_roles_cruzados_importacion(
        expediente=expediente,
        warnings=warnings,
    )


def _finalizar_importacion_legajos(
    *,
    expediente,
    batch_size,
    legajos_crear,
    relaciones_familiares,
    detalles_errores,
    warnings,
    errores,
    excluidos,
):
    relaciones_cruzadas_creadas = _postprocesar_importacion_legajos(
        expediente=expediente,
        batch_size=batch_size,
        legajos_crear=legajos_crear,
        relaciones_familiares=relaciones_familiares,
        detalles_errores=detalles_errores,
        warnings=warnings,
    )

    logger.info(
        "Import completo: %s legajos creados, %s errores, %s excluidos, %s relaciones cruzadas.",
        len(legajos_crear),
        errores,
        len(excluidos),
        relaciones_cruzadas_creadas,
    )

    return _build_resultado_importacion(
        legajos_crear=legajos_crear,
        errores=errores,
        detalles_errores=detalles_errores,
        excluidos=excluidos,
        warnings=warnings,
        relaciones_familiares=relaciones_familiares,
        relaciones_cruzadas_creadas=relaciones_cruzadas_creadas,
    )


def _build_resultado_importacion(
    *,
    legajos_crear,
    errores,
    detalles_errores,
    excluidos,
    warnings,
    relaciones_familiares,
    relaciones_cruzadas_creadas,
):
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
            "SEXO_RESPONSABLE",
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
        data = _leer_bytes_archivo_importacion(archivo_excel)
        df = _leer_excel_importacion(data)
        df = _normalizar_dataframe_importacion(df)

        try:
            with transaction.atomic():
                buffers = _inicializar_buffers_importacion_legajos()
                detalles_errores = buffers["detalles_errores"]
                excluidos = buffers["excluidos"]
                warnings = buffers["warnings"]
                legajos_crear = buffers["legajos_crear"]
                relaciones_familiares = buffers["relaciones_familiares"]  # padre-hijo
                relaciones_familiares_pairs = buffers["relaciones_familiares_pairs"]
                contexto_filas = _build_contexto_filas_importacion_legajos(
                    df=df,
                    usuario=usuario,
                    expediente=expediente,
                    warnings=warnings,
                    detalles_errores=detalles_errores,
                    excluidos=excluidos,
                    legajos_crear=legajos_crear,
                    relaciones_familiares_pairs=relaciones_familiares_pairs,
                    relaciones_familiares=relaciones_familiares,
                )
                _, errores = _procesar_dataframe_importacion_legajos(df, contexto_filas)

                return _finalizar_importacion_legajos(
                    expediente=expediente,
                    batch_size=batch_size,
                    legajos_crear=legajos_crear,
                    excluidos=excluidos,
                    relaciones_familiares=relaciones_familiares,
                    detalles_errores=detalles_errores,
                    warnings=warnings,
                    errores=errores,
                )
        except Exception as exc:
            # transaction.atomic() revierte automáticamente todos los cambios
            logger.exception(
                "Error durante importación de legajos desde Excel. Cambios revertidos.",
                extra={"expediente_id": expediente.id, "archivo": archivo_excel.name},
            )
            raise
