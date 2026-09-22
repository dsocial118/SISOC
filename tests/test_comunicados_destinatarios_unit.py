"""Seleccion personalizada de destinatarios de comunicados (issue #2505)."""

import json

import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from comedores.models import Comedor
from comunicados import services_destinatarios
from comunicados.models import Comunicado, SubtipoComunicado, TipoComunicado
from core.models import Provincia
from organizaciones.models import Organizacion, TipoEntidad

pytestmark = pytest.mark.django_db


def _filtros(items):
    return json.dumps({"logic": "AND", "items": items})


def _form_data(**overrides):
    data = {
        "titulo": "Comunicado con destinatarios",
        "cuerpo": "Contenido",
        "tipo": TipoComunicado.EXTERNO,
        "subtipo": SubtipoComunicado.COMEDORES,
        "fecha_vencimiento": "",
        "adjuntos-TOTAL_FORMS": "0",
        "adjuntos-INITIAL_FORMS": "0",
        "adjuntos-MIN_NUM_FORMS": "0",
        "adjuntos-MAX_NUM_FORMS": "1000",
    }
    data.update(overrides)
    return data


@pytest.fixture
def admin(client):
    usuario = User.objects.create_superuser("admin_dest", "dest@test.com", "test")
    client.force_login(usuario)
    return usuario


def test_buscar_comedores_aplica_filtros_combinables(client, admin):
    buenos_aires = Provincia.objects.create(nombre="Buenos Aires")
    cordoba = Provincia.objects.create(nombre="Cordoba")
    objetivo = Comedor.objects.create(nombre="Comedor Sur", provincia=buenos_aires)
    Comedor.objects.create(nombre="Comedor Sur", provincia=cordoba)
    Comedor.objects.create(nombre="Otro espacio", provincia=buenos_aires)

    response = client.get(
        reverse("comunicados_destinatarios_buscar", args=["comedores"]),
        {
            "filters": _filtros(
                [
                    {"field": "nombre", "op": "contains", "value": "Comedor Sur"},
                    {"field": "provincia", "op": "contains", "value": "Buenos"},
                ]
            )
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert [item["id"] for item in payload["results"]] == [objetivo.pk]
    assert payload["results"][0]["detalle"] == "Buenos Aires"


def test_buscar_organizaciones_usa_los_filtros_del_listado(client, admin):
    tipo = TipoEntidad.objects.create(nombre="Asociacion civil")
    objetivo = Organizacion.objects.create(nombre="Manos Unidas", tipo_entidad=tipo)
    Organizacion.objects.create(nombre="Manos Libres")

    response = client.get(
        reverse("comunicados_destinatarios_buscar", args=["organizaciones"]),
        {
            "filters": _filtros(
                [{"field": "tipo_entidad", "op": "eq", "value": "Asociacion civil"}]
            )
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert [item["id"] for item in payload["results"]] == [objetivo.pk]


def test_buscar_pagina_los_resultados(client, admin, monkeypatch):
    monkeypatch.setattr(services_destinatarios, "PAGE_SIZE", 2)
    for indice in range(5):
        Comedor.objects.create(nombre=f"Comedor {indice:02d}")

    primera = client.get(
        reverse("comunicados_destinatarios_buscar", args=["comedores"]),
        {"filters": _filtros([])},
    ).json()
    segunda = client.get(
        reverse("comunicados_destinatarios_buscar", args=["comedores"]),
        {"filters": _filtros([]), "page": "2"},
    ).json()

    assert primera["total"] == 5
    assert len(primera["results"]) == 2
    assert primera["has_more"] is True
    assert segunda["page"] == 2
    assert [item["nombre"] for item in segunda["results"]] == [
        "Comedor 02",
        "Comedor 03",
    ]


def test_seleccionar_todos_devuelve_los_ids_que_matchean(client, admin):
    incluido = Comedor.objects.create(nombre="Comedor incluido")
    Comedor.objects.create(nombre="Excluido")

    response = client.get(
        reverse("comunicados_destinatarios_todos", args=["comedores"]),
        {"filters": _filtros([{"field": "nombre", "op": "contains", "value": "incl"}])},
    )

    payload = response.json()
    assert payload["truncado"] is False
    assert [item["id"] for item in payload["results"]] == [incluido.pk]


def test_seleccionar_todos_corta_cuando_supera_el_tope(client, admin, monkeypatch):
    monkeypatch.setattr(services_destinatarios, "MAX_SELECCION_MASIVA", 1)
    Comedor.objects.create(nombre="Comedor uno")
    Comedor.objects.create(nombre="Comedor dos")

    payload = client.get(
        reverse("comunicados_destinatarios_todos", args=["comedores"]),
        {"filters": _filtros([])},
    ).json()

    assert payload["truncado"] is True
    assert payload["results"] == []
    assert payload["total"] == 2


def test_buscar_respeta_el_alcance_del_usuario(client, admin, monkeypatch):
    visible = Comedor.objects.create(nombre="Comedor visible")
    Comedor.objects.create(nombre="Comedor ajeno")
    monkeypatch.setattr(
        services_destinatarios,
        "get_ids_comedores_del_usuario",
        lambda user: (visible.pk,),
    )

    payload = client.get(
        reverse("comunicados_destinatarios_buscar", args=["comedores"]),
        {"filters": _filtros([])},
    ).json()

    assert [item["id"] for item in payload["results"]] == [visible.pk]


def test_universo_desconocido_devuelve_404(client, admin):
    response = client.get(
        reverse("comunicados_destinatarios_buscar", args=["ciudadanos"])
    )

    assert response.status_code == 404


def test_buscar_exige_permiso_de_creacion(client):
    sin_permisos = User.objects.create_user("sin_permisos_dest", password="test")
    client.force_login(sin_permisos)

    response = client.get(
        reverse("comunicados_destinatarios_buscar", args=["comedores"])
    )

    assert response.status_code == 403


def test_formulario_guarda_los_destinatarios_elegidos(client, admin):
    uno = Comedor.objects.create(nombre="Comedor uno")
    dos = Comedor.objects.create(nombre="Comedor dos")

    response = client.post(
        reverse("comunicados_crear"),
        _form_data(comedores=[str(uno.pk), str(dos.pk)]),
    )

    assert response.status_code == 302
    comunicado = Comunicado.objects.get(titulo="Comunicado con destinatarios")
    assert set(comunicado.comedores.values_list("pk", flat=True)) == {uno.pk, dos.pk}


def test_el_formulario_no_renderiza_todo_el_universo_en_un_select(client, admin):
    Comedor.objects.create(nombre="Comedor listado")

    response = client.get(reverse("comunicados_crear"))
    contenido = response.content.decode()

    assert response.status_code == 200
    # El universo ya no se serializa en el HTML: el panel lo consulta por AJAX.
    assert "Comedor listado" not in contenido
    assert 'data-universo="comedores"' in contenido
    assert 'data-universo="organizaciones"' in contenido
    assert "destinatarios-filters-config" in contenido


def test_contexto_trae_config_urls_y_seleccion_previa(client, admin):
    comedor = Comedor.objects.create(nombre="Comedor elegido")
    comunicado = Comunicado.objects.create(
        titulo="Editable",
        cuerpo="Contenido",
        tipo=TipoComunicado.EXTERNO,
        subtipo=SubtipoComunicado.COMEDORES,
        usuario_creador=admin,
    )
    comunicado.comedores.add(comedor)

    response = client.get(reverse("comunicados_editar", kwargs={"pk": comunicado.pk}))
    ctx = response.context

    assert ctx["destinatarios_filters_config"]["comedores"]["fields"]
    assert ctx["destinatarios_filters_config"]["organizaciones"]["fields"]
    assert ctx["destinatarios_seleccionados"]["comedores"] == [
        {"id": comedor.pk, "nombre": "Comedor elegido"}
    ]
    assert ctx["destinatarios_urls"]["comedores"]["buscar"].endswith(
        "/comedores/buscar/"
    )


def test_las_secciones_se_muestran_en_el_orden_pedido(client, admin):
    contenido = client.get(reverse("comunicados_crear")).content.decode()

    orden = [
        contenido.index("Configuración"),
        contenido.index("Destinatarios"),
        contenido.index("Redacción"),
        contenido.index("Archivos Adjuntos"),
    ]

    assert orden == sorted(orden)
