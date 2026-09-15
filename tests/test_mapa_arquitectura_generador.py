"""Caracterización del generador del mapa de arquitectura.

El generador lee `config/settings.py`, `config/urls.py` y el template del menú
lateral con regex y AST. Si alguien reformatea esos archivos, el parser no
explota: devuelve datos incompletos en silencio y el mapa pasa a mentir. Estos
tests existen para que eso falle ruidosamente en CI.

No tocan la base ni escriben archivos: sólo ejercitan las funciones de lectura.
"""

import importlib.util
from pathlib import Path

import pytest

pytestmark = pytest.mark.smoke

RAIZ = Path(__file__).resolve().parents[1]
GENERADOR = RAIZ / "scripts" / "arquitectura" / "generar_mapa.py"


@pytest.fixture(scope="module")
def generador():
    spec = importlib.util.spec_from_file_location("generar_mapa", GENERADOR)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


@pytest.fixture(scope="module")
def apps(generador):
    return generador.apps_instaladas()


@pytest.fixture(scope="module")
def menu(generador, apps):
    return generador.menu_lateral(generador.nombres_de_url(apps))


def test_lee_las_apps_propias_de_installed_apps(apps):
    assert {"core", "users", "comedores", "celiaquia", "VAT", "pas"} <= set(apps)
    assert "django" not in apps
    assert "rest_framework" not in apps


def test_toda_app_instalada_tiene_zona_en_el_mapa(generador, apps):
    """Una app nueva sin ubicar cae en 'sin_clasificar' y hay que ubicarla."""
    sin_zona = [app for app in apps if generador.zona_de(app) == "sin_clasificar"]
    assert not sin_zona, (
        "Estas apps no están en ninguna zona del mapa: "
        f"{sin_zona}. Agregalas a ZONAS en {GENERADOR.name}."
    )


def test_mapea_los_prefijos_de_api_a_su_app(generador):
    rutas = generador.rutas_montadas()
    assert "/api/comedores/" in rutas["comedores"]["api"]
    assert "/api/territorial/" in rutas["comedores"]["api"]
    assert "/api/pwa/" in rutas["pwa"]["api"]


def test_distingue_los_planos_de_autenticacion(generador, apps):
    """Token DRF es el plano móvil; API key el server-to-server.

    Una API puede combinarlos: `relevamientos` usa `HasAPIKeyOrToken`, así que
    debe aparecer en los dos. Detectar una sola señal por app ocultaba eso.
    """
    planos = generador.auth_de_apis(apps)
    assert "token" in planos["comedores"]
    assert "token" in planos["pwa"]
    assert planos["ticketera"] == ["api_key"]
    assert planos["VAT"] == ["api_key"]
    assert {"api_key", "token"} <= set(planos["relevamientos"])


def test_separa_fachada_publica_de_import_de_internals(generador, apps):
    aristas, peso = generador.aristas_de_imports(apps)
    por_clave = {(a["src"], a["dst"]): a for a in aristas}

    # dashboard consume comedores sólo por su fachada (contrato declarado).
    assert por_clave[("dashboard", "comedores")]["kind"] == "api"
    assert peso["comedores"]["lineas"] > 0


def test_ve_dependencias_que_import_linter_no_puede_ver(generador, apps):
    """El AST alcanza namespace packages; grimp no.

    `.importlinter` lo documenta como limitación conocida: sólo analiza paquetes
    con `__init__.py`, así que `historial.services` queda fuera de su grafo. Por
    eso el contrato `core-no-domains` no detecta `core/views.py -> historial`,
    que sí viola lo declarado y no está en el baseline de `ignore_imports`.

    Si algún día se corta ese import (o `historial/services/__init__.py` aparece
    y el linter empieza a verlo), este test falla y hay que actualizarlo.
    """
    aristas, _ = generador.aristas_de_imports(apps)
    desde_core = {a["dst"] for a in aristas if a["src"] == "core"}

    assert "historial" in desde_core
    # El resto de lo que importa core es núcleo compartido, no dominio.
    assert desde_core - {"historial"} <= {"users", "iam"}


def test_un_enlace_suelto_no_queda_dentro_del_grupo_anterior(menu):
    """"Mi cuenta" es hermano de los grupos, no un item de Legajos."""
    grupos_de_mi_cuenta = [
        g["label"] for g in menu for i in g["items"] if i["url_name"] == "mi_cuenta"
    ]
    assert grupos_de_mi_cuenta == ["Mi cuenta"]


def test_el_menu_lateral_se_parsea_completo(menu):
    grupos_con_items = [g for g in menu if g["items"]]
    assert len(grupos_con_items) >= 5

    items = [item for grupo in menu for item in grupo["items"]]
    assert len(items) >= 50

    sin_etiqueta = [i["url_name"] for i in items if not i["label"]]
    assert not sin_etiqueta, f"Items de menú sin etiqueta legible: {sin_etiqueta}"

    sin_app = [i["url_name"] for i in items if not i["app"]]
    assert not sin_app, f"Items de menú sin app resuelta: {sin_app}"


def test_el_menu_conserva_la_jerarquia_de_desplegables(menu):
    """La ruta de un item la dan los <a href="#"> que lo contienen."""
    por_url = {i["url_name"]: i for g in menu for i in g["items"]}

    assert por_url["comedores"]["ruta"] == ["Comedores"]
    assert por_url["admisiones_tecnicos_listar"]["ruta"] == [
        "Comedores",
        "Admisión - Comedores",
    ]
    assert por_url["vat_comision_list"]["ruta"] == ["INET", "Oferta Educativa"]
    assert por_url["pas_panel_control"]["ruta"] == ["PAS"]


def test_el_menu_hereda_los_permisos_de_los_if_que_lo_envuelven(menu):
    por_url = {i["url_name"]: i for g in menu for i in g["items"]}

    assert "comedores.view_comedor" in por_url["comedores"]["permisos"]
    # Hereda el gate del desplegable que lo contiene, no sólo el propio.
    tecnicos = por_url["admisiones_tecnicos_listar"]["permisos"]
    assert "admisiones.view_admision" in tecnicos
    assert "comedores.view_comedor" in tecnicos
    # Fuera de todo {% if %} no debe arrastrar permisos de un bloque anterior.
    assert por_url["mi_cuenta"]["permisos"] == []
    # Un gate por is_superuser no es un permiso de Django, pero es el requisito.
    assert "is_superuser" in por_url["papelera_list"]["permisos"]


def test_el_grafo_no_se_publica_como_estatico(generador):
    """El grafo describe permisos y rutas: Nginx sirve /static/ sin auth.

    Tampoco puede escribirse dentro del checkout: `deploy_refresh.sh` aborta el
    despliegue si encuentra cambios locales en archivos versionados, y el
    generador corre en cada arranque.
    """
    assert not (RAIZ / "static" / "arquitectura" / "grafo.json").exists()
    assert (RAIZ / "static" / "arquitectura" / "mapa.js").exists()
    assert generador.SALIDA_RUNTIME == RAIZ / "var" / "arquitectura"
    assert "/var/" in (RAIZ / ".gitignore").read_text(encoding="utf-8")


def test_el_grafo_no_arrastra_metadata_de_despliegue(generador):
    """El registro de PWA trae ssh_identity y puertos internos; no van al grafo."""
    grafo = generador.construir()
    campos = {clave for pwa in grafo["pwas"] for clave in pwa}

    assert "ssh_identity" not in campos
    assert "port" not in campos
    assert "project" not in campos
    assert {"id", "repository", "canonical_path", "consume"} <= campos
