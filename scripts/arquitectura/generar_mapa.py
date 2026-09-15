"""Genera el mapa vivo de arquitectura de SISOC a partir del repositorio.

Extrae, sin datos hardcodeados de dominio salvo la clasificacion por zona:

- apps propias declaradas en ``config/settings.py`` (INSTALLED_APPS);
- prefijos web y API montados en ``config/urls.py``;
- señales de autenticacion de cada API (token DRF = plano movil, API key =
  server-to-server, sesion = web); una API puede combinarlas;
- aristas reales entre apps por AST de imports, distinguiendo fachada publica
  (``<app>.api``) de import de internals;
- arbol del menu lateral (``templates/includes/sidebar/opciones.html``) con sus
  permisos, para saber que modulos alcanza el usuario;
- PWA declaradas en ``scripts/operacion/pwas.json``;
- roles de contenedor de ``docker/django/entrypoint.py`` y servicios Compose.

Salidas:

- ``var/arquitectura/grafo.json``: el grafo que consume la vista. Fuera de git
  (se reescribe en cada arranque) y fuera de ``static/`` (Nginx publica
  ``/static/`` por alias, sin pasar por Django, y el grafo describe permisos,
  rutas y estructura interna). Lo entrega una vista autenticada.
- Con ``--docs``, ademas: ``docs/arquitectura/grafo_sisoc.json`` versionable y
  ``docs/arquitectura/mapa_sisoc.html``, documento de una sola pieza para leer el
  mapa fuera de SISOC. El arranque NO los toca.

``static/arquitectura/mapa.css`` y ``mapa.js`` son fuente versionada del visor,
no salidas: van como estaticos porque el CSP de produccion no admite ``<style>``
ni ``<script>`` inline.

Uso:

    python scripts/arquitectura/generar_mapa.py           # solo el grafo de runtime
    python scripts/arquitectura/generar_mapa.py --docs    # ademas los artefactos de docs/
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
# CSS y JS del visor son fuente versionada, no salidas: se editan aca.
FUENTE_VISOR = RAIZ / "static" / "arquitectura"
# El grafo se regenera en cada arranque, asi que vive fuera de git: si escribiera
# en el checkout, deploy_refresh.sh abortaria el despliegue siguiente por
# cambios locales tracked.
SALIDA_RUNTIME = RAIZ / "var" / "arquitectura"
SALIDA_DOCS = RAIZ / "docs" / "arquitectura"
FUENTES_CSS = (
    "https://fonts.googleapis.com/css2"
    "?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap"
)

# Paquetes propios que no estan en INSTALLED_APPS pero participan del runtime.
PAQUETES_EXTRA = ["iam", "healthcheck"]

# Unica pieza editorial del generador: en que banda del mapa se dibuja cada app.
# Una app nueva sin clasificar cae en "sin_clasificar" y queda visible como tal.
ZONAS = [
    {
        "id": "nucleo",
        "nombre": "Nucleo compartido",
        "detalle": "Base transversal. No puede importar dominios (contrato core-no-domains).",
        "apps": ["core", "users", "iam", "audittrail", "historial", "healthcheck", "sentry"],
    },
    {
        "id": "personas",
        "nombre": "Personas",
        "detalle": "Identidad ciudadana compartida por todos los dominios.",
        "apps": ["ciudadanos"],
    },
    {
        "id": "comedores_core",
        "nombre": "Comedores Core",
        "detalle": "Bounded context: ciclo completo de comedor. Afuera solo se consume por *.api.",
        "apps": [
            "comedores",
            "admisiones",
            "relevamientos",
            "organizaciones",
            "duplas",
            "intervenciones",
            "acompanamientos",
            "expedientespagos",
            "importarexpediente",
            "rendicioncuentasfinal",
            "rendicioncuentasmensual",
        ],
    },
    {
        "id": "satelites",
        "nombre": "Satelites de dominio",
        "detalle": "Verticales con frontera declarada en .importlinter; extraibles a futuro.",
        "apps": [
            "centrodeinfancia",
            "centrodefamilia",
            "celiaquia",
            "VAT",
            "pas",
            "ver_para_ser_libre",
            "dispositivos",
            "datacalle",
        ],
    },
    {
        "id": "transversal",
        "nombre": "Servicios al usuario",
        "detalle": "Atraviesan dominios sin ser dueños de ninguno.",
        "apps": ["dashboard", "comunicados", "encuestas", "ocr", "insumos"],
    },
    {
        "id": "integracion",
        "nombre": "Capa de integracion",
        "detalle": "Contratos hacia afuera: PWA y consumidores server-to-server.",
        "apps": ["pwa", "ticketera"],
    },
    {
        "id": "sin_clasificar",
        "nombre": "Sin clasificar",
        "detalle": "App instalada que todavia no fue ubicada en una zona del mapa.",
        "apps": [],
    },
]

NOMBRES = {
    "VAT": "INET / VAT",
    "pas": "PAS",
    "ocr": "OCR",
    "pwa": "PWA (backend)",
    "iam": "IAM",
    "ver_para_ser_libre": "Ver para Ser Libre",
    "centrodeinfancia": "Centro de Infancia",
    "centrodefamilia": "Centro de Familia",
    "datacalle": "DataCalle",
    "celiaquia": "Celiaquia",
    "rendicioncuentasmensual": "Rendicion mensual",
    "rendicioncuentasfinal": "Rendicion final",
    "expedientespagos": "Expedientes de pago",
    "importarexpediente": "Importar expediente",
    "audittrail": "Audit trail",
    "healthcheck": "Healthcheck",
    "dispositivos": "Dispositivos",
    "acompanamientos": "Acompanamientos",
}

# Consumo de APIs por PWA. Los frontends viven en repos privados separados, asi que
# esto no se puede inferir del monolito: queda declarado con su nivel de certeza y
# su evidencia. Revisar al tocar una PWA o al agregar un namespace de API.
CONSUMO_PWA = {
    "espacios": [
        ("users", "token", "declarado", "docs/contexto/aplicaciones.md: /api/users/ login, me, logout"),
        ("pwa", "token", "declarado", "pwa/api_urls.py: espacios, nomina, actividades, mensajes, push"),
        ("comedores", "token", "declarado", "/api/comedores/: nomina, documentos, prestaciones, rendiciones, usuarios"),
    ],
    "gestionar": [
        ("comedores", "token", "declarado", "/api/territorial/: comedores por provincia, actas, primer seguimiento, firma, imagenes"),
        ("users", "token", "declarado", "/api/users/login/ con Profile.es_territorial_comedor"),
    ],
    "datacalle": [
        ("datacalle", "token", "declarado", "datacalle/api_urls.py + TokenAuthentication en datacalle/api_views.py"),
        ("users", "token", "inferido", "login unico del plano movil en /api/users/login/"),
    ],
}

# Sistemas externos. Cada fila tiene evidencia en el repo; ver la columna evidencia.
EXTERNOS = [
    {
        "id": "gestionar_appsheet",
        "nombre": "GESTIONAR (AppSheet)",
        "rol": "Frontend de campo de relevamientos de comedores. En corte progresivo hacia el plano movil nativo.",
        "direccion": "bidireccional",
        "plano": "api_key",
        "modulos": ["relevamientos", "comedores"],
        "evidencia": "relevamientos/urls/api_urls.py (api/relevamiento, HasAPIKey), comedores/tasks.py, GESTIONAR_API_*",
    },
    {
        "id": "renaper",
        "nombre": "RENAPER",
        "rol": "Consulta de identidad ciudadana. Un solo cliente compartido; ningun dominio tiene el suyo.",
        "direccion": "salida",
        "plano": "",
        "modulos": ["core"],
        "evidencia": "core/integrations/renaper.py, core/services/renaper.py, RENAPER_API_*",
    },
    {
        "id": "sintys",
        "nombre": "SINTyS",
        "rol": "Cruces mensuales de PAS por exportacion e importacion de archivo. No hay API.",
        "direccion": "manual",
        "plano": "",
        "modulos": ["pas"],
        "evidencia": "pas/services/cruces_service.py (generar_nomina_sintys_pas, registrar_importacion_sintys)",
    },
    {
        "id": "ticketera_ext",
        "nombre": "Ticketera",
        "rol": "App externa de tickets. Consume usuarios y auth de SISOC; apagable por TICKETERA_ENABLED.",
        "direccion": "entrada",
        "plano": "api_key",
        "modulos": ["ticketera"],
        "evidencia": "docs/integraciones/ticketera_api.md, ticketera/api_views.py (HasAPIKey)",
    },
    {
        "id": "consumidores_s2s",
        "nombre": "Consumidores server-to-server",
        "rol": "APIs abiertas por API key cuyo consumidor no esta declarado en este repo. Vale confirmar quien las usa.",
        "direccion": "entrada",
        "plano": "api_key",
        "modulos": ["VAT", "centrodefamilia", "comunicados", "core"],
        "evidencia": "HasAPIKey en VAT/api_views.py, centrodefamilia/api_views.py, comunicados/api_views.py, core/api_views.py",
    },
    {
        "id": "webpush",
        "nombre": "Web Push",
        "rol": "Notificaciones push hacia la PWA de Espacios.",
        "direccion": "salida",
        "plano": "",
        "modulos": ["pwa"],
        "evidencia": "PWA_WEB_PUSH_PUBLIC_KEY / PRIVATE_KEY / SUBJECT, /api/pwa/push/",
    },
    {
        "id": "sentry",
        "nombre": "Sentry",
        "rol": "Observabilidad de errores, activable por entorno.",
        "direccion": "salida",
        "plano": "",
        "modulos": ["sentry"],
        "evidencia": "SENTRY_ENABLED, SENTRY_DSN, docs/implementaciones/sentry.md",
    },
    {
        "id": "maps",
        "nombre": "Google Maps",
        "rol": "Mapas embebidos en detalle de comedor, ciudadano y CDI.",
        "direccion": "salida",
        "plano": "",
        "modulos": ["core", "comedores", "ciudadanos", "centrodeinfancia"],
        "evidencia": "core/templatetags/custom_filters.py, GOOGLE_MAPS_API_KEY",
    },
    {
        "id": "email",
        "nombre": "SMTP / correo",
        "rol": "Reset de contrasena y envios masivos por el worker de mailing.",
        "direccion": "salida",
        "plano": "",
        "modulos": ["users"],
        "evidencia": "EMAIL_*, rol de contenedor mailing_worker",
    },
]

EXCLUIR_DIR = {
    "migrations",
    "tests",
    "test",
    "benchmarks",
    "__pycache__",
    "node_modules",
    "static",
    "templates",
    "fixtures",
}
EXCLUIR_ARCHIVO_RE = re.compile(
    r"(^test_|_test\.py$|^tests?\.py$|^conftest\.py$|^debug_queries\.py$)"
)


def _texto(ruta: Path) -> str:
    """Lee como utf-8-sig: hay modulos del repo con BOM y ``ast.parse`` los rechaza."""
    try:
        return ruta.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return ""


def _git(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=RAIZ,
            capture_output=True,
            text=True,
            check=True,
            timeout=20,
        ).stdout.strip()
    except (subprocess.SubprocessError, OSError):
        return ""


# --------------------------------------------------------------------------- #
# Extraccion
# --------------------------------------------------------------------------- #


def apps_instaladas() -> list[str]:
    """Apps propias de INSTALLED_APPS, en el orden en que estan declaradas."""
    contenido = _texto(RAIZ / "config" / "settings.py")
    bloque = re.search(r"INSTALLED_APPS\s*=\s*\[(.*?)\n\]", contenido, re.S)
    if not bloque:
        return []

    apps: list[str] = []
    for crudo in re.findall(r'"([^"]+)"', bloque.group(1)):
        paquete = crudo.split(".")[0]
        if paquete in {"django", "rest_framework"} or "." in crudo and paquete in {
            "crispy_forms",
            "crispy_bootstrap5",
        }:
            continue
        if not (RAIZ / paquete).is_dir():
            continue
        if paquete not in apps:
            apps.append(paquete)
    return apps


def rutas_montadas() -> dict[str, dict[str, list[str]]]:
    """Prefijos web y API por app, leidos de config/urls.py."""
    contenido = _texto(RAIZ / "config" / "urls.py")
    rutas: dict[str, dict[str, list[str]]] = {}
    patron = re.compile(r'path\(\s*"([^"]*)"\s*,\s*include\(\s*"([^"]+)"\s*\)')
    for prefijo, modulo in patron.findall(contenido):
        app = modulo.split(".")[0]
        if not (RAIZ / app).is_dir():
            continue
        destino = "api" if prefijo.startswith("api/") else "web"
        entrada = rutas.setdefault(app, {"web": [], "api": []})
        valor = "/" + prefijo if prefijo else "/ (raiz)"
        if valor not in entrada[destino]:
            entrada[destino].append(valor)
    return rutas


def auth_de_apis(apps: list[str]) -> dict[str, list[str]]:
    """Planos de autenticacion por app.

    Deteccion por señales en el codigo, no por resolucion de permisos: una API
    puede combinarlos (``HasAPIKeyOrToken``, ``HasAPIKey | IsAuthenticated``) y
    ademas heredar los defaults de DRF. Por eso se acumulan todas las señales
    encontradas en vez de elegir una sola.
    """
    señales = {
        "token": ("TokenAuthentication", "HasAPIKeyOrToken"),
        "api_key": ("HasAPIKey",),
        "sesion": ("SessionAuthentication", "IsAuthenticated"),
    }
    planos: dict[str, set[str]] = {}
    for app in apps:
        for archivo in (RAIZ / app).rglob("api_views*.py"):
            if any(p in EXCLUIR_DIR for p in archivo.parts):
                continue
            contenido = _texto(archivo)
            for plano, marcas in señales.items():
                if any(marca in contenido for marca in marcas):
                    planos.setdefault(app, set()).add(plano)
    return {app: sorted(v) for app, v in planos.items()}


def _archivos_py(app: str):
    base = RAIZ / app
    for carpeta, subdirs, archivos in os.walk(base):
        subdirs[:] = [d for d in subdirs if d not in EXCLUIR_DIR]
        for nombre in archivos:
            if not nombre.endswith(".py") or EXCLUIR_ARCHIVO_RE.search(nombre):
                continue
            yield Path(carpeta) / nombre


def aristas_de_imports(apps: list[str]) -> tuple[list[dict], dict[str, dict]]:
    """Dependencias reales entre apps, por AST. Distingue fachada de internals."""
    conocidas = set(apps)
    acumulado: dict[tuple[str, str, str], dict] = {}
    peso: dict[str, dict] = {app: {"archivos": 0, "lineas": 0} for app in apps}

    for app in apps:
        for archivo in _archivos_py(app):
            fuente = _texto(archivo)
            if not fuente:
                continue
            peso[app]["archivos"] += 1
            peso[app]["lineas"] += fuente.count("\n") + 1
            try:
                arbol = ast.parse(fuente)
            except SyntaxError:
                continue

            relativo = archivo.relative_to(RAIZ).as_posix()
            for nodo in ast.walk(arbol):
                modulos: list[str] = []
                if isinstance(nodo, ast.ImportFrom) and nodo.level == 0 and nodo.module:
                    modulos.append(nodo.module)
                elif isinstance(nodo, ast.Import):
                    modulos.extend(alias.name for alias in nodo.names)

                for modulo in modulos:
                    destino = modulo.split(".")[0]
                    if destino == app or destino not in conocidas:
                        continue
                    partes = modulo.split(".")
                    es_fachada = len(partes) > 1 and partes[1] == "api"
                    clave = (app, destino, "api" if es_fachada else "internal")
                    entrada = acumulado.setdefault(
                        clave,
                        {
                            "src": app,
                            "dst": destino,
                            "kind": clave[2],
                            "n": 0,
                            "ejemplos": [],
                        },
                    )
                    entrada["n"] += 1
                    muestra = f"{relativo} -> {modulo}"
                    if len(entrada["ejemplos"]) < 4 and muestra not in entrada["ejemplos"]:
                        entrada["ejemplos"].append(muestra)

    aristas = sorted(acumulado.values(), key=lambda a: (-a["n"], a["src"], a["dst"]))
    return aristas, peso


def nombres_de_url(apps: list[str]) -> dict[str, str]:
    """Mapa name= de urls -> app que lo define."""
    mapa: dict[str, str] = {}
    for app in apps:
        for archivo in (RAIZ / app).rglob("*urls*.py"):
            if any(p in EXCLUIR_DIR for p in archivo.parts):
                continue
            for nombre in re.findall(r'name\s*=\s*"([^"]+)"', _texto(archivo)):
                mapa.setdefault(nombre, app)
    return mapa


def menu_lateral(mapa_urls: dict[str, str]) -> list[dict]:
    """Arbol del sidebar: grupos, items, permisos y app de destino."""
    ruta = RAIZ / "templates" / "includes" / "sidebar" / "opciones.html"
    lineas = _texto(ruta).split("\n")

    re_grupo = re.compile(r"nav-main-item")
    re_orden = re.compile(r'style="order:\s*(\d+)')
    re_url = re.compile(r"{%\s*url '([^']+)'")
    re_texto = re.compile(r">\s*([A-ZÁÉÍÓÚÑa-záéíóúñ][^<>{}]{2,48}?)\s*<")
    re_perm_code = re.compile(r'has_perm_code:"([^"]+)"')
    re_perm_any = re.compile(r'has_any_perm:"([^"]+)"')
    re_perm_django = re.compile(r"perms\.([A-Za-z_]+\.[A-Za-z_]+)")
    re_superuser = re.compile(r"is_superuser")

    re_texto_suelto = re.compile(r"^\s*([A-ZÁÉÍÓÚÑa-záéíóúñ][^<>{}\"=%]{1,47})\s*$")

    def etiqueta_desde(indice: int) -> str:
        for salto in range(indice, min(indice + 8, len(lineas))):
            encontrado = re_texto.search(lineas[salto]) or re_texto_suelto.search(lineas[salto])
            if encontrado:
                return (
                    encontrado.group(1)
                    .replace("&oacute;", "o")
                    .replace("&aacute;", "a")
                    .replace("&eacute;", "e")
                    .replace("&iacute;", "i")
                    .replace("&uacute;", "u")
                    .strip()
                )
        return ""

    def permisos_de(condiciones: list[str]) -> list[str]:
        """Permisos de todos los {% if %} abiertos: el gate real de un item."""
        encontrados: set[str] = set()
        for condicion in condiciones:
            encontrados.update(re_perm_code.findall(condicion))
            for grupo in re_perm_any.findall(condicion):
                encontrados.update(p.strip() for p in grupo.split(","))
            encontrados.update(re_perm_django.findall(condicion))
            if re_superuser.search(condicion):
                encontrados.add("is_superuser")
        return sorted(encontrados)

    grupos: list[dict] = []
    pila: list[dict] = []
    condiciones: list[str] = []
    nivel = 0

    for i, linea in enumerate(lineas):
        # Pila de {% if %}: un if y su endif en la misma linea es inline, no anida.
        abre_if = linea.count("{% if")
        cierra_if = linea.count("{% endif %}")
        if abre_if > cierra_if:
            condiciones.append(linea)
        elif cierra_if > abre_if and condiciones:
            del condiciones[-(cierra_if - abre_if) :]

        if re_grupo.search(linea):
            orden = re_orden.search(linea) or re_orden.search(
                lineas[i + 1] if i + 1 < len(lineas) else ""
            )
            grupos.append(
                {
                    "orden": int(orden.group(1)) if orden else 99,
                    "label": etiqueta_desde(i),
                    "items": [],
                    "linea": i + 1,
                }
            )
            pila, nivel = [], 0
        elif grupos:
            # Un <a href="#"> es un desplegable: agrupa, no navega. El de nivel 0
            # es el toggle del propio grupo y no cuenta como subgrupo.
            if '<a href="#"' in linea and nivel > 0:
                pila = [s for s in pila if s["nivel"] < nivel]
                pila.append({"label": etiqueta_desde(i), "nivel": nivel})
            else:
                encontrado = re_url.search(linea)
                if encontrado:
                    nombre_url = encontrado.group(1)
                    # Un enlace de nivel 0 despues de que el grupo ya cerro su
                    # <ul> es un hermano suelto (p. ej. "Mi cuenta"), no un item
                    # del grupo anterior.
                    if nivel == 0 and grupos[-1]["items"]:
                        grupos.append(
                            {
                                "orden": 98,
                                "label": etiqueta_desde(i),
                                "items": [],
                                "linea": i + 1,
                            }
                        )
                        pila = []
                    grupos[-1]["items"].append(
                        {
                            "label": etiqueta_desde(i),
                            "url_name": nombre_url,
                            "app": mapa_urls.get(nombre_url.split(":")[-1], ""),
                            "nivel": nivel,
                            "ruta": [s["label"] for s in pila if s["nivel"] < nivel],
                            "permisos": permisos_de(condiciones),
                            "linea": i + 1,
                        }
                    )

        # Nesting real del arbol: profundidad de <ul>.
        nivel += linea.count("<ul")
        cierres = linea.count("</ul>")
        if cierres:
            nivel = max(0, nivel - cierres)
            pila = [s for s in pila if s["nivel"] < nivel]

    return sorted(grupos, key=lambda g: g["orden"])


def pwas() -> list[dict]:
    ruta = RAIZ / "scripts" / "operacion" / "pwas.json"
    try:
        datos = json.loads(_texto(ruta))
    except json.JSONDecodeError:
        return []
    return datos.get("apps", [])


def asincronia() -> dict:
    entrypoint = _texto(RAIZ / "docker" / "django" / "entrypoint.py")
    roles = sorted(set(re.findall(r'SERVICE_ROLE_[A-Z_]+ = "([a-z_]+)"', entrypoint)))

    def servicios_de(nombre: str) -> list[str]:
        contenido = _texto(RAIZ / nombre)
        # Cortar antes del bloque de volumenes: sus claves tienen la misma sangria.
        corte = re.search(r"^volumes:", contenido, re.M)
        if corte:
            contenido = contenido[: corte.start()]
        return re.findall(r"^  ([a-z_]+):", contenido, re.M)

    servicios = servicios_de("docker-compose.yml")
    servicios_celery = servicios_de("docker-compose.celery.yml")

    return {
        "roles_contenedor": roles,
        "servicios_compose": servicios,
        "servicios_celery": servicios_celery,
    }


def contratos_importlinter() -> list[dict]:
    contenido = _texto(RAIZ / ".importlinter")
    contratos = []
    for bloque in re.findall(
        r"\[importlinter:contract:([^\]]+)\](.*?)(?=\n\[|\Z)", contenido, re.S
    ):
        clave, cuerpo = bloque
        nombre = re.search(r"^name\s*=\s*(.+)$", cuerpo, re.M)
        excepciones = [
            linea.strip()
            for linea in re.search(r"ignore_imports\s*=(.*)$", cuerpo, re.S).group(1).split("\n")
            if linea.strip() and not linea.strip().startswith("#")
        ] if "ignore_imports" in cuerpo else []
        contratos.append(
            {
                "id": clave,
                "nombre": nombre.group(1).strip() if nombre else clave,
                "excepciones": excepciones,
            }
        )
    return contratos


# --------------------------------------------------------------------------- #
# Ensamblado
# --------------------------------------------------------------------------- #


def zona_de(app: str) -> str:
    for zona in ZONAS:
        if app in zona["apps"]:
            return zona["id"]
    return "sin_clasificar"


def construir() -> dict:
    instaladas = apps_instaladas()
    apps = instaladas + [p for p in PAQUETES_EXTRA if (RAIZ / p).is_dir() and p not in instaladas]

    rutas = rutas_montadas()
    planos = auth_de_apis(apps)
    aristas, peso = aristas_de_imports(apps)
    mapa_urls = nombres_de_url(apps)
    menu = menu_lateral(mapa_urls)

    menu_por_app: dict[str, list[dict]] = {}
    for grupo in menu:
        for item in grupo["items"]:
            if item["app"]:
                menu_por_app.setdefault(item["app"], []).append(
                    {
                        "label": item["label"],
                        "grupo": grupo["label"],
                        "ruta": item["ruta"],
                        "permisos": item["permisos"],
                    }
                )

    entrantes: dict[str, dict[str, int]] = {a: {"api": 0, "internal": 0} for a in apps}
    salientes: dict[str, dict[str, int]] = {a: {"api": 0, "internal": 0} for a in apps}
    for arista in aristas:
        salientes[arista["src"]][arista["kind"]] += 1
        entrantes[arista["dst"]][arista["kind"]] += 1

    modulos = []
    for app in apps:
        modulos.append(
            {
                "id": app,
                "nombre": NOMBRES.get(app, app.replace("_", " ").capitalize()),
                "zona": zona_de(app),
                "instalada": app in instaladas,
                "rutas_web": rutas.get(app, {}).get("web", []),
                "rutas_api": rutas.get(app, {}).get("api", []),
                "planos_api": planos.get(app, []),
                "menu": menu_por_app.get(app, []),
                "archivos": peso.get(app, {}).get("archivos", 0),
                "lineas": peso.get(app, {}).get("lineas", 0),
                "deps_out": salientes.get(app, {"api": 0, "internal": 0}),
                "deps_in": entrantes.get(app, {"api": 0, "internal": 0}),
                "tiene_fachada": (RAIZ / app / "api.py").exists(),
            }
        )

    # Campos explicitos: el registro de PWA trae metadata de despliegue
    # (ssh_identity, proyecto Compose, puertos internos) que no va al grafo.
    lista_pwas = []
    for app_pwa in pwas():
        identificador = app_pwa.get("id", "")
        lista_pwas.append(
            {
                "id": identificador,
                "repository": app_pwa.get("repository", ""),
                "canonical_path": app_pwa.get("canonical_path", ""),
                "legacy_path": app_pwa.get("legacy_path", ""),
                "enabled": app_pwa.get("enabled", False),
                "consume": [
                    {"modulo": m, "plano": plano, "certeza": certeza, "evidencia": evidencia}
                    for m, plano, certeza, evidencia in CONSUMO_PWA.get(identificador, [])
                ],
            }
        )

    return {
        "generado": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "commit": _git("rev-parse", "--short", "HEAD"),
        "rama": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "zonas": [{k: v for k, v in z.items() if k != "apps"} for z in ZONAS],
        "modulos": modulos,
        "aristas": aristas,
        "menu": menu,
        "pwas": lista_pwas,
        "externos": EXTERNOS,
        "asincronia": asincronia(),
        "contratos": contratos_importlinter(),
        "totales": {
            "apps": len(modulos),
            "aristas": len(aristas),
            "aristas_api": sum(1 for a in aristas if a["kind"] == "api"),
            "aristas_internals": sum(1 for a in aristas if a["kind"] == "internal"),
            "lineas": sum(m["lineas"] for m in modulos),
            "items_menu": sum(len(g["items"]) for g in menu),
        },
    }


def escribir(ruta: Path, contenido: str) -> Path:
    """Escribe por archivo temporal y reemplazo atomico.

    Si el proceso muere a mitad de escritura, el consumidor sigue viendo la
    ultima salida completa en vez de un JSON truncado que parece valido.
    """
    ruta.parent.mkdir(parents=True, exist_ok=True)
    temporal = ruta.with_suffix(ruta.suffix + ".tmp")
    temporal.write_text(contenido, encoding="utf-8")
    os.replace(temporal, ruta)
    return ruta


def documento_autocontenido(css: str, js: str, grafo_json: str) -> str:
    """HTML de una sola pieza, para leer el mapa fuera de SISOC."""
    seguro = grafo_json.replace("</", "<\\/")
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Arquitectura de SISOC</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FUENTES_CSS}">
<style>
{css}
</style>
</head>
<body>
<div id="mapa"></div>
<script>window.__GRAFO_SISOC__ = {seguro};</script>
<script>
{js}
</script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--docs",
        action="store_true",
        help="Ademas del grafo de runtime, actualiza los artefactos versionados de docs/.",
    )
    args = parser.parse_args()

    grafo = construir()
    json_compacto = json.dumps(grafo, ensure_ascii=False, separators=(",", ":"))

    escritos = [escribir(SALIDA_RUNTIME / "grafo.json", json_compacto)]

    if args.docs:
        css = _texto(FUENTE_VISOR / "mapa.css")
        js = _texto(FUENTE_VISOR / "mapa.js")
        if not css or not js:
            raise SystemExit(f"Falta el visor (mapa.css / mapa.js) en {FUENTE_VISOR}.")
        escritos.append(
            escribir(
                SALIDA_DOCS / "grafo_sisoc.json",
                json.dumps(grafo, ensure_ascii=False, indent=2) + "\n",
            )
        )
        escritos.append(
            escribir(
                SALIDA_DOCS / "mapa_sisoc.html",
                documento_autocontenido(css, js, json_compacto),
            )
        )

    for ruta in escritos:
        print(f"  {ruta.relative_to(RAIZ)}")

    t = grafo["totales"]
    print(
        f"apps={t['apps']} aristas={t['aristas']} "
        f"(api={t['aristas_api']} internals={t['aristas_internals']}) "
        f"menu={t['items_menu']} lineas={t['lineas']}"
    )


if __name__ == "__main__":
    main()
