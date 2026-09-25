"""Boton "Volver" unificado en todas las pantallas (issue #2460)."""

import pathlib
import re

import pytest
from django.contrib.auth.models import User
from django.urls import reverse

RAIZ = pathlib.Path(__file__).resolve().parent.parent

EXTIENDE_MAIN = 'extends "includes/main.html"'

# Pantallas de error: su "volver al inicio" es un link dentro de un parrafo.
EXCLUIDOS = {
    "templates/403.html",
    "templates/404.html",
    "templates/500.html",
}

ANCHOR_RE = re.compile(r"<a\b[^>]*>.*?</a>", re.I | re.S)
SUBMIT_RE = re.compile(r'type="submit"', re.I)
VENTANA = 400


def _templates_de_pantalla():
    for ruta in RAIZ.rglob("*.html"):
        partes = ruta.parts
        if "node_modules" in partes or "static_root" in partes:
            continue
        relativa = ruta.relative_to(RAIZ).as_posix()
        if relativa in EXCLUIDOS:
            continue
        contenido = ruta.read_text(encoding="utf-8", errors="ignore")
        if EXTIENDE_MAIN in contenido:
            yield relativa, contenido


def _es_boton_volver(html):
    clase = re.search(r'class="([^"]*)"', html, re.I)
    if not clase or "btn" not in clase.group(1):
        return False
    texto = " ".join(re.sub(r"<[^>]+>", " ", html).split())
    return bool(re.match(r"^Volver\b", texto, re.I)) and "{%" not in texto


def test_ninguna_pantalla_declara_su_propio_boton_volver_de_navegacion():
    """El "Volver" lo pone includes/main.html: nadie lo vuelve a declarar.

    Se permite el "Volver" que actua como cancelar de un formulario (el que
    convive con un submit), porque no es navegacion sino descartar la edicion.
    """

    sobrantes = []
    for relativa, contenido in _templates_de_pantalla():
        for match in ANCHOR_RE.finditer(contenido):
            if not _es_boton_volver(match.group(0)):
                continue
            contexto = contenido[
                max(0, match.start() - VENTANA) : match.end() + VENTANA
            ]
            if SUBMIT_RE.search(contexto):
                continue
            linea = contenido[: match.start()].count("\n") + 1
            sobrantes.append(f"{relativa}:{linea}")

    assert not sobrantes, (
        "Estas pantallas declaran su propio boton 'Volver' de navegacion; "
        "el unificado ya lo renderiza includes/main.html:\n  " + "\n  ".join(sobrantes)
    )


def test_el_componente_no_vive_mas_en_el_search_bar():
    search_bar = (RAIZ / "templates/components/search_bar.html").read_text(
        encoding="utf-8"
    )

    assert "poncho-volver" not in search_bar
    assert "back_url" not in search_bar


@pytest.mark.django_db
def test_una_pantalla_cualquiera_renderiza_el_boton(client):
    admin = User.objects.create_superuser("admin_volver", "volver@test.com", "test")
    client.force_login(admin)

    contenido = client.get(reverse("comedores")).content.decode()

    assert "data-sisoc-volver" in contenido
    assert "sisoc-volver-barra" in contenido
    assert "btn btn-secondary btn-sm sisoc-volver" in contenido


@pytest.mark.django_db
def test_la_pantalla_de_inicio_lo_oculta(client):
    admin = User.objects.create_superuser("admin_inicio", "inicio@test.com", "test")
    client.force_login(admin)

    response = client.get(reverse("inicio"))

    assert response.status_code == 200
    assert response.context["ocultar_volver"] is True
    assert "data-sisoc-volver" not in response.content.decode()


@pytest.mark.django_db
def test_la_vista_puede_fijar_un_destino_por_defecto(client):
    from django.template.loader import render_to_string

    html = render_to_string(
        "components/back_button.html", {"volver_url": "/comedores/"}
    )

    assert 'href="/comedores/"' in html
    assert 'data-volver-fallback="/comedores/"' in html


def test_el_context_processor_define_los_defaults():
    from core.context_processors import boton_volver

    defaults = boton_volver(None)

    assert defaults == {
        "ocultar_volver": False,
        "volver_url": "",
        "volver_texto": "Volver",
    }
