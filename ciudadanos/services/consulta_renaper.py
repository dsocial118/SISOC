from django.conf import settings
import requests
import datetime
import unicodedata
from ciudadanos.models import Sexo, TipoDocumento, Provincia

API_BASE = settings.RENAPER_API_URL
LOGIN_URL = f"{API_BASE}/auth/login"
CONSULTA_URL = f"{API_BASE}/consultarenaper"


class APIClient:
    def __init__(self):
        self.username = settings.RENAPER_API_USERNAME
        self.password = settings.RENAPER_API_PASSWORD
        self.token = None
        self.token_expiration = None

    def login(self):
        response = requests.post(
            LOGIN_URL, json={"username": self.username, "password": self.password}
        )

        if response.status_code != 200:
            raise Exception(f"Login fallido: {response.status_code} {response.text}")

        data = response.json()
        self.token = data.get("token")
        self.token_expiration = datetime.datetime.fromisoformat(
            data["expiration"].replace("Z", "+00:00")
        )

    def get_token(self):
        if (
            not self.token
            or datetime.datetime.now(datetime.timezone.utc) >= self.token_expiration
        ):
            self.login()
        return self.token

    def consultar_ciudadano(self, dni, sexo):
        token = self.get_token()
        headers = {"Authorization": f"Bearer {token}"}
        params = {"dni": dni, "sexo": sexo.upper()}

        response = requests.get(CONSULTA_URL, headers=headers, params=params)

        if response.status_code != 200:
            try:
                error_data = response.json()
            except Exception:
                error_data = response.text
            return {
                "success": False,
                "error": f"Error HTTP {response.status_code}: {error_data}",
            }

        try:
            data = response.json()
        except Exception as e:
            return {"success": False, "error": f"No se pudo decodificar JSON: {str(e)}"}

        if not data.get("isSuccess", False):
            return {
                "success": False,
                "error": f"API error: {data.get('message', 'Error desconocido')}",
                "raw_response": data,
            }

        return {"success": True, "data": data["result"]}


def normalizar(texto):
    if not texto:
        return ""
    texto = texto.lower().replace("_", " ")
    texto = (
        unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("utf-8")
    )
    return texto.strip()


def consultar_datos_renaper(dni, sexo):
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
        return {"success": False, "fallecido": True}

    sexo_map = {"F": "Femenino", "M": "Masculino", "X": "X"}
    sexo_texto = sexo_map.get(sexo)
    sexo_pk = None
    if sexo_texto:
        sexo_obj = Sexo.objects.filter(sexo=sexo_texto).first()
        sexo_pk = sexo_obj.pk if sexo_obj else None

    tipo_doc = TipoDocumento.objects.get(tipo="DNI")

    EQUIVALENCIAS_PROVINCIAS = {
        "ciudad de buenos aires": "ciudad autonoma de buenos aires",
        "caba": "ciudad autonoma de buenos aires",
        "ciudad autonoma de buenos aires": "ciudad autonoma de buenos aires",
        "tierra del fuego": "tierra del fuego, antartida e islas del atlantico sur",
        "tierra del fuego antartida e islas del atlantico sur": "tierra del fuego, antartida e islas del atlantico sur",
    }

    provincia_api = datos.get("provincia", "")
    provincia_api_norm = normalizar(provincia_api)
    provincia_api_norm = EQUIVALENCIAS_PROVINCIAS.get(
        provincia_api_norm, provincia_api_norm
    )

    provincia = None
    for prov in Provincia.objects.all():
        nombre_norm = normalizar(prov.nombre)
        if provincia_api_norm == nombre_norm:
            provincia = prov
            break

    datos_mapeados = {
        "documento": dni,
        "tipo_documento": tipo_doc.pk,
        "sexo": sexo_pk,
        "apellido": datos.get("apellido"),
        "nombre": datos.get("nombres"),
        "fecha_nacimiento": datos.get("fechaNacimiento"),
        "calle": datos.get("calle"),
        "altura": datos.get("numero"),
        "piso_departamento": f"{datos.get('piso', '')} {datos.get('departamento', '')}".strip(),
        "ciudad": datos.get("ciudad"),
        "provincia": provincia.pk if provincia else None,
        "pais": datos.get("pais"),
        "codigo_postal": datos.get("cpostal"),
    }

    return {"success": True, "data": datos_mapeados, "datos_api": datos}
