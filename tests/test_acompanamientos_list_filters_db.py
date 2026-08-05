"""Regresiones de filtros y exportacion del listado de acompanamientos."""

import json

import pytest
from django.urls import reverse
from django.test import RequestFactory

from acompanamientos.acompanamiento_service import AcompanamientoService
from admisiones.models.admisiones import Admision
from comedores.models import Comedor
from users.services import UserPermissionService


pytestmark = pytest.mark.django_db


def _filtros_por_estado(estado):
    return json.dumps(
        {
            "logic": "AND",
            "items": [{"field": "estado", "op": "eq", "value": estado}],
        }
    )


def _crear_comedor_con_dos_admisiones(nombre="Comedor con historial"):
    comedor = Comedor.objects.create(nombre=nombre)
    Admision.objects.create(
        comedor=comedor,
        activa=True,
        enviado_acompaniamiento=True,
        estado_admision="iniciada",
        num_expediente="EXP-ANTERIOR",
    )
    Admision.objects.create(
        comedor=comedor,
        activa=True,
        enviado_acompaniamiento=True,
        estado_admision="informe_tecnico_aprobado",
        num_expediente="EXP-VIGENTE",
    )
    return comedor


def _desactivar_scope_de_duplas(monkeypatch):
    monkeypatch.setattr(
        UserPermissionService,
        "es_tecnico_o_abogado",
        staticmethod(lambda _user: False),
    )
    monkeypatch.setattr(
        UserPermissionService,
        "get_coordinador_duplas",
        staticmethod(lambda _user: (False, [])),
    )


def test_filtros_acompanamiento_consultan_la_admision_mostrada(
    superuser, monkeypatch
):
    comedor = _crear_comedor_con_dos_admisiones()
    _desactivar_scope_de_duplas(monkeypatch)
    request = RequestFactory().get(
        "/acompanamientos/acompanamiento/",
        {"filters": _filtros_por_estado("iniciada")},
    )

    resultados = list(
        AcompanamientoService.obtener_comedores_acompanamiento(superuser, request)
    )

    assert resultados == []
    request = RequestFactory().get(
        "/acompanamientos/acompanamiento/",
        {"filters": _filtros_por_estado("informe_tecnico_aprobado")},
    )
    resultados = list(
        AcompanamientoService.obtener_comedores_acompanamiento(superuser, request)
    )

    assert resultados == [comedor]
    filas = AcompanamientoService.preparar_datos_tabla_comedores(resultados)
    assert filas[0]["cells"][3]["content"] == "EXP-VIGENTE"


def test_exportacion_acompanamiento_reutiliza_filtros_avanzados(
    auth_client, monkeypatch
):
    comedor = _crear_comedor_con_dos_admisiones()
    _desactivar_scope_de_duplas(monkeypatch)

    response = auth_client.get(
        reverse("lista_comedores_acompanamiento_exportar"),
        {"filters": _filtros_por_estado("iniciada")},
    )

    contenido = b"".join(response.streaming_content).decode()
    assert response.status_code == 200
    assert comedor.nombre not in contenido


def test_exportacion_acompanamiento_respeta_el_orden_del_listado(
    auth_client, monkeypatch
):
    _crear_comedor_con_dos_admisiones(nombre="Alfa")
    _crear_comedor_con_dos_admisiones(nombre="Zulu")
    _desactivar_scope_de_duplas(monkeypatch)

    response = auth_client.get(
        reverse("lista_comedores_acompanamiento_exportar"),
        {"ordering": "nombre"},
    )

    contenido = b"".join(response.streaming_content).decode()
    assert contenido.index("Alfa") < contenido.index("Zulu")
