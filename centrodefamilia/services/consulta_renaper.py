from django.conf import settings
from django.core.cache import cache
import requests
import unicodedata
from ciudadanos.models import Sexo, TipoDocumento
from requests.exceptions import RequestException, ConnectionError
import logging

logger = logging.getLogger(__name__)

API_BASE = settings.RENAPER_API_URL
LOGIN_URL = f"{API_BASE}/auth/login"
CONSULTA_URL = f"{API_BASE}/consultarenaper"


class APIClient:
    def __init__(self):
        self.username = settings.RENAPER_API_USERNAME
        self.password = settings.RENAPER_API_PASSWORD
        self.session = requests.Session()  # Reutilizar conexiones
        self.session.timeout = 10

    def get_token(self):
        # Cache del token por 50 minutos (tokens duran 1 hora)
        token_data = cache.get("renaper_token")
        if token_data:
            return token_data["token"]

        return self._login_and_cache_token()

    def _login_and_cache_token(self):
        try:
            response = self.session.post(
                LOGIN_URL, json={"username": self.username, "password": self.password}
            )
            response.raise_for_status()
        except ConnectionError:
            logger.error("Error de conexión con RENAPER")
            raise Exception("Error de conexión con el servicio.")
        except RequestException as e:
            logger.error(f"Error en login RENAPER: {str(e)}")
            raise Exception(f"No se pudo conectar al servicio de login: {str(e)}")

        data = response.json()
        token = data.get("token")

        # Cache por 50 minutos
        cache.set("renaper_token", {"token": token}, 3000)
        return token

    def consultar_ciudadano(self, dni, sexo):
        try:
            token = self.get_token()
        except Exception as e:
            return {"success": False, "error": f"Error al obtener token: {str(e)}"}

        headers = {"Authorization": f"Bearer {token}"}
        params = {"dni": dni, "sexo": sexo.upper()}

        try:
            response = self.session.get(CONSULTA_URL, headers=headers, params=params)
            response.raise_for_status()
        except ConnectionError:
            logger.error(f"Error de conexión RENAPER para DNI {dni}")
            return {"success": False, "error": "Error de conexión al servicio."}
        except RequestException as e:
            logger.error(f"Error consulta RENAPER DNI {dni}: {str(e)}")
            return {
                "success": False,
                "error": f"No se pudo conectar al servicio: {str(e)}",
            }

        try:
            data = response.json()
        except Exception as e:
            return {"success": False, "error": f"No se pudo decodificar JSON: {str(e)}"}

        if not data.get("isSuccess", False):
            return {
                "success": False,
                "error": "No se encontró coincidencia.",
                "raw_response": data,
            }

        return {"success": True, "data": data["result"]}


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
            return {
                "success": False,
                "error": response.get("error", "Error desconocido"),
                "raw_response": response.get("raw_response"),
            }

        datos = response["data"]

        if datos.get("mensaf") == "FALLECIDO":
            return {"success": False, "error": f"El ciudadano se encuentra fallecido."}

        sexo_map = {"F": "Femenino", "M": "Masculino", "X": "X"}
        sexo_texto = sexo_map.get(sexo)
        sexo_pk = None
        if sexo_texto:
            sexo_obj = Sexo.objects.filter(sexo=sexo_texto).first()
            sexo_pk = sexo_obj.pk if sexo_obj else None

        tipo_doc = TipoDocumento.objects.get(tipo="DNI")

        # Solo datos básicos de RENAPER, sin mapeo de ubicación

        # Mapeo optimizado de datos
        def safe_int(value):
            try:
                return (
                    int(value)
                    if value and str(value).strip() not in ["0", ""]
                    else None
                )
            except (ValueError, TypeError):
                return None

        datos_mapeados = {
            "cuil": safe_int(datos.get("cuil")),
            "dni": int(dni),
            "apellido": datos.get("apellido", ""),
            "nombre": datos.get("nombres", ""),
            "genero": sexo,
            "fecha_nacimiento": datos.get("fechaNacimiento"),
            # Datos de ubicación sin mapear (se seleccionarán manualmente)
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
        }

        return {"success": True, "data": datos_mapeados, "datos_api": datos}

    except Exception as e:
        return {"success": False, "error": f"Error inesperado: {str(e)}"}
