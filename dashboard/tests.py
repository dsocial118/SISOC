from pathlib import Path

from dashboard.models import Tablero


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

    assert 'src="{{ tablero.get_embed_url }}"' in content
    assert 'target="_blank"' in content
    assert "File &gt; Embed report" in content
