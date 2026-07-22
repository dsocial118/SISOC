"""Regresiones de renderizado para accesos e informes complementarios."""

import re
from types import SimpleNamespace

import pytest
from django.contrib.auth.models import AnonymousUser
from django.template.loader import render_to_string
from django.test import RequestFactory

pytestmark = pytest.mark.django_db


def _campo(identificador, nombre, valor):
    return {"identificador": identificador, "nombre": nombre, "valor": valor}


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
                {
                    "titulo": "Grupo uno",
                    "tipo": "campos",
                    "campos": [_campo("campo_uno", "Campo uno", "Valor uno")],
                },
                {
                    "titulo": "Grupo dos",
                    "tipo": "campos",
                    "campos": [_campo("campo_dos", "Campo dos", "Valor dos")],
                },
            ],
            "campos_modificados_existentes": {},
            "origen_acompanamiento": False,
        },
        request=request,
    )

    for identificador in ("campo_uno", "campo_dos"):
        assert html.count(f'id="check_{identificador}"') == 1
        assert html.count(f'for="check_{identificador}"') == 1
        assert html.count(f'id="input_{identificador}"') == 1
        assert html.count(f'id="campo_{identificador}"') == 1


def test_informe_complementario_renderiza_matrices_de_prestaciones():
    request = RequestFactory().get("/informe-complementario/")
    request.csp_nonce = "test-nonce"
    request.user = AnonymousUser()
    admision = SimpleNamespace(
        id=11,
        comedor_id=5,
        comedor=SimpleNamespace(nombre="Comedor prueba"),
    )
    dias = (
        "lunes",
        "martes",
        "miercoles",
        "jueves",
        "viernes",
        "sabado",
        "domingo",
    )
    solicitudes_filas = [
        {
            "titulo": comida.capitalize(),
            "campos": [
                _campo(
                    f"solicitudes_{comida}_{dia}",
                    f"Solicitudes {comida} {dia}",
                    indice,
                )
                for indice, dia in enumerate(dias, start=1)
            ],
        }
        for comida in ("desayuno", "almuerzo", "merienda", "cena")
    ]
    campos_por_grupo = [
        {
            "titulo": "Solicitudes",
            "tipo": "matriz",
            "identificador": "solicitudes",
            "filas": solicitudes_filas,
        },
        {
            "titulo": "Prestaciones Aprobadas",
            "tipo": "matriz",
            "identificador": "prestaciones_aprobadas",
            "filas": [
                {
                    "titulo": "Almuerzo",
                    "campos": [
                        _campo(
                            "aprobadas_almuerzo_lunes",
                            "Aprobadas almuerzo lunes",
                            8,
                        )
                    ],
                }
            ],
        },
        {
            "titulo": "Prestaciones aprobadas en el último convenio",
            "tipo": "matriz",
            "identificador": "prestaciones_ultimo_convenio",
            "filas": [
                {
                    "titulo": "Merienda",
                    "campos": [
                        _campo(
                            "aprobadas_ultimo_convenio_merienda_lunes",
                            "Prestación anterior",
                            7,
                        )
                    ],
                }
            ],
        },
    ]

    html = render_to_string(
        "admisiones/informe_tecnico_complementario_detalle.html",
        {
            "admision": admision,
            "campos_agrupados": campos_por_grupo,
            "campos_modificados_existentes": {},
            "origen_acompanamiento": False,
        },
        request=request,
    )

    for identificador in (
        "solicitudes",
        "prestaciones_aprobadas",
        "prestaciones_ultimo_convenio",
    ):
        assert f'id="matriz-{identificador}"' in html
    for encabezado in ("Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"):
        assert html.count(f"<th scope=\"col\">{encabezado}</th>") == 3

    tabla_solicitudes = re.search(
        r'<table id="matriz-solicitudes".*?</table>', html, flags=re.DOTALL
    ).group()
    for comida in ("desayuno", "almuerzo", "merienda", "cena"):
        fila = re.search(
            rf"<tr>\s*<th[^>]*>\s*{comida.capitalize()}\s*</th>(.*?)</tr>",
            tabla_solicitudes,
            flags=re.DOTALL,
        ).group(1)
        assert re.findall(r'id="check_(solicitudes_[^"]+)"', fila) == [
            f"solicitudes_{comida}_{dia}" for dia in dias
        ]


def test_informe_complementario_con_origen_acompanamiento_enlaza_breadcrumb_al_convenio():
    request = RequestFactory().get("/informe-complementario/?origen=acompanamiento")
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
            "campos_agrupados": [],
            "campos_modificados_existentes": {},
            "origen_acompanamiento": True,
        },
        request=request,
    )

    assert "/acompanamientos/acompanamiento/5/detalle/?admision_id=11" in html


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
