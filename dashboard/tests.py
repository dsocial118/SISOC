from pathlib import Path

from django.test import RequestFactory

from dashboard.models import Tablero
from dashboard.templatetags.dashboard_tags import tableros_para_sidebar


def _request_para(user, path="/"):
    request = RequestFactory().get(path)
    request.user = user
    return request


def test_tablero_convierte_url_compartible_de_lookerstudio_a_embed():
    tablero = Tablero(
        nombre="FCH Google Analytics",
        slug="fch-google-analytics",
        url=(
            "https://lookerstudio.google.com/u/0/reporting/"
            "7feb7647-eadb-4fd8-910d-11a794227234"
        ),
    )

    assert tablero.usa_url_compartible_looker_studio() is True
    assert (
        tablero.get_embed_url() == "https://lookerstudio.google.com/embed/reporting/"
        "7feb7647-eadb-4fd8-910d-11a794227234"
    )


def test_dashboard_tablero_renderiza_iframe_con_url_embed_de_lookerstudio(
    admin_client,
):
    tablero = Tablero.objects.create(
        nombre="FCH Google Analytics",
        slug="fch-google-analytics",
        url=(
            "https://lookerstudio.google.com/u/0/reporting/"
            "7feb7647-eadb-4fd8-910d-11a794227234"
        ),
        activo=True,
        permisos=["dashboard.view_dashboard"],
    )

    response = admin_client.get(tablero.get_absolute_url())
    content = response.content.decode()

    assert f'src="{tablero.get_embed_url()}"' in content
    assert 'target="_blank"' in content
    assert "File &gt; Embed report" in content


def test_tableros_para_sidebar_agrupa_por_grupo_menu(db, django_user_model):
    admin = django_user_model.objects.create_superuser(
        "admin_tab", "admin_tab@example.com", "x"
    )
    Tablero.objects.create(
        nombre="Aduana", slug="aduana", grupo_menu="Aduana", orden=1, activo=True
    )
    Tablero.objects.create(
        nombre="Aduana Ejecutivo",
        slug="aduana-ejecutivo",
        grupo_menu="Aduana",
        orden=2,
        activo=True,
    )
    suelto = Tablero.objects.create(
        nombre="Prestación Alimentar", slug="prestacion", orden=3, activo=True
    )

    items = tableros_para_sidebar({"request": _request_para(admin)})

    assert [item["tipo"] for item in items] == ["grupo", "single"]
    grupo = items[0]
    assert grupo["nombre"] == "Aduana"
    assert [hijo["nombre"] for hijo in grupo["hijos"]] == ["Aduana", "Aduana Ejecutivo"]
    assert items[1]["nombre"] == "Prestación Alimentar"
    assert items[1]["url"] == suelto.get_absolute_url()


def test_tableros_para_sidebar_colapsa_grupo_de_un_solo_tablero(db, django_user_model):
    admin = django_user_model.objects.create_superuser(
        "admin_tab2", "admin_tab2@example.com", "x"
    )
    Tablero.objects.create(
        nombre="Solo", slug="solo", grupo_menu="Programa X", orden=1, activo=True
    )

    items = tableros_para_sidebar({"request": _request_para(admin)})

    assert len(items) == 1
    assert items[0]["tipo"] == "single"
    assert items[0]["nombre"] == "Solo"


def test_tableros_para_sidebar_marca_activo_por_path(db, django_user_model):
    admin = django_user_model.objects.create_superuser(
        "admin_tab3", "admin_tab3@example.com", "x"
    )
    tablero = Tablero.objects.create(
        nombre="Comedores Interno", slug="comedores-interno", orden=1, activo=True
    )

    items = tableros_para_sidebar(
        {"request": _request_para(admin, tablero.get_absolute_url())}
    )

    assert items[0]["activo"] is True
