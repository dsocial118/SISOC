"""Cobertura de la categorización visible en el legajo (#2163)."""

from django.urls import reverse

from comedores.models import Comedor


def test_legajo_muestra_categoria_y_detalle_de_otra_opcion(
    client_logged_fixture, comedor_fixture
):
    comedor_fixture.categoria_espacio_comunitario = Comedor.CATEGORIA_ESPACIO_OTRA
    comedor_fixture.categoria_espacio_comunitario_otra = "Mutual vecinal"
    comedor_fixture.save(
        update_fields=[
            "categoria_espacio_comunitario",
            "categoria_espacio_comunitario_otra",
        ]
    )

    response = client_logged_fixture.get(
        reverse("comedor_detalle", kwargs={"pk": comedor_fixture.pk})
    )

    assert response.status_code == 200
    assert "Otra (especificar)" in response.content.decode()
    assert "Mutual vecinal" in response.content.decode()
