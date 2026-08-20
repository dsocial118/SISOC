"""Regresiones de filtros y exportacion del listado de acompanamientos."""

import json

import pytest
from django.urls import reverse
from django.test import RequestFactory

from acompanamientos.acompanamiento_service import AcompanamientoService
from acompanamientos.models.acompanamiento import Acompanamiento
from admisiones.models.admisiones import Admision
from comedores.models import Comedor
from users.services import UserPermissionService


pytestmark = pytest.mark.django_db


def _filtros(campo, valor):
    return json.dumps(
        {
            "logic": "AND",
            "items": [{"field": campo, "op": "eq", "value": valor}],
        }
    )


def _filtros_por_estado(estado):
    return _filtros("estado", estado)


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


def _request(params=None):
    return RequestFactory().get("/acompanamientos/acompanamiento/", params or {})


def test_listado_devuelve_una_fila_por_acompanamiento(superuser, monkeypatch):
    """El grano del listado es el convenio: dos admisiones son dos filas."""
    comedor = _crear_comedor_con_dos_admisiones()
    _desactivar_scope_de_duplas(monkeypatch)

    resultados = list(
        AcompanamientoService.obtener_acompanamientos(superuser, _request())
    )

    assert len(resultados) == 2
    assert {a.comedor_id for a in resultados} == {comedor.id}
    assert {a.num_expediente for a in resultados} == {"EXP-ANTERIOR", "EXP-VIGENTE"}


def test_filtros_acompanamiento_consultan_cada_admision(superuser, monkeypatch):
    _crear_comedor_con_dos_admisiones()
    _desactivar_scope_de_duplas(monkeypatch)

    resultados = list(
        AcompanamientoService.obtener_acompanamientos(
            superuser, _request({"filters": _filtros_por_estado("iniciada")})
        )
    )

    assert [a.num_expediente for a in resultados] == ["EXP-ANTERIOR"]

    resultados = list(
        AcompanamientoService.obtener_acompanamientos(
            superuser,
            _request({"filters": _filtros_por_estado("informe_tecnico_aprobado")}),
        )
    )

    assert [a.num_expediente for a in resultados] == ["EXP-VIGENTE"]
    filas = AcompanamientoService.preparar_datos_tabla_acompanamientos(resultados)
    assert filas[0]["cells"][4]["content"] == "EXP-VIGENTE"


def test_el_historico_persiste_con_su_etiqueta(superuser, monkeypatch):
    """Cerrados y finalizados siguen apareciendo, etiquetados."""
    comedor = Comedor.objects.create(nombre="Comedor historico")
    vigente = Admision.objects.create(
        comedor=comedor,
        activa=True,
        enviado_acompaniamiento=True,
        estado_admision="iniciada",
        num_expediente="EXP-VIGENTE",
    )
    cerrada = Admision.objects.create(
        comedor=comedor,
        activa=False,
        enviado_acompaniamiento=True,
        estado_admision="iniciada",
        num_expediente="EXP-CERRADA",
    )
    finalizada = Admision.objects.create(
        comedor=comedor,
        activa=True,
        enviado_acompaniamiento=True,
        estado_admision="iniciada",
        num_expediente="EXP-FINALIZADA",
    )
    Acompanamiento.objects.create(admision=finalizada, nro_convenio="CONV-FIN")
    AcompanamientoService.finalizar_acompanamiento(comedor, finalizada.id, superuser)
    _desactivar_scope_de_duplas(monkeypatch)

    resultados = {
        a.num_expediente: a.estado_acompanamiento
        for a in AcompanamientoService.obtener_acompanamientos(superuser, _request())
    }

    assert resultados == {
        "EXP-VIGENTE": Acompanamiento.ESTADO_ACTIVO,
        "EXP-CERRADA": Acompanamiento.ESTADO_CERRADO,
        "EXP-FINALIZADA": Acompanamiento.ESTADO_FINALIZADO,
    }
    assert {vigente.id, cerrada.id, finalizada.id} == {
        a.id
        for a in AcompanamientoService.obtener_acompanamientos(superuser, _request())
    }


def test_filtro_por_estado_del_acompanamiento(superuser, monkeypatch):
    comedor = Comedor.objects.create(nombre="Comedor filtrable")
    Admision.objects.create(
        comedor=comedor,
        activa=True,
        enviado_acompaniamiento=True,
        estado_admision="iniciada",
        num_expediente="EXP-VIGENTE",
    )
    Admision.objects.create(
        comedor=comedor,
        activa=False,
        enviado_acompaniamiento=True,
        estado_admision="iniciada",
        num_expediente="EXP-CERRADA",
    )
    _desactivar_scope_de_duplas(monkeypatch)

    resultados = list(
        AcompanamientoService.obtener_acompanamientos(
            superuser,
            _request(
                {
                    "filters": _filtros(
                        "estado_acompanamiento", Acompanamiento.ESTADO_CERRADO
                    )
                }
            ),
        )
    )

    assert [a.num_expediente for a in resultados] == ["EXP-CERRADA"]


def test_la_fila_apunta_al_convenio_correcto(superuser, monkeypatch):
    comedor = _crear_comedor_con_dos_admisiones()
    _desactivar_scope_de_duplas(monkeypatch)

    resultados = list(
        AcompanamientoService.obtener_acompanamientos(superuser, _request())
    )
    filas = AcompanamientoService.preparar_datos_tabla_acompanamientos(resultados)

    for admision, fila in zip(resultados, filas):
        url = fila["actions"][0]["url"]
        assert f"/acompanamiento/{comedor.id}/detalle/" in url
        assert f"admision_id={admision.id}" in url


def test_exportacion_acompanamiento_reutiliza_filtros_avanzados(
    auth_client, monkeypatch
):
    _crear_comedor_con_dos_admisiones()
    _desactivar_scope_de_duplas(monkeypatch)

    response = auth_client.get(
        reverse("lista_comedores_acompanamiento_exportar"),
        {"filters": _filtros_por_estado("iniciada")},
    )

    contenido = b"".join(response.streaming_content).decode()
    assert response.status_code == 200
    assert "EXP-ANTERIOR" in contenido
    assert "EXP-VIGENTE" not in contenido


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


def test_exportacion_incluye_organizacion_y_estado_del_acompanamiento(
    auth_client, monkeypatch, superuser
):
    """Las columnas relacionadas se resuelven con puntos, no con lookups ORM."""
    from organizaciones.models import Organizacion

    organizacion = Organizacion.objects.create(nombre="Org Exportable")
    comedor = Comedor.objects.create(nombre="Comedor Export", organizacion=organizacion)
    admision = Admision.objects.create(
        comedor=comedor,
        activa=False,
        enviado_acompaniamiento=True,
        estado_admision="iniciada",
        num_expediente="EXP-EXPORT",
    )
    Acompanamiento.objects.create(admision=admision, nro_convenio="CONV-EXPORT")
    _desactivar_scope_de_duplas(monkeypatch)

    response = auth_client.get(reverse("lista_comedores_acompanamiento_exportar"))
    contenido = b"".join(response.streaming_content).decode()

    assert "Org Exportable" in contenido
    assert "CONV-EXPORT" in contenido
    assert "Cerrado" in contenido
