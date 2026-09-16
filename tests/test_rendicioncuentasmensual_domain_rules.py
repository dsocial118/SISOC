from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection

from comedores.models import Comedor
from organizaciones.models import Organizacion, ProyectoOrganizacion
from rendicioncuentasmensual.filter_config import ESTADO_PROCESO_CHOICES
from rendicioncuentasmensual.models import (
    DocumentacionAdjunta,
    RendicionCuentaMensual,
)
from rendicioncuentasmensual.services import (
    RendicionCuentaMensualService,
    periodo_fin_maximo,
)


@pytest.fixture
def scopes(db):
    organizacion = Organizacion.objects.create(nombre="Organizacion de prueba")
    proyecto_1 = ProyectoOrganizacion.objects.create(
        organizacion=organizacion,
        codigo="PROY-1",
    )
    proyecto_2 = ProyectoOrganizacion.objects.create(
        organizacion=organizacion,
        codigo="PROY-2",
    )
    comedor_1 = Comedor.objects.create(
        nombre="Comedor 1",
        organizacion=organizacion,
        proyecto=proyecto_1,
    )
    comedor_2 = Comedor.objects.create(
        nombre="Comedor 2",
        organizacion=organizacion,
        proyecto=proyecto_2,
    )
    return comedor_1, proyecto_1, comedor_2, proyecto_2


def _crear_rendicion(
    comedor,
    proyecto,
    *,
    convenio="P01",
    numero=1,
    inicio=date(2026, 1, 1),
    fin=date(2026, 1, 31),
    linea=DocumentacionAdjunta.LINEA_TRADICIONAL,
):
    return RendicionCuentaMensual.objects.create(
        comedor=comedor,
        proyecto=proyecto,
        mes=inicio.month,
        anio=inicio.year,
        convenio=convenio,
        numero_rendicion=numero,
        periodo_inicio=inicio,
        periodo_fin=fin,
        linea_programatica=linea,
    )


def _validar(
    comedor,
    proyecto,
    *,
    convenio="P01",
    numero=1,
    inicio=date(2026, 2, 1),
    fin=date(2026, 2, 28),
    linea=DocumentacionAdjunta.LINEA_TRADICIONAL,
    excluir_pk=None,
    numero_actual=None,
):
    return RendicionCuentaMensualService._validar_numero_y_periodo(
        comedor=comedor,
        convenio=convenio,
        numero_rendicion=numero,
        periodo=(inicio, fin),
        proyecto=proyecto,
        linea_programatica=linea,
        excluir_pk=excluir_pk,
        numero_actual=numero_actual,
    )


@pytest.mark.django_db
def test_primera_rendicion_acepta_uno_y_rechaza_dos(scopes):
    comedor, proyecto, _, _ = scopes

    _validar(comedor, proyecto, numero=1)

    with pytest.raises(ValidationError) as exc:
        _validar(comedor, proyecto, numero=2)

    assert exc.value.message_dict["numero_rendicion"] == [
        "El número de rendición debe ser 1: debe continuar la secuencia "
        "del convenio dentro del proyecto."
    ]


@pytest.mark.django_db
def test_validacion_acumula_errores_identificables_por_campo(scopes):
    comedor, proyecto, _, _ = scopes

    with pytest.raises(ValidationError) as exc:
        _validar(
            comedor,
            proyecto,
            convenio="invalido",
            numero=7,
            inicio=date(2026, 2, 2),
            fin=date(2026, 2, 1),
        )

    assert set(exc.value.message_dict) == {
        "convenio",
        "numero_rendicion",
        "periodo_fin",
    }


@pytest.mark.django_db
def test_con_ultimo_dos_acepta_tres(scopes):
    comedor, proyecto, _, _ = scopes
    _crear_rendicion(comedor, proyecto, numero=2)

    _validar(comedor, proyecto, numero=3)


@pytest.mark.django_db
def test_rechaza_numero_repetido(scopes):
    comedor, proyecto, _, _ = scopes
    _crear_rendicion(comedor, proyecto, numero=1)

    with pytest.raises(ValidationError) as exc:
        _validar(comedor, proyecto, numero=1)

    mensajes = exc.value.message_dict["numero_rendicion"]
    assert (
        "Ya existe una rendición con ese número dentro del mismo convenio." in mensajes
    )
    assert any("debe continuar" in mensaje for mensaje in mensajes)


@pytest.mark.django_db
def test_rechaza_numero_menor_a_la_secuencia(scopes):
    comedor, proyecto, _, _ = scopes
    _crear_rendicion(comedor, proyecto, numero=2)

    with pytest.raises(ValidationError) as exc:
        _validar(comedor, proyecto, numero=1)

    assert any(
        "debe ser 3" in mensaje
        for mensaje in exc.value.message_dict["numero_rendicion"]
    )


@pytest.mark.django_db
def test_rechaza_numero_que_salta_la_secuencia(scopes):
    comedor, proyecto, _, _ = scopes
    _crear_rendicion(comedor, proyecto, numero=1)

    with pytest.raises(ValidationError) as exc:
        _validar(comedor, proyecto, numero=3)

    assert any(
        "debe ser 2" in mensaje
        for mensaje in exc.value.message_dict["numero_rendicion"]
    )


@pytest.mark.django_db
def test_mismo_numero_se_permite_en_distinto_convenio(scopes):
    comedor, proyecto, _, _ = scopes
    _crear_rendicion(comedor, proyecto, convenio="P01", numero=1)

    _validar(
        comedor,
        proyecto,
        convenio="P02",
        numero=1,
        inicio=date(2026, 2, 1),
        fin=date(2026, 2, 28),
    )


@pytest.mark.django_db
def test_mismo_numero_se_permite_en_distinto_proyecto(scopes):
    comedor_1, proyecto_1, comedor_2, proyecto_2 = scopes
    _crear_rendicion(comedor_1, proyecto_1, numero=1)

    _validar(comedor_2, proyecto_2, numero=1)


@pytest.mark.django_db
def test_edicion_sin_cambiar_numero_pasa_aunque_rompa_secuencia(scopes):
    comedor, proyecto, _, _ = scopes
    rendicion = _crear_rendicion(comedor, proyecto, numero=2)

    _validar(
        comedor,
        proyecto,
        numero=2,
        inicio=rendicion.periodo_inicio,
        fin=rendicion.periodo_fin,
        excluir_pk=rendicion.pk,
        numero_actual=2,
    )


@pytest.mark.django_db
def test_edicion_cambiando_numero_fuera_de_secuencia_falla(scopes):
    comedor, proyecto, _, _ = scopes
    rendicion = _crear_rendicion(comedor, proyecto, numero=2)

    with pytest.raises(ValidationError) as exc:
        _validar(
            comedor,
            proyecto,
            numero=4,
            inicio=rendicion.periodo_inicio,
            fin=rendicion.periodo_fin,
            excluir_pk=rendicion.pk,
            numero_actual=2,
        )

    assert any(
        "debe ser 1" in mensaje
        for mensaje in exc.value.message_dict["numero_rendicion"]
    )


@pytest.mark.django_db
def test_baja_logica_libera_numero(scopes):
    comedor, proyecto, _, _ = scopes
    _crear_rendicion(comedor, proyecto, numero=1)
    rendicion_2 = _crear_rendicion(
        comedor,
        proyecto,
        numero=2,
        inicio=date(2026, 2, 1),
        fin=date(2026, 2, 28),
    )
    assert (
        RendicionCuentaMensualService.siguiente_numero_rendicion(
            comedor=comedor,
            convenio="P01",
            proyecto=proyecto,
        )
        == 3
    )

    rendicion_2.delete()

    assert (
        RendicionCuentaMensualService.siguiente_numero_rendicion(
            comedor=comedor,
            convenio="P01",
            proyecto=proyecto,
        )
        == 2
    )


@pytest.mark.django_db
def test_crear_rendicion_bloquea_scope_dentro_de_transaccion(scopes, mocker):
    comedor, proyecto, _, _ = scopes
    atomic_states = []

    def registrar_atomicidad(*args, **kwargs):
        atomic_states.append(connection.in_atomic_block)

    bloqueo = mocker.patch.object(
        RendicionCuentaMensualService,
        "_bloquear_scope_numeracion",
        side_effect=registrar_atomicidad,
    )

    RendicionCuentaMensualService.crear_rendicion_mobile(
        comedor=comedor,
        data={
            "proyecto_id": proyecto.pk,
            "convenio": "P01",
            "numero_rendicion": 1,
            "periodo_inicio": date(2026, 1, 1),
            "periodo_fin": date(2026, 1, 31),
            "linea_programatica": DocumentacionAdjunta.LINEA_TRADICIONAL,
        },
    )

    bloqueo.assert_called_once_with(comedor, proyecto)
    assert atomic_states == [True]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("fin",),
    [
        (date(2026, 11, 30),),
        (date(2026, 12, 31),),
        (date(2027, 1, 31),),
    ],
)
def test_periodo_secos_acepta_hasta_ultimo_dia_del_tercer_mes(scopes, fin):
    comedor, proyecto, _, _ = scopes

    _validar(
        comedor,
        proyecto,
        inicio=date(2026, 11, 15),
        fin=fin,
        linea=DocumentacionAdjunta.LINEA_SECOS,
    )


@pytest.mark.django_db
def test_periodo_secos_rechaza_primer_dia_del_cuarto_mes(scopes):
    comedor, proyecto, _, _ = scopes

    with pytest.raises(ValidationError) as exc:
        _validar(
            comedor,
            proyecto,
            inicio=date(2026, 11, 15),
            fin=date(2027, 2, 1),
            linea=DocumentacionAdjunta.LINEA_SECOS,
        )

    assert exc.value.message_dict["periodo_fin"] == [
        "Para Abordaje Comunitario - Línea Secos el período puede abarcar "
        "hasta tres meses: la fecha de fin no puede superar el 31/01/2027."
    ]


@pytest.mark.django_db
def test_periodo_secos_cruce_de_anio(scopes):
    comedor, proyecto, _, _ = scopes
    _validar(
        comedor,
        proyecto,
        inicio=date(2026, 11, 15),
        fin=date(2027, 1, 31),
        linea=DocumentacionAdjunta.LINEA_SECOS,
    )

    with pytest.raises(ValidationError) as exc:
        _validar(
            comedor,
            proyecto,
            inicio=date(2026, 11, 15),
            fin=date(2027, 2, 1),
            linea=DocumentacionAdjunta.LINEA_SECOS,
        )

    assert "periodo_fin" in exc.value.message_dict


@pytest.mark.django_db
def test_periodo_secos_febrero_no_bisiesto(scopes):
    comedor, proyecto, _, _ = scopes
    inicio = date(2026, 12, 15)
    assert periodo_fin_maximo(inicio, DocumentacionAdjunta.LINEA_SECOS) == date(
        2027, 2, 28
    )

    _validar(
        comedor,
        proyecto,
        inicio=inicio,
        fin=date(2027, 2, 28),
        linea=DocumentacionAdjunta.LINEA_SECOS,
    )


@pytest.mark.django_db
def test_periodo_secos_febrero_bisiesto(scopes):
    comedor, proyecto, _, _ = scopes

    _validar(
        comedor,
        proyecto,
        inicio=date(2027, 12, 15),
        fin=date(2028, 2, 29),
        linea=DocumentacionAdjunta.LINEA_SECOS,
    )


@pytest.mark.django_db
def test_periodo_tradicional_rechaza_fin_fuera_del_mes(scopes):
    comedor, proyecto, _, _ = scopes

    with pytest.raises(ValidationError) as exc:
        _validar(
            comedor,
            proyecto,
            inicio=date(2026, 1, 15),
            fin=date(2026, 2, 1),
        )

    assert exc.value.message_dict["periodo_fin"] == [
        "Las fechas deben pertenecer al mismo período mensual."
    ]


def test_catalogo_secos_excluye_planilla_seguros_y_tradicional_la_incluye():
    categorias_secos = {
        item["codigo"]
        for item in DocumentacionAdjunta.categorias_mobile(
            DocumentacionAdjunta.LINEA_SECOS
        )
    }
    categorias_tradicional = {
        item["codigo"]
        for item in DocumentacionAdjunta.categorias_mobile(
            DocumentacionAdjunta.LINEA_TRADICIONAL
        )
    }

    assert DocumentacionAdjunta.CATEGORIA_PLANILLA_SEGUROS not in categorias_secos
    assert DocumentacionAdjunta.CATEGORIA_PLANILLA_SEGUROS in categorias_tradicional


@pytest.mark.django_db
def test_catalogo_secos_conserva_planilla_seguros_historica(scopes):
    comedor, proyecto, _, _ = scopes
    rendicion = _crear_rendicion(
        comedor,
        proyecto,
        linea=DocumentacionAdjunta.LINEA_SECOS,
    )
    DocumentacionAdjunta.objects.create(
        nombre="planilla historica",
        categoria=DocumentacionAdjunta.CATEGORIA_PLANILLA_SEGUROS,
        archivo="historicos/planilla-seguros.pdf",
        rendicion_cuenta_mensual=rendicion,
    )

    categorias = RendicionCuentaMensualService.obtener_categorias_visibles(rendicion)

    assert DocumentacionAdjunta.CATEGORIA_PLANILLA_SEGUROS in {
        item["codigo"] for item in categorias
    }


@pytest.mark.django_db
def test_planilla_seguros_no_se_puede_adjuntar_en_secos(scopes):
    comedor, proyecto, _, _ = scopes
    rendicion = _crear_rendicion(
        comedor,
        proyecto,
        linea=DocumentacionAdjunta.LINEA_SECOS,
    )
    assert (
        DocumentacionAdjunta.get_categoria_config(
            DocumentacionAdjunta.CATEGORIA_PLANILLA_SEGUROS,
            DocumentacionAdjunta.LINEA_SECOS,
        )
        is None
    )

    with pytest.raises(ValidationError) as exc:
        RendicionCuentaMensualService.adjuntar_documentacion_mobile(
            rendicion=rendicion,
            categoria=DocumentacionAdjunta.CATEGORIA_PLANILLA_SEGUROS,
            documento_data={
                "nombre": "planilla.pdf",
                "archivo": SimpleUploadedFile("planilla.pdf", b"contenido"),
            },
        )

    assert "categoria" in exc.value.message_dict


def test_etiquetas_documentales_actualizadas():
    categorias = dict(DocumentacionAdjunta.CATEGORIA_CHOICES)
    assert (
        categorias["comprobantes_alimentario"]
        == "Facturas y Tickets Prestación Alimentaria"
    )
    assert categorias["comprobantes_siph"] == "Facturas y Tickets SIPH"


def test_etiquetas_etapas_distinguen_revision_para_carga_de_auditoria():
    etapas = dict(RendicionCuentaMensual.ETAPA_PROCESO_CHOICES)
    assert etapas["revision_auditoria"] == "Revisión para Carga"
    assert etapas["auditoria"] == "Auditoría"

    rendicion = RendicionCuentaMensual(
        etapa_proceso=RendicionCuentaMensual.ETAPA_REVISION_AUDITORIA,
        subestado_proceso=RendicionCuentaMensual.SUBESTADO_PENDIENTE,
    )
    assert rendicion.estado_proceso_display.startswith("Revisión para Carga")


def test_values_de_estados_de_proceso_no_cambian():
    assert [value for value, _ in ESTADO_PROCESO_CHOICES] == [
        "carga_documentacion:en_curso",
        "revision_documentacion:pendiente",
        "revision_documentacion:en_curso",
        "revision_documentacion:pendiente_correcciones",
        "revision_documentacion:subsanado",
        "revision_auditoria:pendiente",
        "revision_auditoria:en_curso",
        "revision_auditoria:pendiente_correcciones",
        "revision_auditoria:subsanado",
        "auditoria:pendiente",
        "auditoria:en_curso",
        "auditoria:finalizada",
        "auditoria:finalizada_con_observaciones",
        "regularizacion:en_curso",
        "regularizacion:finalizada",
    ]
