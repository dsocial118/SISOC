"""Comentarios técnicos estructurados y su publicación a Provincia (issue #2318).

Cubre las reglas de `ComentariosTecnicosService`: validación de la combinación
de opciones, multi-alta sin sobrescritura, concatenación cronológica sin
duplicados y publicación selectiva (sólo las observaciones con ``Sí``).
"""

from datetime import date

import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from ciudadanos.models import Ciudadano
from celiaquia.comentarios_tecnicos import (
    CODIGO_OTROS,
    TipoDocumentoComentario,
    catalogo_serializable,
    es_codigo_valido,
    observaciones_de,
    texto_observacion,
)
from celiaquia.models import (
    EstadoExpediente,
    EstadoLegajo,
    Expediente,
    ExpedienteCiudadano,
    HistorialComentarios,
    RevisionTecnico,
)
from celiaquia.services.comentarios_tecnicos_service import (
    ComentariosTecnicosService,
    normalizar_si_no,
)

pytestmark = pytest.mark.django_db

CODIGO_RENAPER = "RENAPER_FECHA_NACIMIENTO"
CODIGO_ANSES = "ANSES_REGISTRA_OBRA_SOCIAL"


@pytest.fixture(name="tecnico")
def fixture_tecnico():
    return User.objects.create_user(username="tec_comentarios", password="pass")


@pytest.fixture(name="legajo")
def fixture_legajo(tecnico):
    estado_exp = EstadoExpediente.objects.create(nombre="EST_EXP_CT")
    estado_legajo = EstadoLegajo.objects.create(nombre="EST_LEG_CT")
    expediente = Expediente.objects.create(usuario_provincia=tecnico, estado=estado_exp)
    ciudadano = Ciudadano.objects.create(
        apellido="Tecnico",
        nombre="Comentario",
        documento="40100200",
        fecha_nacimiento=date(1990, 1, 1),
    )
    return ExpedienteCiudadano.objects.create(
        expediente=expediente, ciudadano=ciudadano, estado=estado_legajo
    )


def _registrar(legajo, usuario, **kwargs):
    datos = {
        "tipo_documento": TipoDocumentoComentario.RENAPER,
        "tiene_observaciones": True,
        "observacion_codigo": CODIGO_RENAPER,
    }
    datos.update(kwargs)
    return ComentariosTecnicosService.registrar(legajo=legajo, usuario=usuario, **datos)


# --- Catálogo -------------------------------------------------------------


def test_catalogo_tiene_otros_en_los_tres_tipos():
    for tipo in TipoDocumentoComentario.values:
        codigos = [codigo for codigo, _ in observaciones_de(tipo)]
        assert codigos[-1] == CODIGO_OTROS
        assert len(codigos) == len(set(codigos))


def test_codigo_no_es_valido_para_otro_tipo_de_documento():
    assert es_codigo_valido(TipoDocumentoComentario.RENAPER, CODIGO_RENAPER)
    assert not es_codigo_valido(TipoDocumentoComentario.ANSES, CODIGO_RENAPER)


def test_catalogo_serializable_marca_la_opcion_libre():
    catalogo = catalogo_serializable()
    assert set(catalogo) == set(TipoDocumentoComentario.values)
    libres = [o for o in catalogo[TipoDocumentoComentario.ANSES.value] if o["libre"]]
    assert [o["codigo"] for o in libres] == [CODIGO_OTROS]


@pytest.mark.parametrize(
    "valor,esperado",
    [
        ("SI", True),
        ("sí", True),
        ("1", True),
        (True, True),
        ("No", False),
        ("0", False),
        (False, False),
        ("", None),
        ("cualquiera", None),
        (None, None),
    ],
)
def test_normalizar_si_no(valor, esperado):
    assert normalizar_si_no(valor) is esperado


# --- Alta -----------------------------------------------------------------


def test_registrar_guarda_texto_de_catalogo_como_interno(legajo, tecnico):
    comentario = _registrar(legajo, tecnico)

    assert comentario.tipo_comentario == HistorialComentarios.TIPO_COMENTARIO_TECNICO
    assert comentario.es_interno is True
    assert comentario.publicado_en is None
    assert comentario.tiene_observaciones is True
    assert comentario.observacion_codigo == CODIGO_RENAPER
    assert comentario.comentario == texto_observacion(
        TipoDocumentoComentario.RENAPER, CODIGO_RENAPER
    )
    assert comentario.usuario == tecnico
    # Estado del legajo al momento de la creación (requerimiento §4).
    assert comentario.estado_relacionado == RevisionTecnico.PENDIENTE


def test_registrar_sin_observaciones_deja_la_observacion_vacia(legajo, tecnico):
    comentario = _registrar(
        legajo,
        tecnico,
        tiene_observaciones=False,
        observacion_codigo=CODIGO_RENAPER,
        observacion_libre="se ignora",
    )

    assert comentario.tiene_observaciones is False
    assert comentario.observacion_codigo is None
    assert comentario.comentario == "Sin observaciones."


def test_registrar_otros_usa_el_texto_libre(legajo, tecnico):
    comentario = _registrar(
        legajo,
        tecnico,
        observacion_codigo=CODIGO_OTROS,
        observacion_libre="  Falta la firma del profesional.  ",
    )

    assert comentario.observacion_codigo == CODIGO_OTROS
    assert comentario.comentario == "Falta la firma del profesional."


@pytest.mark.parametrize(
    "kwargs",
    [
        {"tipo_documento": ""},
        {"tipo_documento": "INEXISTENTE"},
        {"tiene_observaciones": ""},
        {"observacion_codigo": ""},
        {"observacion_codigo": "INEXISTENTE"},
        {"tipo_documento": TipoDocumentoComentario.ANSES},  # código de otro tipo
        {"observacion_codigo": CODIGO_OTROS, "observacion_libre": "   "},
    ],
)
def test_registrar_rechaza_combinaciones_invalidas(legajo, tecnico, kwargs):
    with pytest.raises(ValidationError):
        _registrar(legajo, tecnico, **kwargs)
    assert not ComentariosTecnicosService.historial(legajo).exists()


def test_altas_sucesivas_no_se_sobrescriben(legajo, tecnico):
    _registrar(legajo, tecnico)
    _registrar(legajo, tecnico, tiene_observaciones=False)
    _registrar(
        legajo,
        tecnico,
        tipo_documento=TipoDocumentoComentario.ANSES,
        observacion_codigo=CODIGO_ANSES,
    )

    assert ComentariosTecnicosService.historial(legajo).count() == 3


# --- Concatenación --------------------------------------------------------


def test_concatenado_es_cronologico_e_ignora_los_no(legajo, tecnico):
    _registrar(legajo, tecnico)
    _registrar(legajo, tecnico, tiene_observaciones=False)
    _registrar(
        legajo,
        tecnico,
        tipo_documento=TipoDocumentoComentario.ANSES,
        observacion_codigo=CODIGO_ANSES,
    )

    lineas = ComentariosTecnicosService.lineas_concatenadas(legajo)

    assert len(lineas) == 2
    assert lineas[0].startswith("RENAPER: ")
    assert lineas[1].startswith("ANSES: ")
    assert "Sin observaciones." not in ComentariosTecnicosService.texto_concatenado(
        legajo
    )


def test_concatenado_deduplica_el_mismo_codigo(legajo, tecnico):
    _registrar(legajo, tecnico)
    _registrar(legajo, tecnico)

    assert len(ComentariosTecnicosService.lineas_concatenadas(legajo)) == 1


def test_concatenado_deduplica_otros_con_el_mismo_texto(legajo, tecnico):
    _registrar(
        legajo, tecnico, observacion_codigo=CODIGO_OTROS, observacion_libre="Falta DNI"
    )
    _registrar(
        legajo,
        tecnico,
        observacion_codigo=CODIGO_OTROS,
        observacion_libre="  falta   dni ",
    )
    _registrar(
        legajo,
        tecnico,
        observacion_codigo=CODIGO_OTROS,
        observacion_libre="Falta la partida",
    )

    lineas = ComentariosTecnicosService.lineas_concatenadas(legajo)
    assert len(lineas) == 2


def test_componer_motivo_agrega_el_texto_libre(legajo, tecnico):
    _registrar(legajo, tecnico)

    motivo = ComentariosTecnicosService.componer_motivo(legajo, "  Urgente.  ")

    assert motivo.startswith("RENAPER: ")
    assert motivo.endswith("Urgente.")


def test_componer_motivo_sin_observaciones_acepta_solo_texto_libre(legajo, tecnico):
    _registrar(legajo, tecnico, tiene_observaciones=False)

    assert ComentariosTecnicosService.componer_motivo(legajo, "Motivo puntual.") == (
        "Motivo puntual."
    )


def test_componer_motivo_sin_observaciones_ni_texto_libre_falla(legajo, tecnico):
    _registrar(legajo, tecnico, tiene_observaciones=False)

    with pytest.raises(ValidationError):
        ComentariosTecnicosService.componer_motivo(legajo, "   ")


# --- Publicación ----------------------------------------------------------


def test_publicar_solo_alcanza_a_las_observaciones_con_si(legajo, tecnico):
    con_obs = _registrar(legajo, tecnico)
    sin_obs = _registrar(legajo, tecnico, tiene_observaciones=False)

    assert ComentariosTecnicosService.publicar(legajo, usuario=tecnico) == 1

    con_obs.refresh_from_db()
    sin_obs.refresh_from_db()
    assert con_obs.es_interno is False
    assert con_obs.publicado_en is not None
    assert con_obs.publicado_por == tecnico
    assert sin_obs.es_interno is True
    assert sin_obs.publicado_en is None


def test_publicar_no_repisa_la_auditoria_de_los_ya_publicados(legajo, tecnico):
    primero = _registrar(legajo, tecnico)
    ComentariosTecnicosService.publicar(legajo, usuario=tecnico)
    primero.refresh_from_db()
    publicado_en_original = primero.publicado_en

    otro_tecnico = User.objects.create_user(username="tec_2", password="pass")
    _registrar(
        legajo,
        tecnico,
        tipo_documento=TipoDocumentoComentario.ANSES,
        observacion_codigo=CODIGO_ANSES,
    )
    assert ComentariosTecnicosService.publicar(legajo, usuario=otro_tecnico) == 1

    primero.refresh_from_db()
    assert primero.publicado_en == publicado_en_original
    assert primero.publicado_por == tecnico
