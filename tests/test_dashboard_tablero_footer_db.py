"""El footer no debe quedar tapado por un tablero embebido.

El iframe estaba en ``position:absolute`` dentro de un contenedor sin alto: el
contenedor colapsaba a 0, el tablero quedaba fuera de flujo y se dibujaba
encima de la barra de acciones y del footer. Al pisarlos capturaba la rueda del
mouse y la página quedaba trabada al llegar al final.

En esta pantalla el footer se sigue renderizando igual que en el resto del
sitio: lo oculta `tableroEmbed.css`, que solo se carga acá.
"""

import pytest
from django.template import engines
from django.urls import reverse

from dashboard.models import Tablero

pytestmark = pytest.mark.django_db


@pytest.fixture(name="tablero")
def tablero_fixture():
    return Tablero.objects.create(
        nombre="DataCalle General Chaco",
        slug="datacalle-general-chaco",
        url="https://lookerstudio.google.com/embed/reporting/abc",
        activo=True,
    )


def _get(client, superuser, tablero):
    client.force_login(superuser)
    respuesta = client.get(reverse("dashboard_tablero", kwargs={"slug": tablero.slug}))
    assert respuesta.status_code == 200, respuesta.status_code
    return respuesta.content.decode()


def test_el_footer_se_renderiza_pero_queda_oculto(client, superuser, tablero):
    """El footer sigue en el DOM; la hoja de estilos de la página lo esconde."""
    html = _get(client, superuser, tablero)

    assert "app-footer" in html, "el footer no debe removerse del DOM"
    assert "tableroEmbed.css" in html, "falta la hoja que lo oculta"


def test_la_regla_que_oculta_el_footer_le_gana_a_main_css():
    """Sin igualar la especificidad de `main.css` el footer seguiría visible."""
    from pathlib import Path as _Path

    css = _Path("static/custom/css/tableroEmbed.css").read_text(encoding="utf-8")
    regla = css.split(".app-wrapper .app-footer,", 1)[1].split("}", 1)[0]

    assert "footer.app-footer" in regla
    assert "display: none" in regla


def test_el_iframe_queda_dentro_del_flujo(client, superuser, tablero):
    """Regresión: fuera de flujo tapaba el footer y trababa el scroll."""
    html = _get(client, superuser, tablero)

    assert "position:absolute" not in html
    assert 'class="tablero-embed"' in html
    assert 'class="tablero-embed-frame"' in html
    assert "tableroEmbed.css" in html


def test_la_barra_de_acciones_sigue_accesible(client, superuser, tablero):
    """Antes el iframe la tapaba, aunque estuviera en el DOM."""
    html = _get(client, superuser, tablero)

    assert "Abrir tablero en una pestana nueva" in html


def test_un_tablero_sin_url_sigue_mostrando_el_mensaje(client, superuser):
    tablero = Tablero.objects.create(
        nombre="En confeccion", slug="en-confeccion", activo=True
    )
    html = _get(client, superuser, tablero)

    assert "Tablero en confecci" in html
    assert "app-footer" in html


def test_el_resto_del_sitio_no_carga_la_hoja_que_oculta(rf, superuser):
    """El layout compartido queda intacto: el footer se ve como siempre."""
    plantilla = engines["django"].from_string(
        '{% extends "includes/base.html" %}{% block content %}hola{% endblock %}'
    )
    request = rf.get("/x")
    request.user = superuser
    request.csp_nonce = "n"

    html = plantilla.render({"request": request}, request)

    assert "app-footer" in html
    assert "tableroEmbed.css" not in html, "la regla no debe filtrarse a otras páginas"
