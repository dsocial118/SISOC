"""Contrato Python público para resolver ciudadanos desde RENAPER."""

from __future__ import annotations

import logging
import unicodedata
from datetime import date, datetime
from typing import Any

from django.db import IntegrityError

from ciudadanos.models import Ciudadano
from core.models import Localidad, Municipio, Nacionalidad, Provincia
from core.services.renaper import consultar_datos_renaper


logger = logging.getLogger("django")

_GEO_ALIASES = {
    "ciudad de buenos aires": "ciudad autonoma de buenos aires",
    "ciudad autonoma de buenos aires": "ciudad autonoma de buenos aires",
    "caba": "ciudad autonoma de buenos aires",
    "capital federal": "ciudad autonoma de buenos aires",
}
_NUMEROS_INICIALES = {
    "uno": "1",
    "una": "1",
    "dos": "2",
    "tres": "3",
    "cuatro": "4",
    "cinco": "5",
    "seis": "6",
    "siete": "7",
    "ocho": "8",
    "nueve": "9",
    "diez": "10",
    "once": "11",
    "doce": "12",
    "trece": "13",
    "catorce": "14",
    "quince": "15",
    "dieciseis": "16",
    "diecisiete": "17",
    "dieciocho": "18",
    "diecinueve": "19",
    "veinte": "20",
    "veintiuno": "21",
    "veintidos": "22",
    "veintitres": "23",
    "veinticuatro": "24",
    "veinticinco": "25",
    "veintiseis": "26",
    "veintisiete": "27",
    "veintiocho": "28",
    "veintinueve": "29",
    "treinta": "30",
}


def _normalizar(valor: object) -> str:
    if not valor:
        return ""
    texto = str(valor).replace("_", " ").replace("-", " ").lower()
    texto = " ".join(texto.split())
    texto = _GEO_ALIASES.get(texto, texto)
    texto = " ".join(
        unicodedata.normalize("NFKD", texto)
        .encode("ascii", "ignore")
        .decode("utf-8")
        .split()
    )
    partes = texto.split()
    if partes and partes[0] in _NUMEROS_INICIALES:
        partes[0] = _NUMEROS_INICIALES[partes[0]]
    return " ".join(partes)


def _buscar_por_nombre(queryset, valor: object):
    objetivo = _normalizar(valor)
    if not objetivo:
        return None
    return next(
        (
            item
            for item in queryset
            if _normalizar(getattr(item, "nombre", "")) == objetivo
        ),
        None,
    )


def _resolver_ubicacion(datos: dict[str, Any]) -> dict[str, object | None]:
    provincia = _buscar_por_nombre(Provincia.objects.all(), datos.get("provincia_api"))
    municipios = Municipio.objects.all()
    if provincia:
        municipios = municipios.filter(provincia=provincia)
    municipio = _buscar_por_nombre(municipios, datos.get("municipio_api"))
    localidades = Localidad.objects.all()
    if municipio:
        localidades = localidades.filter(municipio=municipio)
    elif provincia:
        localidades = localidades.filter(municipio__provincia=provincia)
    return {
        "provincia": provincia,
        "municipio": municipio,
        "localidad": _buscar_por_nombre(localidades, datos.get("localidad_api")),
    }


def _resolver_nacionalidad(nombre: object):
    objetivo = _normalizar(nombre)
    if not objetivo:
        return None
    return next(
        (
            nacionalidad
            for nacionalidad in Nacionalidad.objects.all()
            if _normalizar(nacionalidad.nacionalidad) == objetivo
        ),
        None,
    )


def _parse_fecha(valor: object):
    if isinstance(valor, date):
        return valor
    if not valor:
        return None
    for formato in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(str(valor), formato).date()
        except ValueError:
            continue
    return None


def _consultar_por_dni(dni: str, sexo: str | None) -> dict[str, Any]:
    sexos = (
        (sexo.upper(),)
        if sexo and sexo.upper() in {"M", "F", "X"}
        else (
            "M",
            "F",
            "X",
        )
    )
    ultimo_error = "No se encontraron datos en RENAPER."
    for sexo_consulta in sexos:
        resultado = consultar_datos_renaper(dni, sexo_consulta)
        if resultado.get("success"):
            return resultado
        ultimo_error = resultado.get("error") or ultimo_error
        if resultado.get("error_type") != "no_match":
            break
    return {"success": False, "error": ultimo_error}


def _datos_para_ciudadano(
    datos: dict[str, Any], dni: str
) -> tuple[dict[str, Any] | None, str | None]:
    apellido = " ".join(str(datos.get("apellido") or "").split()).title()
    nombre = " ".join(str(datos.get("nombre") or "").split()).title()
    fecha_nacimiento = _parse_fecha(datos.get("fecha_nacimiento"))
    if not apellido or not nombre or not fecha_nacimiento:
        return None, "RENAPER no devolvió datos mínimos para crear el ciudadano."

    try:
        documento = int(datos.get("dni") or dni)
    except (TypeError, ValueError):
        return None, "RENAPER devolvió un DNI inválido."

    ubicacion = _resolver_ubicacion(datos)
    ciudadano_data: dict[str, Any] = {
        "apellido": apellido,
        "nombre": nombre,
        "documento": documento,
        "tipo_documento": datos.get("tipo_documento") or Ciudadano.DOCUMENTO_DNI,
        "fecha_nacimiento": fecha_nacimiento,
        "origen_dato": "renaper",
        "cuil_cuit": str(datos.get("cuil")) if datos.get("cuil") else None,
        "calle": datos.get("calle") or None,
        "altura": str(datos.get("altura")) if datos.get("altura") else None,
        "piso_departamento": datos.get("piso_vivienda")
        or datos.get("departamento_vivienda"),
        "barrio": datos.get("barrio") or None,
        "codigo_postal": (
            str(datos.get("codigo_postal")) if datos.get("codigo_postal") else None
        ),
    }
    if datos.get("sexo"):
        ciudadano_data["sexo_id"] = datos["sexo"]
    for campo, objeto in ubicacion.items():
        if objeto:
            ciudadano_data[f"{campo}_id"] = objeto.pk
    nacionalidad = _resolver_nacionalidad(datos.get("nacionalidad_api"))
    if nacionalidad:
        ciudadano_data["nacionalidad_id"] = nacionalidad.pk
    return ciudadano_data, None


def construir_datos_ciudadano_desde_renaper(
    datos: dict[str, Any], dni: object
) -> tuple[dict[str, Any] | None, str | None]:
    """Mapea una respuesta RENAPER a campos de ``Ciudadano`` para consumidores."""

    return _datos_para_ciudadano(datos, str(dni).strip())


def resolver_nacionalidad_desde_renaper(valor: object):
    """Resuelve la nacionalidad local informada por RENAPER."""

    return _resolver_nacionalidad(valor)


def obtener_datos_ciudadano_desde_renaper(
    dni: object, sexo: str | None = None
) -> dict[str, Any]:
    """Consulta RENAPER y devuelve datos listos para precargar un formulario."""

    resultado = consultar_ciudadano_renaper(dni, sexo)
    if not resultado.get("success"):
        return resultado

    ciudadano_data, error = construir_datos_ciudadano_desde_renaper(
        resultado.get("data") or {}, dni
    )
    if not ciudadano_data:
        return {"success": False, "message": error}

    datos_formulario = dict(ciudadano_data)
    for field_name in ("sexo", "provincia", "municipio", "localidad", "nacionalidad"):
        field_id = f"{field_name}_id"
        if field_id in datos_formulario:
            datos_formulario[field_name] = datos_formulario.pop(field_id)
    return {
        "success": True,
        "data": datos_formulario,
        "message": resultado["message"],
        "datos_api": resultado.get("datos_api"),
    }


def _buscar_ciudadano_verificado(dni: str):
    ciudadano = Ciudadano.objects.filter(documento_unico_key=f"DNI_{dni}").first()
    if ciudadano:
        return ciudadano
    return Ciudadano.objects.filter(
        tipo_documento=Ciudadano.DOCUMENTO_DNI,
        documento=int(dni),
        tipo_registro_identidad=Ciudadano.TIPO_REGISTRO_ESTANDAR,
    ).first()


def _resumen_ciudadano(ciudadano) -> dict[str, Any]:
    sexo = str(ciudadano.sexo or "")
    sexo_normalizado = {"masculino": "M", "femenino": "F", "x": "X"}.get(
        sexo.lower(), sexo[:1].upper()
    )
    return {
        "dni": str(ciudadano.documento or ""),
        "nombre": ciudadano.nombre or "",
        "apellido": ciudadano.apellido or "",
        "genero": sexo,
        "sexo": sexo_normalizado,
        "fecha_nacimiento": (
            ciudadano.fecha_nacimiento.isoformat() if ciudadano.fecha_nacimiento else ""
        ),
        "edad": ciudadano.edad,
        "telefono": ciudadano.telefono or "",
        "ciudadano_id": ciudadano.pk,
    }


def consultar_ciudadano_renaper(dni: object, sexo: str | None = None) -> dict[str, Any]:
    """Consulta RENAPER sin inspeccionar ni crear ciudadanos locales."""

    dni_texto = str(dni or "").strip()
    if not dni_texto.isdigit() or len(dni_texto) < 7:
        return {"success": False, "message": "Debe ingresar un DNI válido."}
    resultado = _consultar_por_dni(dni_texto, sexo)
    if not resultado.get("success"):
        return {"success": False, "message": resultado.get("error")}
    return {
        "success": True,
        "message": "Datos obtenidos desde RENAPER.",
        "data": resultado.get("data") or {},
        "datos_api": resultado.get("datos_api"),
    }


def prevalidar_ciudadano_renaper(
    dni: object, sexo: str | None = None
) -> dict[str, Any]:
    """Consulta o recupera un ciudadano sin crear registros nuevos."""

    dni_texto = str(dni or "").strip()
    if not dni_texto.isdigit() or len(dni_texto) < 7:
        return {"success": False, "message": "Debe ingresar un DNI válido."}
    existente = _buscar_ciudadano_verificado(dni_texto)
    if existente:
        return {
            "success": True,
            "message": "Ciudadano existente validado.",
            "data": _resumen_ciudadano(existente),
            "datos_api": None,
            "created": False,
            "pending_creation": False,
        }
    resultado = consultar_ciudadano_renaper(dni_texto, sexo)
    if not resultado.get("success"):
        return resultado
    return {
        **resultado,
        "created": False,
        "pending_creation": True,
    }


def resolver_ciudadano_renaper(
    dni: object, usuario=None, sexo: str | None = None
) -> dict[str, Any]:
    """Resuelve un ciudadano validado; crea uno sólo si RENAPER lo permite."""

    resultado = prevalidar_ciudadano_renaper(dni, sexo)
    if not resultado.get("success") or not resultado.get("pending_creation"):
        return resultado
    ciudadano_data, error = _datos_para_ciudadano(
        resultado.get("data") or {}, str(dni).strip()
    )
    if not ciudadano_data:
        return {
            "success": False,
            "message": error,
        }
    if usuario and getattr(usuario, "is_authenticated", False):
        ciudadano_data.update({"creado_por": usuario, "modificado_por": usuario})
    try:
        ciudadano = Ciudadano.objects.create(**ciudadano_data)
    except IntegrityError:
        ciudadano = _buscar_ciudadano_verificado(str(dni).strip())
        if not ciudadano:
            logger.exception("ciudadanos.renaper.create_conflict")
            return {
                "success": False,
                "message": "No se pudo crear el ciudadano con los datos de RENAPER.",
            }
        return {
            "success": True,
            "message": "El ciudadano ya existe en la base.",
            "data": _resumen_ciudadano(ciudadano),
            "datos_api": None,
            "created": False,
        }
    return {
        "success": True,
        "message": "Ciudadano creado automáticamente con datos de RENAPER.",
        "data": _resumen_ciudadano(ciudadano),
        "datos_api": resultado.get("datos_api"),
        "created": True,
    }
