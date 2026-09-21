from copy import deepcopy
from datetime import date
from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db.models.query import QuerySet
from django.utils import timezone

from ciudadanos.models import Ciudadano
from centrodeinfancia.models import CentroDeInfancia, NominaCentroInfancia
from core.models import Sexo

pytestmark = pytest.mark.django_db
COMMAND = "validar_renaper_nominas_cdi"
LOOKUP = (
    "centrodeinfancia.management.commands.validar_renaper_nominas_cdi."
    "consultar_datos_renaper"
)


@pytest.fixture
def crear_ficha():
    centro = CentroDeInfancia.objects.create(nombre="CDI revalidación")

    def crear(documento=55123456, **kwargs):
        ciudadano = Ciudadano.objects.create(
            documento=documento,
            apellido="Pérez",
            nombre="Ana María",
            fecha_nacimiento=date(2024, 1, 15),
            calle="Calle cargada",
            **kwargs,
        )
        NominaCentroInfancia.objects.create(centro=centro, ciudadano=ciudadano)
        return ciudadano

    return crear


def _success(**overrides):
    data = {
        "dni": 55123456,
        "apellido": "PÉREZ",
        "nombre": " ANA   MARÍA ",
        "fecha_nacimiento": "15/01/2024",
        "calle": "Otra calle",
    }
    data.update(overrides)
    return {"success": True, "data": data, "datos_api": {"respuesta": "original"}}


def _snapshot(ciudadano):
    return deepcopy(Ciudadano.objects.filter(pk=ciudadano.pk).values().get())


@pytest.mark.parametrize("dry_run", [False, True])
@pytest.mark.parametrize(
    "caso", ["coincide", "apellido", "nombre", "fecha", "incompleto", "no_match"]
)
def test_resultados_y_dry_run(crear_ficha, caso, dry_run):
    ciudadano = crear_ficha()
    previo = _snapshot(ciudadano)
    result = _success()
    if caso == "apellido":
        result["data"]["apellido"] = "Gómez"
    elif caso == "nombre":
        result["data"]["nombre"] = "Laura"
    elif caso == "fecha":
        result["data"]["fecha_nacimiento"] = "01/01/2024"
    elif caso == "incompleto":
        result["data"]["nombre"] = ""
    elif caso == "no_match":
        result = {"success": False, "error_type": "no_match"}
    output = StringIO()
    with patch(LOOKUP, return_value=result):
        call_command(COMMAND, dry_run=dry_run, stdout=output)
    ciudadano.refresh_from_db()
    if dry_run:
        assert _snapshot(ciudadano) == previo
        assert "escritos=0" in output.getvalue()
    else:
        esperado = (
            Ciudadano.RENAPER_VALIDADO
            if caso == "coincide"
            else Ciudadano.RENAPER_NO_VALIDADO
        )
        assert ciudadano.estado_validacion_renaper == esperado
        assert ciudadano.fecha_validacion_renaper is not None
        if caso == "coincide":
            assert ciudadano.datos_renaper == result["datos_api"]
            assert ciudadano.origen_dato == "renaper"
        else:
            assert ciudadano.motivo_no_validacion_renaper
            assert ciudadano.motivo_no_validacion_descripcion
            assert ciudadano.origen_dato == previo["origen_dato"]
        for campo in ("documento", "apellido", "nombre", "fecha_nacimiento", "calle"):
            assert getattr(ciudadano, campo) == previo[campo]
        assert "escritos=1" in output.getvalue()


@pytest.mark.parametrize(
    "error_type",
    [
        "timeout",
        "auth_error",
        "remote_error",
        "invalid_response",
    ],
)
@pytest.mark.parametrize("dry_run", [False, True])
def test_error_tardio_conserva_lotes_y_reanuda(crear_ficha, error_type, dry_run):
    ciudadanos = [crear_ficha(55123456 + i) for i in range(5)]
    previos = [_snapshot(ciudadano) for ciudadano in ciudadanos]
    output = StringIO()
    with patch(
        LOOKUP,
        side_effect=[
            _success(),
            {"success": False, "error_type": "no_match"},
            {"success": False, "error_type": "no_match"},
            {"success": False, "error_type": "no_match"},
            _success(),
            {"success": False, "error_type": error_type},
        ],
    ) as consultar:
        with pytest.raises(CommandError):
            call_command(COMMAND, batch_size=2, dry_run=dry_run, stdout=output)
    assert consultar.call_count == 6
    confirmados = 0 if dry_run else 2
    assert [_snapshot(c) for c in ciudadanos[confirmados:]] == previos[confirmados:]
    assert f"escritos={confirmados}" in output.getvalue()
    assert "errores=1" in output.getvalue()
    with patch(LOOKUP, return_value=_success()) as consultar:
        call_command(COMMAND, batch_size=2)
    assert [call.args[0] for call in consultar.call_args_list] == [
        str(c.documento) for c in ciudadanos[confirmados:]
    ]


def test_reintenta_sexo_solo_hasta_exito(crear_ficha):
    crear_ficha()
    with patch(
        LOOKUP,
        side_effect=[{"success": False, "error_type": "no_match"}, _success()],
    ) as consultar:
        call_command(COMMAND)
    assert [call.args for call in consultar.call_args_list] == [
        ("55123456", "M"),
        ("55123456", "F"),
    ]


def test_sexo_conocido_como_importacion_masiva(crear_ficha):
    sexo = Sexo.objects.create(sexo="Femenino")
    crear_ficha(sexo=sexo)
    with patch(LOOKUP, return_value=_success()) as consultar:
        call_command(COMMAND)
    consultar.assert_called_once_with("55123456", "F")


def test_universo_limit_reanudacion_y_no_duplicar_consultas(crear_ficha):
    primero = crear_ficha()
    segundo = crear_ficha(55123457)
    borrado = crear_ficha(55123458)
    borrado.nominas_centros_infancia.update(deleted_at=timezone.now())
    sin_documento = crear_ficha(None)
    validado = crear_ficha(
        55123459, estado_validacion_renaper=Ciudadano.RENAPER_VALIDADO
    )
    no_validado = crear_ficha(
        55123460, estado_validacion_renaper=Ciudadano.RENAPER_NO_VALIDADO
    )
    sin_nomina = Ciudadano.objects.create(
        documento=55123461,
        apellido="Fuera",
        nombre="Universo",
        fecha_nacimiento=date(2024, 1, 15),
    )
    NominaCentroInfancia.objects.create(
        centro=CentroDeInfancia.objects.create(nombre="Histórico"),
        ciudadano=primero,
        estado=NominaCentroInfancia.ESTADO_BAJA,
    )
    excluidos = [borrado, sin_documento, validado, no_validado, sin_nomina]
    previos = [_snapshot(ciudadano) for ciudadano in excluidos]
    with patch(LOOKUP, return_value=_success()) as consultar:
        call_command(COMMAND, limit=1, batch_size=1)
        consultar.assert_called_once_with(str(primero.documento), "M")
    with patch(LOOKUP, return_value=_success(dni=segundo.documento)) as consultar:
        call_command(COMMAND, batch_size=1)
        consultar.assert_called_once_with(str(segundo.documento), "M")
    with patch(LOOKUP) as consultar:
        call_command(COMMAND)
        consultar.assert_not_called()
    assert [_snapshot(ciudadano) for ciudadano in excluidos] == previos


@pytest.mark.parametrize("cambio", ["nombre", "documento", "estado", "borrado"])
def test_omite_ciudadano_modificado_durante_consulta(crear_ficha, cambio):
    ciudadano = crear_ficha()

    def consultar(*_args):
        if cambio == "borrado":
            ciudadano.nominas_centros_infancia.update(deleted_at=timezone.now())
        else:
            updates = {
                "nombre": {"nombre": "Otra"},
                "documento": {"documento": 55123499},
                "estado": {"estado_validacion_renaper": Ciudadano.RENAPER_NO_VALIDADO},
            }
            Ciudadano.objects.filter(pk=ciudadano.pk).update(**updates[cambio])
        return _success()

    output = StringIO()
    with patch(LOOKUP, side_effect=consultar):
        call_command(COMMAND, stdout=output)
    ciudadano.refresh_from_db()
    assert ciudadano.estado_validacion_renaper != Ciudadano.RENAPER_VALIDADO
    assert ciudadano.fecha_validacion_renaper is None
    assert "omitidos=1" in output.getvalue()


@pytest.mark.parametrize(
    "options",
    [{"batch_size": 0}, {"batch_size": -1}, {"limit": 0}, {"limit": -1}],
)
def test_rechaza_limites_invalidos(options):
    with patch(LOOKUP) as consultar:
        with pytest.raises(CommandError):
            call_command(COMMAND, **options)
        consultar.assert_not_called()


def test_excepcion_inesperada_omite_ficha_y_continua(crear_ficha):
    ciudadanos = [crear_ficha(55123456 + i) for i in range(3)]
    previo = _snapshot(ciudadanos[1])
    output = StringIO()
    with patch(
        LOOKUP, side_effect=[_success(), RuntimeError("dato sensible"), _success()]
    ):
        call_command(COMMAND, batch_size=2, stdout=output)
    assert "dato sensible" not in output.getvalue()
    assert "escritos=2" in output.getvalue()
    assert "omitidos=1" in output.getvalue()
    assert _snapshot(ciudadanos[1]) == previo


def test_error_de_escritura_revierte_solo_lote_actual(crear_ficha):
    ciudadanos = [crear_ficha(55123456 + i) for i in range(4)]
    previos = [_snapshot(ciudadano) for ciudadano in ciudadanos]
    update = QuerySet.update
    intentos = []

    def fallar_cuarta_escritura(queryset, **kwargs):
        if queryset.model is Ciudadano and "estado_validacion_renaper" in kwargs:
            intentos.append(True)
            if len(intentos) == 4:
                raise RuntimeError("Falla simulada")
        return update(queryset, **kwargs)

    with (
        patch(LOOKUP, return_value=_success()),
        patch.object(QuerySet, "update", fallar_cuarta_escritura),
    ):
        with pytest.raises(CommandError):
            call_command(COMMAND, batch_size=2)
    assert len(intentos) == 4
    assert [_snapshot(c) for c in ciudadanos[2:]] == previos[2:]
    for c in ciudadanos[:2]:
        c.refresh_from_db()
        assert c.estado_validacion_renaper == Ciudadano.RENAPER_VALIDADO


@pytest.mark.parametrize("dry_run", [False, True])
def test_fallecido_se_marca_y_no_interrumpe(crear_ficha, dry_run):
    fallecido = crear_ficha()
    siguiente = crear_ficha(55123457)
    previo = _snapshot(fallecido)
    output = StringIO()
    with patch(
        LOOKUP,
        side_effect=[{"success": False, "error_type": "fallecido"}, _success()],
    ) as consultar:
        call_command(COMMAND, batch_size=1, dry_run=dry_run, stdout=output)
    assert consultar.call_count == 2
    assert "fallecidos=1" in output.getvalue()
    if dry_run:
        assert _snapshot(fallecido) == previo
        assert "escritos=0" in output.getvalue()
    else:
        fallecido.refresh_from_db()
        siguiente.refresh_from_db()
        assert fallecido.estado_validacion_renaper == Ciudadano.RENAPER_NO_VALIDADO
        assert (
            fallecido.motivo_no_validacion_renaper == Ciudadano.MOTIVO_NO_VALIDADO_OTRO
        )
        assert "RENAPER reporta" in fallecido.motivo_no_validacion_descripcion
        assert "fallecida" in fallecido.motivo_no_validacion_descripcion
        assert siguiente.estado_validacion_renaper == Ciudadano.RENAPER_VALIDADO
        assert "escritos=2" in output.getvalue()


@pytest.mark.parametrize("error_type", ["unexpected_error", "desconocido", None])
def test_error_no_sistemico_omite_sin_escribir_y_sigue(crear_ficha, error_type):
    omitido = crear_ficha()
    siguiente = crear_ficha(55123457)
    previo = _snapshot(omitido)
    output = StringIO()
    with patch(
        LOOKUP,
        side_effect=[{"success": False, "error_type": error_type}, _success()],
    ):
        call_command(COMMAND, batch_size=1, stdout=output)
    assert _snapshot(omitido) == previo
    siguiente.refresh_from_db()
    assert siguiente.estado_validacion_renaper == Ciudadano.RENAPER_VALIDADO
    assert "omitidos=1" in output.getvalue()
    assert "errores=1" in output.getvalue()


def test_corte_por_20_errores_consecutivos_conserva_lotes(crear_ficha):
    ciudadanos = [crear_ficha(55123456 + i) for i in range(24)]
    output = StringIO()
    resultados = [_success()] * 3 + [
        {"success": False, "error_type": "unexpected_error"}
    ] * 21
    with patch(LOOKUP, side_effect=resultados) as consultar:
        with pytest.raises(CommandError, match="20 errores"):
            call_command(COMMAND, batch_size=2, stdout=output)
    assert consultar.call_count == 23
    assert "errores=20" in output.getvalue()
    assert "escritos=3" in output.getvalue()
    assert "omitidos=20" in output.getvalue()
    assert (
        Ciudadano.objects.filter(
            estado_validacion_renaper=Ciudadano.RENAPER_NO_CONSULTADO
        ).count()
        == 21
    )
    assert _snapshot(ciudadanos[-1])["fecha_validacion_renaper"] is None


def test_resultado_concluyente_reinicia_contador_consecutivo(crear_ficha):
    for i in range(39):
        crear_ficha(55123456 + i)
    fallo = {"success": False, "error_type": "unexpected_error"}
    with patch(LOOKUP, side_effect=[fallo] * 19 + [_success()] + [fallo] * 19):
        call_command(COMMAND, batch_size=2)
    assert (
        Ciudadano.objects.filter(
            estado_validacion_renaper=Ciudadano.RENAPER_VALIDADO
        ).count()
        == 1
    )


@pytest.mark.parametrize(
    "apellido,nombre",
    [("P\u00c3\u00a9rez", "Ana Mar\u00c3\u00ada"), ("Perez", "Ana Maria")],
)
def test_revalida_mojibake_y_acentos_sin_pisar_identidad(crear_ficha, apellido, nombre):
    ciudadano = crear_ficha()
    Ciudadano.objects.filter(pk=ciudadano.pk).update(apellido=apellido, nombre=nombre)
    with patch(LOOKUP, return_value=_success()):
        call_command(COMMAND)
    ciudadano.refresh_from_db()
    assert ciudadano.estado_validacion_renaper == Ciudadano.RENAPER_VALIDADO
    assert ciudadano.apellido == apellido
    assert ciudadano.nombre == nombre
