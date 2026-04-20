import logging
import unicodedata

from django.conf import settings
from django.core.cache import cache
import requests

from ciudadanos.models import Ciudadano
from core.models import Sexo

logger = logging.getLogger("django")

API_BASE = settings.RENAPER_API_URL
LOGIN_URL = f"{API_BASE}/auth/login"
CONSULTA_URL = f"{API_BASE}/consultarenaper"


class RenaperServiceError(RuntimeError):
    def __init__(self, message, error_type, raw_response=None):
        super().__init__(message)
        self.error_type = error_type
        self.raw_response = raw_response


def _safe_response_payload(response):
    if response is None:
        return None

    try:
        return response.json()
    except ValueError:
        return getattr(response, "text", None)


def _build_error_result(message, error_type, raw_response=None, **extra):
    result = {"success": False, "error": message, "error_type": error_type}
    if raw_response is not None:
        result["raw_response"] = raw_response
    result.update(extra)
    return result


class APIClient:
    def __init__(self):
        self.username = settings.RENAPER_API_USERNAME
        self.password = settings.RENAPER_API_PASSWORD
        self.session = requests.Session()  # Reutilizar conexiones

    def get_token(self):
        # Cache del token por 50 minutos (tokens duran 1 hora)
        token_data = cache.get("renaper_token")
        if token_data:
            return token_data["token"]

        return self._login_and_cache_token()

    def _login_and_cache_token(self):
        try:
            response = self.session.post(
                LOGIN_URL,
                json={"username": self.username, "password": self.password},
                timeout=10,
            )
            response.raise_for_status()
        except requests.Timeout as exc:
            raise RenaperServiceError(
                "RENAPER no respondio a tiempo durante la autenticacion.",
                "timeout",
            ) from exc
        except requests.HTTPError as exc:
            status_code = getattr(exc.response, "status_code", None)
            error_type = "auth_error" if status_code in {401, 403} else "remote_error"
            message = (
                "RENAPER rechazo la autenticacion."
                if error_type == "auth_error"
                else "RENAPER devolvio un error durante la autenticacion."
            )
            raise RenaperServiceError(
                message,
                error_type,
                raw_response=_safe_response_payload(exc.response),
            ) from exc
        except requests.RequestException as exc:
            raise RenaperServiceError(
                f"No se pudo conectar al servicio de login de RENAPER: {str(exc)}",
                "remote_error",
            ) from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise RenaperServiceError(
                "RENAPER devolvio una respuesta invalida durante la autenticacion.",
                "invalid_response",
                raw_response=getattr(response, "text", None),
            ) from exc

        token = data.get("token") if isinstance(data, dict) else None
        if not token:
            raise RenaperServiceError(
                "RENAPER no devolvio un token de autenticacion.",
                "invalid_response",
                raw_response=data,
            )

        # Cache por 50 minutos
        cache.set("renaper_token", {"token": token}, 3000)
        return token

    def consultar_ciudadano(self, dni, sexo):
        try:
            token = self.get_token()
        except RenaperServiceError as exc:
            return _build_error_result(
                str(exc), exc.error_type, raw_response=exc.raw_response
            )

        headers = {"Authorization": f"Bearer {token}"}
        params = {"dni": dni, "sexo": sexo.upper()}

        try:
            response = self.session.get(
                CONSULTA_URL, headers=headers, params=params, timeout=10
            )
            response.raise_for_status()
        except requests.Timeout:
            return _build_error_result(
                "RENAPER no respondio a tiempo durante la consulta.", "timeout"
            )
        except requests.HTTPError as exc:
            status_code = getattr(exc.response, "status_code", None)
            error_type = "auth_error" if status_code in {401, 403} else "remote_error"
            message = (
                "RENAPER rechazo la autenticacion de la consulta."
                if error_type == "auth_error"
                else "RENAPER devolvio un error durante la consulta."
            )
            return _build_error_result(
                message,
                error_type,
                raw_response=_safe_response_payload(exc.response),
            )
        except requests.RequestException as exc:
            return _build_error_result(
                f"No se pudo consultar RENAPER: {str(exc)}", "remote_error"
            )

        try:
            data = response.json()
        except ValueError as exc:
            return _build_error_result(
                f"No se pudo decodificar JSON de RENAPER: {str(exc)}",
                "invalid_response",
                raw_response=getattr(response, "text", None),
            )

        if not isinstance(data, dict):
            return _build_error_result(
                "RENAPER devolvio una estructura de respuesta invalida.",
                "invalid_response",
                raw_response=data,
            )

        if not data.get("isSuccess", False):
            return _build_error_result(
                "No se encontro coincidencia.", "no_match", raw_response=data
            )

        result = data.get("result")
        if not isinstance(result, dict):
            return _build_error_result(
                "RENAPER devolvio una respuesta invalida.",
                "invalid_response",
                raw_response=data,
            )

        return {"success": True, "data": result}


def normalizar(texto):
    if not texto:
        return ""
    texto = texto.lower().replace("_", " ")
    return (
        unicodedata.normalize("NFKD", texto)
        .encode("ascii", "ignore")
        .decode("utf-8")
        .strip()
    )


def consultar_datos_renaper(dni, sexo):
    try:
        client = APIClient()
        response = client.consultar_ciudadano(dni, sexo)

        if not response["success"]:
            return _build_error_result(
                response.get("error", "Error desconocido al consultar RENAPER"),
                response.get("error_type", "unexpected_error"),
                raw_response=response.get("raw_response"),
            )

        datos = response["data"]
        if not isinstance(datos, dict):
            return _build_error_result(
                "RENAPER devolvio un payload invalido del ciudadano.",
                "invalid_response",
                raw_response=datos,
            )

        if datos.get("mensaf") == "FALLECIDO":
            return _build_error_result(
                "El ciudadano se encuentra fallecido.",
                "fallecido",
                raw_response=datos,
                fallecido=True,
            )

        sexo_map = {"F": "Femenino", "M": "Masculino", "X": "X"}
        sexo_texto = sexo_map.get(sexo)
        sexo_pk = None
        if sexo_texto:
            sexo_obj = Sexo.objects.filter(sexo=sexo_texto).first()
            sexo_pk = sexo_obj.pk if sexo_obj else None

        # Solo datos basicos de RENAPER, sin mapeo de ubicacion
        # Mapeo optimizado de datos
        def safe_int(value):
            try:
                return (
                    int(value)
                    if value and str(value).strip() not in ["0", ""]
                    else None
                )
            except (ValueError, TypeError):
                logger.error(f"Error safe_int RENAPER DNI {dni}: {value}")
                return None

        datos_mapeados = {
            "cuil": safe_int(datos.get("cuil")),
            "dni": int(dni),
            "apellido": datos.get("apellido", ""),
            "nombre": datos.get("nombres", ""),
            "genero": sexo,
            "sexo": sexo_pk,
            "tipo_documento": Ciudadano.DOCUMENTO_DNI,
            "fecha_nacimiento": datos.get("fechaNacimiento"),
            # Datos de ubicacion sin mapear (se seleccionaran manualmente)
            "provincia_api": datos.get("provincia", ""),
            "municipio_api": datos.get("municipio", ""),
            "localidad_api": datos.get("ciudad", ""),
            "codigo_postal": safe_int(datos.get("cpostal")),
            "calle": datos.get("calle", ""),
            "altura": safe_int(datos.get("numero")),
            "piso_vivienda": datos.get("piso", "") or None,
            "departamento_vivienda": datos.get("departamento", "") or None,
            "barrio": (
                datos.get("barrio")
                if datos.get("barrio") not in ["0", "", None]
                else None
            ),
            "monoblock": datos.get("monoblock") or None,
            "nacionalidad_api": datos.get("pais") or "",
        }

        return {"success": True, "data": datos_mapeados, "datos_api": datos}
    except Exception as exc:
        logger.exception(f"Error inesperado consultando RENAPER: {str(exc)}")
        return _build_error_result(
            f"Error inesperado al consultar RENAPER: {str(exc)}",
            "unexpected_error",
        )
