from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from encuestas.models import (
    Encuesta,
    EstadoRonda,
    OpcionPregunta,
    OperadorCondicion,
    Pregunta,
    RecordatorioUsuario,
    RespuestaPregunta,
    RespuestaRonda,
    RondaEncuesta,
    SegmentacionDestinatario,
    SegmentacionEncuesta,
    TipoDocumento,
    TipoPregunta,
    TipoSegmentacion,
)


@pytest.fixture
def usuario_creador(django_user_model):
    return django_user_model.objects.create_user(username="creador", password="x")


@pytest.fixture
def encuesta_obligatoria(usuario_creador):
    return Encuesta.objects.create(
        titulo="Satisfacción",
        es_obligatoria=True,
        duracion_ronda_dias=7,
        usuario_creador=usuario_creador,
    )


@pytest.mark.django_db
def test_encuesta_obligatoria_no_requiere_intervalo_recordatorio(encuesta_obligatoria):
    encuesta_obligatoria.full_clean()


@pytest.mark.django_db
def test_encuesta_no_obligatoria_requiere_intervalo_recordatorio(usuario_creador):
    encuesta = Encuesta(
        titulo="Clima laboral",
        es_obligatoria=False,
        duracion_ronda_dias=7,
        usuario_creador=usuario_creador,
    )
    with pytest.raises(ValidationError):
        encuesta.full_clean()


@pytest.mark.django_db
def test_encuesta_recurrente_requiere_intervalo_recurrencia(usuario_creador):
    encuesta = Encuesta(
        titulo="Clima laboral",
        es_obligatoria=True,
        es_recurrente=True,
        duracion_ronda_dias=7,
        usuario_creador=usuario_creador,
    )
    with pytest.raises(ValidationError):
        encuesta.full_clean()


@pytest.mark.django_db
def test_no_puede_haber_dos_versiones_iguales_del_mismo_padre(
    usuario_creador, encuesta_obligatoria
):
    Encuesta.objects.create(
        titulo=encuesta_obligatoria.titulo,
        es_obligatoria=True,
        duracion_ronda_dias=7,
        usuario_creador=usuario_creador,
        version_de=encuesta_obligatoria,
        version=2,
    )
    version_duplicada = Encuesta(
        titulo=encuesta_obligatoria.titulo,
        es_obligatoria=True,
        duracion_ronda_dias=7,
        usuario_creador=usuario_creador,
        version_de=encuesta_obligatoria,
        version=2,
    )
    with pytest.raises(IntegrityError):
        version_duplicada.save()


@pytest.mark.django_db
def test_pregunta_condicion_debe_ser_de_la_misma_encuesta(usuario_creador):
    encuesta_a = Encuesta.objects.create(
        titulo="A",
        es_obligatoria=True,
        duracion_ronda_dias=7,
        usuario_creador=usuario_creador,
    )
    encuesta_b = Encuesta.objects.create(
        titulo="B",
        es_obligatoria=True,
        duracion_ronda_dias=7,
        usuario_creador=usuario_creador,
    )
    pregunta_ajena = Pregunta.objects.create(
        encuesta=encuesta_b, texto="¿Usás el módulo X?", tipo=TipoPregunta.SI_NO
    )
    pregunta = Pregunta(
        encuesta=encuesta_a,
        texto="¿Qué mejorarías?",
        tipo=TipoPregunta.TEXTO_LARGO,
        pregunta_condicion=pregunta_ajena,
        operador_condicion=OperadorCondicion.IGUAL,
        valor_condicion="si",
    )
    with pytest.raises(ValidationError):
        pregunta.full_clean()


@pytest.mark.django_db
def test_condicion_requiere_pregunta_operador_y_valor_en_conjunto(encuesta_obligatoria):
    pregunta_base = Pregunta.objects.create(
        encuesta=encuesta_obligatoria,
        texto="¿Usás el módulo X?",
        tipo=TipoPregunta.SI_NO,
    )
    pregunta_incompleta = Pregunta(
        encuesta=encuesta_obligatoria,
        texto="¿Qué mejorarías?",
        tipo=TipoPregunta.TEXTO_LARGO,
        pregunta_condicion=pregunta_base,
        operador_condicion="",
    )
    with pytest.raises(ValidationError):
        pregunta_incompleta.full_clean()


@pytest.mark.django_db
def test_flujo_completo_pregunta_opciones_ronda_y_respuesta(
    encuesta_obligatoria, usuario_creador
):
    pregunta = Pregunta.objects.create(
        encuesta=encuesta_obligatoria,
        texto="¿Cómo calificás el servicio?",
        tipo=TipoPregunta.OPCION_UNICA,
    )
    opcion = OpcionPregunta.objects.create(
        pregunta=pregunta, texto="Muy bueno", valor="5"
    )

    segmentacion = SegmentacionEncuesta.objects.create(
        encuesta=encuesta_obligatoria, tipo=TipoSegmentacion.TODOS_LOS_USUARIOS
    )
    SegmentacionDestinatario.objects.create(
        segmentacion=segmentacion,
        tipo_documento=TipoDocumento.DNI,
        numero_documento="30111222",
    )

    ahora = timezone.now()
    ronda = RondaEncuesta.objects.create(
        encuesta=encuesta_obligatoria,
        numero_ronda=1,
        fecha_apertura=ahora,
        fecha_cierre_programada=ahora
        + timedelta(days=encuesta_obligatoria.duracion_ronda_dias),
        estado=EstadoRonda.ABIERTA,
    )

    respuesta_ronda = RespuestaRonda.objects.create(
        ronda=ronda, usuario=usuario_creador, completa=True
    )
    respuesta_pregunta = RespuestaPregunta.objects.create(
        respuesta_ronda=respuesta_ronda, pregunta=pregunta
    )
    respuesta_pregunta.opciones_seleccionadas.add(opcion)

    assert ronda.respuestas.count() == 1
    assert respuesta_pregunta.opciones_seleccionadas.get() == opcion


@pytest.mark.django_db
def test_un_usuario_no_puede_responder_dos_veces_la_misma_ronda(
    usuario_creador, encuesta_obligatoria
):
    ahora = timezone.now()
    ronda = RondaEncuesta.objects.create(
        encuesta=encuesta_obligatoria,
        numero_ronda=1,
        fecha_apertura=ahora,
        fecha_cierre_programada=ahora + timedelta(days=7),
    )
    RespuestaRonda.objects.create(ronda=ronda, usuario=usuario_creador)
    with pytest.raises(IntegrityError):
        RespuestaRonda.objects.create(ronda=ronda, usuario=usuario_creador)


@pytest.mark.django_db
def test_no_se_puede_borrar_ronda_con_respuestas(usuario_creador, encuesta_obligatoria):
    ahora = timezone.now()
    ronda = RondaEncuesta.objects.create(
        encuesta=encuesta_obligatoria,
        numero_ronda=1,
        fecha_apertura=ahora,
        fecha_cierre_programada=ahora + timedelta(days=7),
    )
    RespuestaRonda.objects.create(ronda=ronda, usuario=usuario_creador)
    with pytest.raises(Exception):
        ronda.delete()


@pytest.mark.django_db
def test_recordatorio_usuario_es_unico_por_ronda(usuario_creador, encuesta_obligatoria):
    ahora = timezone.now()
    ronda = RondaEncuesta.objects.create(
        encuesta=encuesta_obligatoria,
        numero_ronda=1,
        fecha_apertura=ahora,
        fecha_cierre_programada=ahora + timedelta(days=7),
    )
    RecordatorioUsuario.objects.create(
        ronda=ronda,
        usuario=usuario_creador,
        fecha_proximo_aviso=ahora + timedelta(days=3),
    )
    with pytest.raises(IntegrityError):
        RecordatorioUsuario.objects.create(
            ronda=ronda,
            usuario=usuario_creador,
            fecha_proximo_aviso=ahora + timedelta(days=5),
        )
