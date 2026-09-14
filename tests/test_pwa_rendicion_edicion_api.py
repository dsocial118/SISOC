"""Pruebas del contrato de edición de datos generales de una rendición PWA."""

from datetime import date

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from organizaciones.models import Organizacion, ProyectoOrganizacion
from rendicioncuentasmensual.models import RendicionCuentaMensual
from tests.test_pwa_comedores_api import (
    _create_coordinador_pwa,
    _create_pwa_user,
    _grant_mobile_rendicion_permission,
    _token_client,
    comedores,
)
from users.models import AccesoComedorPWA


@pytest.fixture(autouse=True)
def global_temp_media_root(settings):
    """Evita crear temporales: este archivo no escribe contenido multimedia."""

    settings.MEDIA_ROOT = settings.BASE_DIR / "media"


def _crear_rendicion(comedor, **overrides):
    datos = {
        "comedor": comedor,
        "mes": 1,
        "anio": 2026,
        "convenio": "P01",
        "numero_rendicion": 1,
        "nombre": "Rendición original",
        "periodo_inicio": date(2026, 1, 1),
        "periodo_fin": date(2026, 1, 31),
        "observaciones": "Observación original",
        "estado": RendicionCuentaMensual.ESTADO_ELABORACION,
    }
    datos.update(overrides)
    return RendicionCuentaMensual.objects.create(**datos)


def _cliente_representante(comedor, username="representante_edición"):
    representante = _create_pwa_user(
        comedor=comedor,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username=username,
    )
    _grant_mobile_rendicion_permission(representante)
    return representante, _token_client(representante)


def _url(comedor, rendicion):
    return f"/api/comedores/{comedor.id}/rendiciones/{rendicion.id}/"


@pytest.mark.django_db
def test_edicion_durante_elaboracion_persiste_y_actualiza_periodo(comedores):
    comedor, _ = comedores
    representante, client = _cliente_representante(comedor)
    rendicion = _crear_rendicion(comedor)

    response = client.patch(
        _url(comedor, rendicion),
        {
            "convenio": "P01",
            "numero_rendicion": 1,
            "nombre": "Rendición editada",
            "periodo_inicio": "2026-02-01",
            "periodo_fin": "2026-02-28",
            "observaciones": "Observación actualizada",
        },
        format="json",
    )

    assert response.status_code == 200, response.data
    assert response.data["nombre"] == "Rendición editada"
    assert response.data["periodo_inicio"] == "2026-02-01"
    rendicion.refresh_from_db()
    assert rendicion.nombre == "Rendición editada"
    assert rendicion.observaciones == "Observación actualizada"
    assert rendicion.periodo_inicio == date(2026, 2, 1)
    assert rendicion.periodo_fin == date(2026, 2, 28)
    assert (rendicion.mes, rendicion.anio) == (2, 2026)
    assert rendicion.usuario_ultima_modificacion == representante


@pytest.mark.django_db
def test_edicion_despues_de_presentar_devuelve_conflicto_y_no_persiste(comedores):
    comedor, _ = comedores
    _, client = _cliente_representante(comedor, username="representante_presentada")
    rendicion = _crear_rendicion(
        comedor,
        estado=RendicionCuentaMensual.ESTADO_REVISION,
    )

    response = client.patch(
        _url(comedor, rendicion),
        {"nombre": "Rendición que no debe guardarse"},
        format="json",
    )

    assert response.status_code == 409
    assert response.data == {
        "detail": "La rendición ya no admite edición en su estado actual.",
        "estado": RendicionCuentaMensual.ESTADO_REVISION,
    }
    rendicion.refresh_from_db()
    assert rendicion.nombre == "Rendición original"
    get_response = client.get(_url(comedor, rendicion))
    assert get_response.data["reglas_datos_generales"]["edicion_habilitada"] is False


@pytest.mark.django_db
def test_usuario_sin_alcance_sobre_el_comedor_no_puede_editar(comedores):
    comedor, otro_comedor = comedores
    _, client = _cliente_representante(
        otro_comedor,
        username="representante_sin_alcance",
    )
    rendicion = _crear_rendicion(comedor)

    response = client.patch(
        _url(comedor, rendicion),
        {"nombre": "Rendición fuera de alcance"},
        format="json",
    )

    assert response.status_code == 403
    rendicion.refresh_from_db()
    assert rendicion.nombre == "Rendición original"


@pytest.mark.django_db
def test_coordinador_pwa_tiene_acceso_de_solo_lectura(comedores):
    comedor, _ = comedores
    coordinador = _create_coordinador_pwa(
        comedor=comedor,
        username="coordinador_edición",
    )
    client = _token_client(coordinador)
    rendicion = _crear_rendicion(comedor)

    response = client.patch(
        _url(comedor, rendicion),
        {"nombre": "Rendición coordinada"},
        format="json",
    )

    assert response.status_code == 403
    assert response.data["detail"] == (
        "El coordinador PWA tiene acceso de solo lectura."
    )
    rendicion.refresh_from_db()
    assert rendicion.nombre == "Rendición original"


@pytest.mark.django_db
def test_payload_parcial_conserva_los_campos_omitidos(comedores):
    comedor, _ = comedores
    _, client = _cliente_representante(comedor, username="representante_parcial")
    rendicion = _crear_rendicion(comedor)
    valores_originales = {
        "convenio": rendicion.convenio,
        "numero_rendicion": rendicion.numero_rendicion,
        "periodo_inicio": rendicion.periodo_inicio,
        "periodo_fin": rendicion.periodo_fin,
        "observaciones": rendicion.observaciones,
    }

    response = client.patch(
        _url(comedor, rendicion),
        {"nombre": "Sólo cambia el nombre"},
        format="json",
    )

    assert response.status_code == 200, response.data
    rendicion.refresh_from_db()
    assert rendicion.nombre == "Sólo cambia el nombre"
    for campo, valor in valores_originales.items():
        assert getattr(rendicion, campo) == valor


@pytest.mark.django_db
def test_campos_protegidos_se_ignoran_y_quedan_intactos(comedores):
    comedor, _ = comedores
    organizacion = Organizacion.objects.create(nombre="Organización protegida")
    proyecto_original = ProyectoOrganizacion.objects.create(
        organizacion=organizacion,
        codigo="PROY-ORIGINAL",
        nombre="Proyecto original",
    )
    proyecto_alterno = ProyectoOrganizacion.objects.create(
        organizacion=organizacion,
        codigo="PROY-ALTERNO",
        nombre="Proyecto alterno",
    )
    comedor.organizacion = organizacion
    comedor.proyecto = proyecto_original
    comedor.save(update_fields=("organizacion", "proyecto"))
    _, client = _cliente_representante(comedor, username="representante_protegidos")
    rendicion = _crear_rendicion(comedor, proyecto=proyecto_original)
    etapa_original = rendicion.etapa_proceso
    linea_original = rendicion.linea_programatica

    response = client.patch(
        _url(comedor, rendicion),
        {
            "nombre": "Rendición con campos protegidos",
            "estado": RendicionCuentaMensual.ESTADO_REVISION,
            "etapa_proceso": "otra_etapa",
            "linea_programatica": "otra_línea",
            "proyecto": proyecto_alterno.id,
        },
        format="json",
    )

    assert response.status_code == 200, response.data
    rendicion.refresh_from_db()
    assert rendicion.nombre == "Rendición con campos protegidos"
    assert rendicion.estado == RendicionCuentaMensual.ESTADO_ELABORACION
    assert rendicion.etapa_proceso == etapa_original
    assert rendicion.linea_programatica == linea_original
    assert rendicion.proyecto == proyecto_original


@pytest.mark.django_db
def test_cambio_de_estado_antes_del_lock_devuelve_conflicto_sin_escribir(comedores):
    comedor, _ = comedores
    _, client = _cliente_representante(comedor, username="representante_carrera")
    rendicion = _crear_rendicion(comedor)
    RendicionCuentaMensual.objects.filter(pk=rendicion.pk).update(
        estado=RendicionCuentaMensual.ESTADO_REVISION
    )

    response = client.patch(
        _url(comedor, rendicion),
        {"nombre": "Rendición llegada durante la carrera"},
        format="json",
    )

    assert response.status_code == 409
    rendicion.refresh_from_db()
    assert rendicion.estado == RendicionCuentaMensual.ESTADO_REVISION
    assert rendicion.nombre == "Rendición original"


@pytest.mark.django_db
def test_convenio_invalido_acumula_errores_de_convenio_y_numero(comedores):
    comedor, _ = comedores
    _, client = _cliente_representante(comedor, username="representante_convenio")
    rendicion = _crear_rendicion(comedor)

    response = client.patch(
        _url(comedor, rendicion),
        {"convenio": "P99", "numero_rendicion": 7},
        format="json",
    )

    assert response.status_code == 400
    assert "convenio" in response.data["detail"]
    assert "numero_rendicion" in response.data["detail"]
    rendicion.refresh_from_db()
    assert rendicion.convenio == "P01"
    assert rendicion.numero_rendicion == 1


@pytest.mark.django_db
def test_numero_fuera_de_secuencia_devuelve_error_de_dominio(comedores):
    comedor, _ = comedores
    _, client = _cliente_representante(comedor, username="representante_secuencia")
    rendicion = _crear_rendicion(comedor)

    response = client.patch(
        _url(comedor, rendicion),
        {"numero_rendicion": 3},
        format="json",
    )

    assert response.status_code == 400
    assert "numero_rendicion" in response.data["detail"]
    rendicion.refresh_from_db()
    assert rendicion.numero_rendicion == 1


@pytest.mark.django_db
def test_periodo_fin_fuera_de_ventana_devuelve_error_de_dominio(comedores):
    comedor, _ = comedores
    _, client = _cliente_representante(comedor, username="representante_período")
    rendicion = _crear_rendicion(comedor)

    response = client.patch(
        _url(comedor, rendicion),
        {"periodo_fin": "2026-02-28"},
        format="json",
    )

    assert response.status_code == 400
    assert "periodo_fin" in response.data["detail"]
    rendicion.refresh_from_db()
    assert rendicion.periodo_fin == date(2026, 1, 31)


@pytest.mark.django_db
def test_get_conserva_contrato_y_agrega_reglas_de_datos_generales(comedores):
    comedor, _ = comedores
    _, client = _cliente_representante(comedor, username="representante_reglas")
    linea_secos = next(
        valor
        for valor, etiqueta in RendicionCuentaMensual.LINEA_PROGRAMATICA_CHOICES
        if "Secos" in str(etiqueta)
    )
    rendicion = _crear_rendicion(
        comedor,
        convenio="P02",
        numero_rendicion=6,
        linea_programatica=linea_secos,
        periodo_fin=date(2026, 3, 31),
    )
    _crear_rendicion(
        comedor,
        convenio="P01",
        numero_rendicion=1,
        periodo_inicio=date(2025, 10, 1),
        periodo_fin=date(2025, 10, 31),
    )
    _crear_rendicion(
        comedor,
        convenio="P01",
        numero_rendicion=2,
        periodo_inicio=date(2025, 11, 1),
        periodo_fin=date(2025, 11, 30),
    )
    _crear_rendicion(
        comedor,
        convenio="P02",
        numero_rendicion=2,
        periodo_inicio=date(2025, 12, 1),
        periodo_fin=date(2025, 12, 31),
    )

    with CaptureQueriesContext(connection) as queries:
        response = client.get(_url(comedor, rendicion))

    assert response.status_code == 200, response.data
    campos_lectura = {
        "id",
        "proyecto",
        "convenio",
        "nombre",
        "numero_rendicion",
        "mes",
        "anio",
        "periodo_inicio",
        "periodo_fin",
        "periodo_label",
        "linea_programatica",
        "linea_programatica_label",
        "estado",
        "estado_label",
        "etapa_proceso",
        "subestado_proceso",
        "estado_proceso_label",
        "documento_adjunto",
        "observaciones",
        "fecha_creacion",
        "ultima_modificacion",
        "comprobantes",
        "documentacion",
        "modelos",
    }
    assert campos_lectura <= set(response.data)
    assert response.data.get("proyecto_codigo") is None
    reglas = response.data["reglas_datos_generales"]
    assert reglas == {
        "edicion_habilitada": True,
        "campos_editables": [
            "convenio",
            "numero_rendicion",
            "periodo_inicio",
            "periodo_fin",
            "nombre",
            "observaciones",
        ],
        "convenios": ["P01", "P02", "P03"],
        "numero_rendicion_minimo": 1,
        "numero_rendicion_maximo": 6,
        "proximo_numero_por_convenio": {"P01": 3, "P02": 3, "P03": 1},
        "meses_periodo": 3,
    }
    # El número sugerido se delega en `siguiente_numero_rendicion` para que salga
    # del mismo scope que después valida el servidor. Eso cuesta un agregado por
    # convenio, pero la cantidad es fija: no crece con las rendiciones cargadas,
    # que es la propiedad que interesa cuidar acá.
    consultas_maximo = [
        consulta["sql"] for consulta in queries if "MAX(" in consulta["sql"].upper()
    ]
    assert len(consultas_maximo) == len(reglas["convenios"])


def _url_validar(comedor):
    return f"/api/comedores/{comedor.id}/rendiciones/validar/"


def _payload_validar(**overrides):
    payload = {
        "convenio": "P01",
        "numero_rendicion": 1,
        "nombre": "Rendición para validar",
        "periodo_inicio": "2026-01-01",
        "periodo_fin": "2026-01-31",
        "observaciones": "Sin persistencia",
    }
    payload.update(overrides)
    return payload


@pytest.mark.django_db
def test_validar_alta_valida_sin_crear_rendicion(comedores):
    comedor, _ = comedores
    _, client = _cliente_representante(comedor, username="representante_validar_alta")
    cantidad_antes = RendicionCuentaMensual.objects.count()

    response = client.post(_url_validar(comedor), _payload_validar(), format="json")

    assert response.status_code == 204, response.data
    assert RendicionCuentaMensual.objects.count() == cantidad_antes


@pytest.mark.django_db
def test_validar_alta_rechaza_numero_fuera_de_secuencia_sin_escribir(comedores):
    comedor, _ = comedores
    _, client = _cliente_representante(
        comedor,
        username="representante_validar_secuencia",
    )
    cantidad_antes = RendicionCuentaMensual.objects.count()

    response = client.post(
        _url_validar(comedor),
        _payload_validar(numero_rendicion=2),
        format="json",
    )

    assert response.status_code == 400
    assert "numero_rendicion" in response.data["detail"]
    assert RendicionCuentaMensual.objects.count() == cantidad_antes


@pytest.mark.django_db
def test_validar_alta_rechaza_periodo_fuera_de_ventana(comedores):
    comedor, _ = comedores
    _, client = _cliente_representante(
        comedor,
        username="representante_validar_período",
    )

    response = client.post(
        _url_validar(comedor),
        _payload_validar(periodo_fin="2026-02-28"),
        format="json",
    )

    assert response.status_code == 400
    assert "periodo_fin" in response.data["detail"]
    convenio_invalido = client.post(
        _url_validar(comedor),
        _payload_validar(convenio="P99"),
        format="json",
    )
    assert convenio_invalido.status_code == 400
    assert "convenio" in convenio_invalido.data


@pytest.mark.django_db
def test_validar_edicion_acepta_los_datos_persistidos_de_la_rendicion(comedores):
    comedor, _ = comedores
    _, client = _cliente_representante(
        comedor,
        username="representante_validar_edición",
    )
    rendicion = _crear_rendicion(comedor)

    response = client.post(
        _url_validar(comedor),
        _payload_validar(
            rendicion_id=rendicion.id,
            convenio=rendicion.convenio,
            numero_rendicion=rendicion.numero_rendicion,
            periodo_inicio=rendicion.periodo_inicio.isoformat(),
            periodo_fin=rendicion.periodo_fin.isoformat(),
        ),
        format="json",
    )

    assert response.status_code == 204, response.data
    numero_invalido = client.post(
        _url_validar(comedor),
        _payload_validar(rendicion_id=rendicion.id, numero_rendicion=3),
        format="json",
    )
    assert numero_invalido.status_code == 400
    assert "numero_rendicion" in numero_invalido.data["detail"]


@pytest.mark.django_db
def test_validar_edicion_inexistente_devuelve_404(comedores):
    comedor, _ = comedores
    _, client = _cliente_representante(
        comedor,
        username="representante_validar_inexistente",
    )

    response = client.post(
        _url_validar(comedor),
        _payload_validar(rendicion_id=999999),
        format="json",
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_validar_rechaza_usuario_sin_alcance_sobre_el_comedor(comedores):
    comedor, otro_comedor = comedores
    _, client = _cliente_representante(
        otro_comedor,
        username="representante_validar_sin_alcance",
    )

    response = client.post(_url_validar(comedor), _payload_validar(), format="json")

    assert response.status_code == 403


@pytest.mark.django_db
def test_validar_rechaza_coordinador_pwa(comedores):
    comedor, _ = comedores
    coordinador = _create_coordinador_pwa(
        comedor=comedor,
        username="coordinador_validar",
    )
    client = _token_client(coordinador)

    response = client.post(_url_validar(comedor), _payload_validar(), format="json")

    assert response.status_code == 403
    assert response.data["detail"] == "El coordinador PWA tiene acceso de solo lectura."


@pytest.mark.django_db
def test_validar_rechaza_proyecto_de_otra_organizacion(comedores):
    comedor, _ = comedores
    organizacion = Organizacion.objects.create(nombre="Organización del comedor")
    otra_organizacion = Organizacion.objects.create(nombre="Otra organización")
    proyecto_ajeno = ProyectoOrganizacion.objects.create(
        organizacion=otra_organizacion,
        codigo="PROY-AJENO",
        nombre="Proyecto ajeno",
    )
    comedor.organizacion = organizacion
    comedor.save(update_fields=("organizacion",))
    _, client = _cliente_representante(
        comedor,
        username="representante_validar_proyecto",
    )

    response = client.post(
        _url_validar(comedor),
        _payload_validar(proyecto_id=proyecto_ajeno.id),
        format="json",
    )

    assert response.status_code == 400
    assert "proyecto_id" in response.data["detail"]


@pytest.mark.django_db
def test_ruta_validar_resuelve_la_action_especifica(comedores):
    from django.urls import resolve

    comedor, _ = comedores

    match = resolve(_url_validar(comedor))

    assert match.func.actions["post"] == "rendicion_a_validar"


@pytest.mark.django_db
def test_subsanacion_origen_territorial_aparece_en_listado_y_detalle(comedores):
    comedor, _ = comedores
    _, client = _cliente_representante(
        comedor,
        username="representante_subsanación_territorial",
    )
    rendicion = _crear_rendicion(
        comedor,
        etapa_proceso=RendicionCuentaMensual.ETAPA_REVISION_DOCUMENTACION,
        subestado_proceso=RendicionCuentaMensual.SUBESTADO_PENDIENTE_CORRECCIONES,
    )

    listado = client.get(f"/api/comedores/{comedor.id}/rendiciones/")
    detalle = client.get(_url(comedor, rendicion))

    assert listado.status_code == 200, listado.data
    assert detalle.status_code == 200, detalle.data
    assert listado.data["results"][0]["subsanacion_origen"] == "territorial"
    assert detalle.data["subsanacion_origen"] == "territorial"


@pytest.mark.django_db
def test_subsanacion_origen_auditoria_para_revision_auditoria(comedores):
    comedor, _ = comedores
    _, client = _cliente_representante(
        comedor,
        username="representante_subsanación_auditoría",
    )
    rendicion = _crear_rendicion(
        comedor,
        etapa_proceso=RendicionCuentaMensual.ETAPA_REVISION_AUDITORIA,
        subestado_proceso=RendicionCuentaMensual.SUBESTADO_PENDIENTE_CORRECCIONES,
    )

    response = client.get(_url(comedor, rendicion))

    assert response.status_code == 200, response.data
    assert response.data["subsanacion_origen"] == "auditoria"
    etapa_auditoria = _crear_rendicion(
        comedor,
        etapa_proceso=RendicionCuentaMensual.ETAPA_AUDITORIA,
        subestado_proceso=RendicionCuentaMensual.SUBESTADO_PENDIENTE_CORRECCIONES,
    )
    respuesta_etapa_auditoria = client.get(_url(comedor, etapa_auditoria))
    assert respuesta_etapa_auditoria.status_code == 200, respuesta_etapa_auditoria.data
    assert respuesta_etapa_auditoria.data["subsanacion_origen"] is None


@pytest.mark.django_db
def test_subsanacion_origen_es_nulo_fuera_de_pendiente_correcciones(comedores):
    comedor, _ = comedores
    _, client = _cliente_representante(
        comedor,
        username="representante_subsanación_nula",
    )
    for subestado in (
        RendicionCuentaMensual.SUBESTADO_EN_CURSO,
        RendicionCuentaMensual.SUBESTADO_PENDIENTE,
    ):
        rendicion = _crear_rendicion(
            comedor,
            etapa_proceso=RendicionCuentaMensual.ETAPA_REVISION_DOCUMENTACION,
            subestado_proceso=subestado,
        )
        response = client.get(_url(comedor, rendicion))

        assert response.status_code == 200, response.data
        assert response.data["subsanacion_origen"] is None


@pytest.mark.django_db
def test_validar_acepta_el_payload_exacto_que_envia_la_pwa(comedores):
    """Contrato de integración con Espacios-Comunitarios (PR #11, ya mergeado).

    La PWA postea el mismo objeto que usa para el alta, con `linea_programatica`
    incluida, y sólo mira que la respuesta no sea un error. Este test fija ese
    shape para que un cambio en el serializer no rompa la app en silencio.
    """
    comedor, _ = comedores
    _, client = _cliente_representante(comedor, username="representante_pwa_shape")

    payload = {
        "proyecto_id": None,
        "convenio": "P01",
        "nombre": "Rendición Secos",
        "numero_rendicion": 1,
        "periodo_inicio": "2026-09-03",
        "periodo_fin": "2026-11-30",
        "linea_programatica": "secos",
        "observaciones": "",
    }

    response = client.post(_url_validar(comedor), payload, format="json")

    assert response.status_code == 204, response.data
    assert RendicionCuentaMensual.objects.count() == 0


@pytest.mark.django_db
def test_validar_respeta_la_linea_programatica_enviada_en_el_payload(comedores):
    """Un período de tres meses sólo es válido en Secos, no en Tradicional."""
    comedor, _ = comedores
    _, client = _cliente_representante(comedor, username="representante_pwa_linea")

    base = {
        "convenio": "P01",
        "numero_rendicion": 1,
        "periodo_inicio": "2026-09-03",
        "periodo_fin": "2026-11-30",
    }

    secos = client.post(
        _url_validar(comedor),
        {**base, "linea_programatica": "secos"},
        format="json",
    )
    tradicional = client.post(
        _url_validar(comedor),
        {**base, "linea_programatica": "tradicional"},
        format="json",
    )

    assert secos.status_code == 204, secos.data
    assert tradicional.status_code == 400
    assert "periodo_fin" in tradicional.data["detail"]
