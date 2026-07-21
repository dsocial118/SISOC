"""Regresiones de renderizado para accesos e informes complementarios."""

import re
from types import SimpleNamespace

import pytest
from django.contrib.auth.models import AnonymousUser
from django.template.loader import render_to_string
from django.test import RequestFactory

pytestmark = pytest.mark.django_db


def test_informe_complementario_renderiza_ids_unicos_en_dos_grupos():
    request = RequestFactory().get("/informe-complementario/")
    request.csp_nonce = "test-nonce"
    request.user = AnonymousUser()
    admision = SimpleNamespace(
        id=11,
        comedor_id=5,
        comedor=SimpleNamespace(nombre="Comedor prueba"),
    )

    html = render_to_string(
        "admisiones/informe_tecnico_complementario_detalle.html",
        {
            "admision": admision,
            "campos_agrupados": [
                ("Grupo uno", [("Campo uno", "Valor uno")]),
                ("Grupo dos", [("Campo dos", "Valor dos")]),
            ],
            "campos_modificados_existentes": {},
            "origen_acompanamiento": False,
        },
        request=request,
    )

    for grupo in (1, 2):
        assert html.count(f'id="check_{grupo}_1"') == 1
        assert html.count(f'for="check_{grupo}_1"') == 1
        assert html.count(f'id="input_{grupo}_1"') == 1
        assert html.count(f'id="campo_{grupo}_1"') == 1


def test_acompanamiento_renderiza_informe_en_columna_derecha():
    request = RequestFactory().get(
        "/acompanamientos/acompanamiento/5/detalle/?admision_id=17"
    )
    request.csp_nonce = "test-nonce"
    request.user = AnonymousUser()
    html = render_to_string(
        "acompañamiento_detail.html",
        {
            "comedor": SimpleNamespace(id=5, nombre="Comedor prueba"),
            "admision_id_activa": 17,
            "informe_tecnico_complementario": SimpleNamespace(id=70, tipo="base"),
        },
        request=request,
    )

    acciones = html[html.index('<div class="row justify-content-between">') :]
    assert re.search(
        r'<div class="col-auto">\s*<a [^>]*>\s*<i [^>]*></i>Informe Técnico Complementario',
        acciones,
    )
    assert "/base/70/" in acciones
    assert "admision_id=17" in acciones
